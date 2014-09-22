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
from mlp.groups.models import Roster, GroupFile, Group
from mlp.groups.enums import UserRole
from mlp.groups.views import file_add
from .perms import decorators, can_list_all_files
from .models import File, FileTag, AssociatedFile
from .enums import FileType, FileStatus
from .forms import FileForm, FileSearchForm
from .tasks import process_uploaded_file

@login_required
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
    ).exclude(type=FileType.TEXT)

    failed = File.objects.filter(
        status=FileStatus.FAILED,
        uploaded_by=request.user,
    ).exclude(type=FileType.TEXT)

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
    related_objects = []
    file_tags = FileTag.objects.filter(file=file)
    group_files = GroupFile.objects.filter(file=file)
    associated_files = AssociatedFile.objects.filter(main_file=file)
    files = File.objects.filter(file_id__in=associated_files.values('associated_file'))

    # add related objects to list
    for f in file_tags:
        related_objects.append(f)
    for a in associated_files:
        related_objects.append(a)
    for c in group_files:
        related_objects.append(c)

    if request.method == "POST" or file.status == FileStatus.FAILED:
        for f in files:
            related_objects.append(f)
        for item in related_objects:
            # delete related objects
            item.delete()
        file.delete()
        admin = Roster.objects.filter(user=request.user, role=UserRole.ADMIN)
        if request.user.is_staff or admin.exists():
            return HttpResponseRedirect(reverse('files-list'))
        else:
            return HttpResponseRedirect(reverse('users-home'))

    return render(request, 'files/delete.html', {
        "related_objects": related_objects,
        "file": file,        
    })

@decorators.can_edit_file
def edit(request, file_id):
    """
    Edit a file
    """
    file = get_object_or_404(File, pk=file_id)
    associated_files = AssociatedFile.objects.filter(main_file=file).values('associated_file')
    associated_files = File.objects.filter(file_id__in=associated_files, status=FileStatus.READY)
    if request.POST:
        form = FileForm(request.POST, instance=file)
        if form.is_valid():
            form.save(user=request.user)
            messages.success(request, "File edited!")
            return HttpResponseRedirect(reverse("files-detail", args=(file.pk,)))
    else:
        form = FileForm(instance=file)

    return render(request, 'files/edit.html', {
        'associated_files': associated_files,
        'form': form,
        'file': file,
        'FileType': FileType,
        'FileStatus': FileStatus,
    })

def detail(request, file_id):
    """
    Detail view
    """
    file = get_object_or_404(File, pk=file_id)
    file_tags = file.filetag_set.all().select_related("tag")
    duration = str(datetime.timedelta(seconds=math.floor(file.duration)))
    associated_files = AssociatedFile.objects.filter(main_file=file).values('associated_file')
    associated_files = File.objects.filter(file_id__in=associated_files, status=FileStatus.READY)
    if not associated_files:
        associated_files = AssociatedFile.objects.all().values('associated_file')
        associated_files = File.objects.filter(uploaded_by=request.user, status=FileStatus.READY, type=FileType.TEXT).exclude(file_id__in=associated_files)
        for _file in associated_files:
            AssociatedFile.objects.create(main_file=file, associated_file=_file)

    return render(request, 'files/detail.html', {
        'duration': duration,
        'file': file,
        'file_tags': file_tags,
        'associated_files': associated_files,
        'FileType': FileType,
        'FileStatus': FileStatus,
    })

@decorators.can_upload_file
def upload(request):
    """
    Uploads a file to the server
    """
    return _upload(request, group_id=None)

@decorators.can_upload_to_group
def upload_to_group(request, group_id):
    """
    Uploads a file directly to a class
    """
    return _upload(request, group_id)

def _upload(request, group_id):
    """
    Basic upload view
    """
    if group_id is None:
        group = None
    else:
        group = get_object_or_404(Group, pk=group_id)
        group = Roster.objects.filter(group=group, user=request.user)

    my_files = File.objects.filter(uploaded_by=request.user, status=FileStatus.READY)
    if request.method == "POST":
        if request.POST.get("error_message"):
            messages.error(request, request.POST["error_message"])
        else:
            messages.success(request, "Files Uploaded! Processing...")

        admin = Roster.objects.filter(user=request.user, role=UserRole.ADMIN)
        if group:
            # add files to a class if one was specified
            for file in File.objects.filter(status=FileStatus.UPLOADED, uploaded_by=request.user):
                file_add(request, group_id, file.pk) 
            
        if request.user.is_staff or admin.exists():
            return HttpResponseRedirect(reverse('files-list'))
        elif group_id:
            return HttpResponseRedirect(reverse('groups-file_list', args=(group_id,)))
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
        'chunk_size': settings.CHUNK_SIZE,    
        'group': group,
    })

def upload_associated_file(request, file_id):
    """
    Takes a file id and uploads text files, then links them to that file.
    """
    main_file = get_object_or_404(File, pk=file_id)
    associated_files = AssociatedFile.objects.filter(main_file=main_file).values('associated_file')
    associated_files = File.objects.filter(file_id__in=associated_files, status=FileStatus.READY)
    if request.method == "POST":
        if request.POST.get("error_message"):
            messages.error(request, request.POST["error_message"])
        else:
            messages.success(request, "Associated Files Uploaded! Processing...")
    
        for associated_file in File.objects.filter(uploaded_by=request.user, type=FileType.TEXT):
            if AssociatedFile.objects.filter(associated_file=associated_file).exists():
                pass
            else:
                AssociatedFile.objects.create(main_file=main_file, associated_file=associated_file)            

        return HttpResponseRedirect(reverse('files-edit', args=(file_id,)))

    uploaded = File.objects.filter(
        status=FileStatus.UPLOADED,
        uploaded_by=request.user,
    )

    failed = File.objects.filter(
        status=FileStatus.FAILED,
        uploaded_by=request.user,
    )

    return render(request, 'files/upload_associated.html', {
        "file": main_file,
        "uploaded": uploaded,
        "failed": failed,
        "chunk_size": settings.CHUNK_SIZE,
        "associated_files": associated_files,
        "FileType": FileType,
        "FileStatus": FileStatus,
    })

def delete_associated_file(request, file_id):
    """
    Deletes an associated file.
    """
    file = get_object_or_404(File, pk=file_id)
    associated_file = AssociatedFile.objects.get(associated_file=file)
    main_file = associated_file.main_file
    associated_file.delete()
    file.delete()
    messages.success(request, 'File deleted!')
    return HttpResponseRedirect(reverse('files-edit', args=(main_file.pk,)))

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
    response['Content-Disposition'] = 'attachment; filename=%s' % (file.name)
    # Django doesn't support x-sendfile, so write the file in debug mode
    if settings.DEBUG:
        shutil.copyfileobj(open(file.file.path), response)
    return response

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



