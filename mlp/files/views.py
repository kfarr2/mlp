from wsgiref.util import FileWrapper
import arcutils
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
from mlp.utils import RangedFileReader, parse_range_header
from mlp.groups.models import Roster, GroupFile, Group
from mlp.groups.enums import UserRole
from mlp.groups.views import file_add
from .perms import decorators, can_list_all_files
from .models import File, FileTag, AssociatedFile
from .enums import FileType, FileStatus
from .forms import FileForm, FileSearchForm
from .tasks import process_uploaded_file, get_duration

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
        'FileType': FileType,
        'FileStatus': FileStatus,
    })

@decorators.can_edit_file(field='slug')
def delete(request, slug):
    """
    Delete a file
    """
    file = get_object_or_404(File, slug=slug)
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

@decorators.can_edit_file(field='slug')
def edit(request, slug):
    """
    Edit a file
    """
    file = get_object_or_404(File, slug=slug)
    if request.FILES:
        for a_file in request.FILES['file']:
            AssociatedFile.objects.get_or_create(associated_file=a_file, main_file=main_file)
    associated_files = AssociatedFile.objects.filter(main_file=file).values('associated_file')
    associated_files = File.objects.filter(file_id__in=associated_files, status=FileStatus.READY)
    if request.POST:
        form = FileForm(request.POST, instance=file)
        if form.is_valid():
            form.save(user=request.user)
            messages.success(request, "File edited!")
            return HttpResponseRedirect(reverse("files-detail", args=(file.slug,)))
    else:
        form = FileForm(instance=file)

    return render(request, 'files/edit.html', {
        'associated_files': associated_files,
        'form': form,
        'file': file,
        'FileType': FileType,
        'FileStatus': FileStatus,
    })

def detail(request, slug):
    """
    Detail view
    """
    file = get_object_or_404(File, slug=slug)
    file_tags = file.filetag_set.all().select_related("tag")
    duration = str(datetime.timedelta(seconds=math.floor(file.duration)))
    associated_files = AssociatedFile.objects.filter(main_file=file).values('associated_file')
    associated_files = File.objects.filter(file_id__in=associated_files, status=FileStatus.READY)
    if not associated_files:
        if request.user.is_authenticated():
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
    return _upload(request, slug=None)

@decorators.can_upload_to_group(field='slug')
def upload_to_group(request, slug):
    """
    Uploads a file directly to a class
    """
    return _upload(request, slug)

def _upload(request, slug):
    """
    Basic upload view
    """
    if slug is None:
        group = None
    else:
        group = get_object_or_404(Group, slug=slug)
        group = Roster.objects.filter(group=group, user=request.user)

    associated_files = AssociatedFile.objects.values('associated_file')
    associated_files = File.objects.filter(file_id__in=associated_files)
    my_files = File.objects.filter(uploaded_by=request.user, status=FileStatus.READY).exclude(file_id__in=associated_files)
    to_delete = File.objects.filter(uploaded_by=request.user, status=FileStatus.READY, type=FileType.TEXT).exclude(file_id__in=associated_files)
    if to_delete.exists():
        for file in to_delete:
            file.delete()
    if request.method == "POST":
        if request.POST.get("error_message"):
            messages.error(request, request.POST["error_message"])
        else:
            messages.success(request, "Files Uploaded! Processing...")

        admin = Roster.objects.filter(user=request.user, role=UserRole.ADMIN)
        if group:
            # add files to a class if one was specified
            for file in File.objects.filter(status=FileStatus.UPLOADED, uploaded_by=request.user):
                file_add(request, slug, file.pk) 
            
        if slug:
            return HttpResponseRedirect(reverse('groups-file_list', args=(slug,)))
        elif request.user.is_staff or admin.exists():
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
        'chunk_size': settings.CHUNK_SIZE,    
        'group': group,
        'FileType': FileType,
        'FileStatus': FileStatus,
    })

@decorators.can_edit_file(field='slug')
def upload_associated_file(request, slug):
    """
    Takes a file id and uploads text files, then links them to that file.
    """
    main_file = get_object_or_404(File, slug=slug)
    associated_files = AssociatedFile.objects.filter(main_file=main_file).values('associated_file')
    associated_files = File.objects.filter(file_id__in=associated_files, status=FileStatus.READY)
    if request.method == "POST":
        if request.POST.get("error_message"):
            messages.error(request, request.POST["error_message"])
        else:
            messages.success(request, "Associated Files Uploaded! Processing...")
            # we'll update the database on the redirect
            a_file=File.objects.last()
            AssociatedFile.objects.create(main_file=main_file, associated_file=a_file)
        
        return HttpResponseRedirect(reverse('files-edit', args=(slug,)))

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

@decorators.can_edit_file(field='slug')
def delete_associated_file(request, slug):
    """
    Deletes an associated file.
    """
    file = get_object_or_404(File, slug=slug)
    associated_file = AssociatedFile.objects.get(associated_file=file)
    main_file = associated_file.main_file
    associated_file.delete()
    file.delete()
    messages.success(request, 'File deleted!')
    return HttpResponseRedirect(reverse('files-edit', args=(main_file.slug,)))

@decorators.can_download_file(field='slug')
def download(request, slug):
    """
    Basic download view
    
    TODO: this will actually need to be fixed to stop XSS injections in files.
    Files should be downloaded over a completely different domain.
    """
    file = get_object_or_404(File, slug=slug)
    response = HttpResponse()
    response['Content-Type'] = mimetypes.guess_type(file.file.path)[0]
    response['X-Sendfile'] = file.file.path
    response['Content-Disposition'] = 'attachment; filename=%s' % (file.name)
    # Django doesn't support x-sendfile, so write the file in debug mode
    if settings.DEBUG:
        shutil.copyfileobj(open(file.file.path, 'rb'), response)
    return response

def media(request, slug):
    """
    Takes a request and a slug and passes back the file
    """
    slug, file_part = os.path.split(slug)
    file = File.objects.get(slug=slug)
    path = os.path.join(file.directory, file_part)
    size = os.stat(path).st_size
    file = RangedFileReader(open(path, 'rb'))
    content_type = mimetypes.guess_type(path)[0]
    if not settings.DEBUG:
        response = HttpResponse()
        response['X-Sendfile'] = path
        response['Content-Type'] = content_type
        return response

    response = StreamingHttpResponse(file, content_type)
    response['Content-Length'] = size
    response['Accept-Ranges'] = "bytes"

    if "HTTP_RANGE" in request.META:
        try:
            ranges = parse_range_header(request.META['HTTP_RANGE'], size)
        except ValueError:
            ranges = None

        if ranges is not None and len(ranges) == 1:
            start, stop = ranges[0]
            if stop > size:
                return HttpResponse(status=416)
            file.start = start
            file.stop = stop
            response['Content-Range'] = "bytes %d-%d/%d" % (start, stop-1, size)
            response['Content-Length'] = stop - start
            response.status_code = 206

    response['X-Sendfile'] = path
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



