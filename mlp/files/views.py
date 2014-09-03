from wsgiref.util import FileWrapper
import mimetypes
import shutil
import os
import math
import datetime
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
from mlp.classes.models import Roster
from mlp.classes.enums import UserRole
from .perms import decorators, can_list_all_files
from .models import File
from .enums import FileType, FileStatus
from .forms import FileForm, FileSearchForm
from .tasks import process_uploaded_file

@decorators.can_list_all_files
def list_(request):
    """
    List all the files
    """
    form = FileSearchForm(request.GET, user=request.user)
    form.is_valid()
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

@decorators.can_edit_file
def delete(request, file_id):
    """
    Delete a file
    """
    file = get_object_or_404(File, pk=file_id)
    if request.method == "POST" or file.status == FileStatus.FAILED:
        file.delete()
        admin = Roster.objects.filter(user=request.user, role=UserRole.ADMIN)
        if request.user.is_staff or admin.exists():
            return HttpResponseRedirect(reverse('files-list'))
        else:
            return HttpResponseRedirect(reverse('users-home'))

    return render(request, 'files/delete.html', {
        "file": file,        
    })

@decorators.can_edit_file
def edit(request, file_id):
    """
    Edit a file
    """
    file = get_object_or_404(File, pk=file_id)
    if request.POST:
        form = FileForm(request.POST, instance=file)
        if form.is_valid():
            form.save(user=request.user)
            messages.success(request, "File edited!")
            return HttpResponseRedirect(reverse("files-detail", args=(file.pk,)))
    else:
        form = FileForm(instance=file)

    return render(request, 'files/edit.html', {
        'form': form,
        'file': file,
    })

def detail(request, file_id):
    """
    Detail views
    """
    file = get_object_or_404(File, pk=file_id)
    file_tags = file.filetag_set.all().select_related("tag")
    duration = str(datetime.timedelta(seconds=math.floor(file.duration)))
    
    return render(request, 'files/detail.html', {
        'duration': duration,
        'file': file,
        'file_tags': file_tags,
        'FileType': FileType,
        'FileStatus': FileStatus,
    })

@decorators.can_upload_file
def upload(request):
    """
    Basic upload view
    """
    my_files = File.objects.filter(uploaded_by=request.user)
    if request.method == "POST":
        if request.POST.get("error_message"):
            messages.error(request, request.POST["error_message"])
            return HttpResponse(request.POST["error_message"])
        else:
            messages.success(request, "Files Uploaded! Processing...")

        admin = Roster.objects.filter(user=request.user, role=UserRole.ADMIN)
        if request.user.is_staff or admin.exists():
            return HttpResponseRedirect(reverse('files-list'))
        else:
            return HttpResponseRedirect(reverse('files-upload'))
    
    uploaded = File.objects.filter(
        status=FileStatus.UPLOADED,
        uploaded_by=request.user,
    )

    failed = File.objects.filter(
        status=FileStatus.FAILED,
        uploaded_by=request.user,
    )

    return render(request, 'files/upload.html', {
        'failed': failed,
        'uploaded': uploaded,
        'my_files': my_files,
        'chunk_size': settings.CHUNK_SIZE    
    })

@decorators.can_download_file
def download(request, file_id):
    """
    Basic download view
    
    TODO: this will actually need to be fixed to stop XSS injections in files.
    Files should be downloaded over a completely different domain.
    """
    file = get_object_or_404(File, pk=file_id)
    response = HttpResponse()
    response['Content-Type'] = mimetypes.guess_type(file.file.path)[0]
    response['X-Sendfile'] = file.file.path
    # Django doesn't support x-sendfile, so write the file in debug mode
    if settings.DEBUG:
        shutil.copyfileobj(open(file.file.path), response)
    return response

@csrf_exempt
@decorators.can_upload_file
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

    max_number_of_chunks = math.ceil(float(settings.MAX_UPLOAD_SIZE) / settings.CHUNK_SIZE)
    if int(request.POST['resumableChunkNumber']) > max_number_of_chunks:
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



