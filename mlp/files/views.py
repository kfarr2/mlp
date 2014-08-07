from wsgiref.util import FileWrapper
import mimetypes
import shutil
import os
import math
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseRedirect, StreamingHttpResponse
from django.db import transaction, DatabaseError
from django.db.models import F
from django.shortcuts import render, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.conf import settings
#from .perms import decorators, can_list_all_files
from .models import File
from .enums import FileType, FileStatus
from .forms import FileForm, FileSearchForm
from .tasks import process_uploaded_file

def list(request):
    """
    List all the files
    """
    form = FileSearchForm(request.GET, user=request.user)
    form.is_valid
    files = form.results(page=request.GET.get("page"))

    uploaded = File.objects.filter(
        status=FileStatus.UPLOADED,
        uploaded_by=request.user,
    )

    failed = File.objects.filter(
        status=FileStatus.FAILED,
        uploaded_by=request.user,
    )

    return render(request, 'files/list.html', {
        'files': files,
        'uploaded': uploaded,
        'failed': failed,
        'form': form,
    })
   
def detail(request, file_id):
    """
    Detail views
    """
    return render(request, 'files/detail.html', {
        
    })

def upload(request):
    """
    Basic upload view
    """
    if request.method == "POST":
        if request.POST.get("error_message"):
            return HttpResponse(request.POST["error_message"])
        else:
            messages.success(request, "Files Uploaded!")
        return HttpResponseRedirect(reverse('files-list'))

    return render(request, 'files/upload.html', {
        'chunk_size': settings.CHUNK_SIZE    
    })

def download(request, file_id):
    """
    Basic download view
    """
    return render(request, 'files/download.html', {
        
    })

@csrf_exempt
def store(request):
    """
    This view recieves a chunk of a file and saves it. When all
    the chunks are uploaded, they are joined together to make
    a complete file
    """
    guid = File.sanitize_filename(request.POST['resumableIdentifier'])
    if not guid:
        return HttpResponseNotFound("Invalid file identifier")

    dir_path = os.path.join(settings.TMP_ROOT, str(request.user.pk) + "-" + guid)
    try:
        os.makedirs(dir_path)
    except OSError as e:
        # directory exists, bro.
        pass

    # each file will be named 1.part, 2.part, etc. and stored inside the dir_path
    file_path = os.path.join(dir_path, str(int(request.POST['resumableChunkNumber'])) + '.part')
    file = request.FILES['file']

    # don't let that chunk be too big
    if file.size > (settings.CHUNK_SIZE*2):
        shutil.rmtree(dir_path)
        return HttpResponseNotFound("Too many chunks")

    with open(file_path, 'wb') as dest:
        for chunk in file.chunks():
            dest.write(chunk)

    total_number_of_chunks = int(request.POST['resumableTotalChunks'])
    total_number_of_uploaded_chunks = len(os.listdir(dir_path))
    if total_number_of_chunks != total_number_of_uploaded_chunks:
        return HttpResponse("OK")

    total_size = 0
    for i in range(1, total_number_of_chunks + 1):
        chunk_path = os.path.join(dir_path, str(i) + '.part')
        total_size += os.path.getsize(chunk_path)
        if total_size > settings.MAX_UPLOAD_SIZE:
            shutil.rmtree(dir_path)
            return HttpResponseNotFound("File too big")

    if total_size != int(request.POST['resumableTotalSize']):
        # All files present and accounted for. 
        # Slow when being written, however.
        return HttpResponse("OK")

    try:
        f = File(
            name=request.POST['resumableFilename'],
            type=FileType.UNKNOWN,
            status=FileStatus.UPLOADED,
            uploaded_by=request.user,
            tmp_path=dir_path,
        )
        f.save()
    except DatabaseError as e:
        # the file object was already created and handled
        return HttpResponse("OK")

    # only one thread per upload
    process_uploaded_file.delay(total_number_of_chunks, f)
    return HttpResponse("COMPLETE")



