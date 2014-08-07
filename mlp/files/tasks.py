from __future__ import absolute_import, print_function
import re
import collections
import tempfile
import sys
import os
import shutil
import subprocess
import datetime
import mimetypes
import hashlib
from functools import partial
from django.conf import settings
from django.db import IntegrityError, transaction, DatabaseError
from celery import shared_task
from .enums import FileStatus, VIDEO_FILE_MIME_TYPES, FileType, AUDIO_FILE_MIME_TYPES
from .models import File


@shared_task
def process_uploaded_file(total_number_of_chunks, file):
    """
    This handles a chunked uploaded by concatenating the chunks together to
    form a single file, converting the file to different file types if
    necessary, and then updating the File model instance with the path to the
    concatenated file
    """
    # since all the chunks are uploaded, we need to concatenate them
    # together to form the complete file
    try:
        os.makedirs(file.directory)
    except OSError as e: # pragma no cover
        pass
    ext = os.path.splitext(file.name)[1] or ".unknown"
    final_resting_file_path = os.path.join(file.directory, 'original' + ext)
    concat_file = open(final_resting_file_path, "wb")
    # combine all the chunks into a simple file (chunk numbers are 1 based,
    # not 0 based)
    for i in range(1, total_number_of_chunks + 1):
        chunk_path = os.path.join(file.tmp_path, str(i) + '.part')
        shutil.copyfileobj(open(chunk_path, 'rb'), concat_file)

    concat_file.close()
    file.file = os.path.relpath(final_resting_file_path, settings.MEDIA_ROOT)
    file.status = FileStatus.FAILED
    mime_type = mimetypes.guess_type(final_resting_file_path)[0]
    if mime_type in VIDEO_FILE_MIME_TYPES:
        file.type = FileType.VIDEO
        was_successful = convert_video(file)
        file.duration = get_duration(final_resting_file_path)

        if was_successful:
            file.status = FileStatus.READY
            generate_thumbnail(file, datetime.time(second=1))
    elif mime_type in AUDIO_FILE_MIME_TYPES:
        
        file.type = FileType.AUDIO
        was_successful = convert_audio(file)
        file.duration = get_duration(final_resting_file_path)
 
        if was_successful:
            file.status = FileStatus.READY

    # since we were passed in serialized File object, some of the fields (like the
    # name or description may have changed, so we only want to update the
    # relevant fields). And, the file object in the DB could have been deleted
    # by the time we get here, so we make sure it still exists.
    with transaction.atomic():
        try:
            # this query ensures we get a lock on the File object, and it (still) exists
            row = File.objects.select_for_update().get(pk=file.pk)
            file.save(update_fields=['status', 'file', 'type', 'duration'])
        except (IndexError, DatabaseError, File.DoesNotExist) as e:
            return -1
        finally:
            # clean up
            shutil.rmtree(file.tmp_path)

    return file.status


def get_matching_file(path):
    '''
    returns a File object with a md5_sum that matches that of path,
    IF it exists. Otherwise, returns None.
    
    There's some tricky stuff with permissions, so in its current state,
    this should only be used when importing orgs.
    '''
    md5_sum = get_md5_sum(path)
    
    files = File.objects.filter(md5_sum=md5_sum)
    
    if len(files) > 0:
        return files[0]
    else:
        return None
    

def conditional_copy(src_path, dest_path):
    '''
    only copies the file if the destination doesn't match the source,
    either because it doesn't exist or because the file sizes don't match.
    '''
    if are_duplicate_files(src_path, dest_path):
        return
    
    shutil.copyfile(src_path, dest_path)
        
def are_duplicate_files(src_path, dest_path):
    ''' assumes the 1st file exists. doesn't assume anything about the 2nd. '''    
    if os.path.isfile(dest_path):
        src_size = os.stat(src_path).st_size
        dst_size = os.stat(dest_path).st_size

        if src_size == dst_size:
            return True        
    return False


def get_media_file_duration(filepath):
    '''
    gets the duration of a media file, using ffmpeg.
    
    '''
    # we need to determine what to do with filepath, which MAY or MAY NOT contain a file extension
    # this code is almost identical to code in process_imported_video. might want to make a separate function.    
    ext = os.path.splitext(filepath)[1] or None
    
    if ext is None:
        if os.path.isfile(filepath + '.mp4'):
            filepath = filepath + '.mp4'
        elif os.path.isfile(filepath + '.ogv'):
            filepath = filepath + '.ogv'
        else:
            print("Couldn't find file %s" % filepath)
            return 0
    else:
        if not os.path.isfile(filepath):
            print("Couldn't find file %s" % filepath)
            return 0
    
    command = ['ffmpeg', '-i', filepath]

    output = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()[1]        # entire output comes through as an error, for some reason.
    
    try:    
        duration_string = re.search('(?<=Duration: )[\d:.]+', output).group(0)          # fixme: error-checking
    except AttributeError as e:
        print("Error getting media file duration!")
        return 0
    
    hours, minutes, seconds, subseconds = re.findall('\d+', duration_string)
    duration = int(hours) * 3600 + int(minutes) * 60 + int(seconds) + float(subseconds) / 100
    
    return duration                  


def get_md5_sum(filename):
    '''
    returns an md5_sum as a 32-character string
    '''
    with open(filename, mode='rb') as file:
        md5 = hashlib.md5()
        for buffer in iter(partial(file.read, 128), b''):
            md5.update(buffer)
    return md5.hexdigest()


def path_has_extension(path):
    return True if len(os.path.splitext(path)[1]) > 0 else False


def get_or_import_video(path, name, description, created_date, changed_date):
    '''
    Returns a File object (if possible)
    and starts importing it using Celery.
    
    Returns None on error.
    
    '''
    
    # check if our path has an extension. if it does, exit out.
    if path_has_extension(path):
        return None
    
    # see if there's an mp4 or ogv version
    if os.path.isfile(path + '.mp4'):
        path = path + '.mp4'
    elif os.path.isfile(path + '.ogv'):
        path = path + '.ogv'
    else:
        print("Couldn't find mp4 or ogv of %s" % path)
        # if neither, exit out
        return None

    md5_sum = get_md5_sum(path)     # do an md5_sum on the original.
    
    # check our db to see if another file has this md5_sum
    files = File.objects.filter(md5_sum=md5_sum)        
    if len(files) > 0:
        print("Found file with identical md5_sum for %s" % path)
        return files[0]    # if so, return that file
    
    # if not, we need to import this file
    # create the file model, and send the import task to Celery

    duration = get_media_file_duration(path)
    
    file = File(name=name,
                description=description or "",
                type=FileType.VIDEO,
                status=FileStatus.IMPORTED,
                tmp_path=path,
                duration=duration,
                md5_sum=md5_sum,
                )
    file.save()
    
    file.uploaded_on=created_date
    file.edited_on=changed_date
    file.save()
    
    process_imported_file.delay(file)           # remove .delay if you want to test this without Celery
    
    return file


@shared_task
def process_imported_file(file):
    """
    Expects a FULL path including extension.
    
    Used by the import_org manage command for processing imported files from the old Drupal site.    
    
    """
    try:
        os.makedirs(file.directory)
    except OSError as e: # pragma no cover
        #return False
        pass

    path, ext = os.path.splitext(file.tmp_path)

    mp4_file_path = os.path.join(file.directory, 'file.mp4')
    ogv_file_path = os.path.join(file.directory, 'file.ogv')

    file.status = FileStatus.READY    
    if ext == '.mp4':
        original_file_path = os.path.join(file.directory, 'original.mp4')        

        print("Copying %s to %s" % (file.tmp_path, original_file_path))
        conditional_copy(file.tmp_path, original_file_path)        # copy the mp4 as original.mp4
        conditional_copy(original_file_path, mp4_file_path)        # copy the mp4 as original.mp4

        if os.path.isfile(path + '.ogv'):                       # copy the ogv as file.ogv if it exists
            print("Copying %s to %s" % (path + '.ogv', ogv_file_path))
            conditional_copy(path + '.ogv', ogv_file_path)
        else:                  
            print("Converting %s to ogv" % file.tmp_path)                                 # convert it if it doesn't
            if convert_video_to_ogv(file) != 0:
                file.status = FileStatus.FAILED
        
    elif ext == '.ogv':
        original_file_path = os.path.join(file.directory, 'original.ogv')

        # don't check for mp4. we only get ogv originals if the mp4 doesn't exist
        print("Copying %s to %s" % (file.tmp_path, original_file_path))
        conditional_copy(file.tmp_path, original_file_path)         # copy the ogv as original
        print("Copying %s to %s" % (file.tmp_path, ogv_file_path))
        conditional_copy(original_file_path, ogv_file_path)

        print("Converting %s to mp4" % file.tmp_path)        
        if convert_video_to_mp4(file) != 0:
            file.status = FileStatus.FAILED            
    else:
        file.status = FileStatus.FAILED
        
    if file.status == FileStatus.READY:
        file.file = os.path.relpath(original_file_path, settings.MEDIA_ROOT)
        print("Generating thumbnail...")
        generate_thumbnail(file, datetime.time(second=1))
        
        print("Success!")
        
    file.save()
    return file.status


def get_duration(video_path):
    """Returns the duration of the file in seconds"""
    with tempfile.SpooledTemporaryFile() as output:
        # ffmpeg outputs the duration to stderr for some reason
        subprocess.call([
            'ffmpeg',
            '-i', video_path,
        ], stderr=output)
        output.seek(0)
        matches = re.search(r"Duration: (?P<hours>\d+):(?P<minutes>\d+):(?P<seconds>[0-9.]+),", output.read())
        if not matches:
            return 0
        vals = matches.groupdict()
        duration = float(vals['hours'])*3600 + float(vals['minutes'])*60 + float(vals['seconds'])
        return duration

def generate_thumbnail(file, time):
    """
    This will capture a PNG of a video at a particular time and save it as a
    PNG in the same directory the video file is in. The thumbnail will be at
    most 64x64 pixels. The aspect ratio is preserved
    """
    stderr = open(file.path_with_extension("log"), "a")
    stdout = stderr

    if settings.TEST:
        stderr = open("/tmp/vcp.log", "w")
        stdout = stderr

    code = subprocess.call([
        'ffmpeg',
        '-i', file.file.path,
        '-ss', time.isoformat(),
        '-vframes', "1",
        # we either want the scale to be 64:-1, or -1:64, depending on whether
        # the video file is wide or tall. The 64 should be in the larger
        # dimension, and the -1 in the smaller dimension. The capture will
        # never be larger than 64px in either dimension
        "-vf", "scale='if (gte (iw\, ih)\, 64\, -1) : if (gte(iw\, ih)\, -1\, 64)'",
        '-y',
        file.path_with_extension("png")
    ], stderr=stderr, stdout=stdout)

    return code == 0

def convert_audio(file):
    """
    Convert a audio file to HTML5 formats
    """
    stderr = open(file.path_with_extension("log"), "a")
    stdout = stderr

    if settings.TEST:
        stderr = open("/tmp/vcp.log", "w")
        stdout = stderr
    
    mp3_code = subprocess.call([
        "ffmpeg",
        "-i", file.file.path,       # input file
        "-f", "mp3",
        '-y',                       # overwrite previous files
        "-ar", "44100", # Set the audio sampling frequency. For output streams it is set by default to the frequency of the corresponding input stream
        "-ab", "128k", # audio bitrate (I think)        
        file.path_with_extension("mp3")
    ], stderr=stderr, stdout=stdout)    
    
    ogg_code = subprocess.call([
        "ffmpeg",
        "-i", file.file.path,       # input file
        "-f", "ogg",
        '-y',                       # overwrite previous files
        '-acodec', 'libvorbis',
        "-ar", "44100", # Set the audio sampling frequency. For output streams it is set by default to the frequency of the corresponding input stream
        "-ab", "128k", 
        file.path_with_extension("ogg")
    ], stderr=stderr, stdout=stdout)     
    
    
    return mp3_code == 0 and ogg_code == 0

def convert_video(file):
    """
    Convert a video to mp4 and ogv
    """    
    mp4_code = convert_video_to_mp4(file)
    ogv_code = convert_video_to_ogv(file)
    
    # returns True if both conversions were successful
    return ogv_code == 0 and mp4_code == 0

def convert_video_to_mp4(file):
    """
    Convert a video to mp4
    Returns 0 on success.
    """    
    
    stderr = open(file.path_with_extension("log"), "a")
    stdout = stderr

    if settings.TEST:
        stderr = open("/tmp/vcp.log", "w")
        stdout = stderr

    mp4_code = subprocess.call([
        "ffmpeg",
        "-i", file.file.path, # input file
        "-b:v", "200k", # bitrate of video
        "-f", "mp4", # force the output to be mp4
        "-vcodec", "libx264", # video codec
        "-acodec", "aac", # audio codec
        "-ac", "2", # audio channels
        "-ar", "44100", # Set the audio sampling frequency. For output streams it is set by default to the frequency of the corresponding input stream
        "-ab", "128k", # audio bitrate (I think)
        "-r", "30", # fps
        # video filter: scale using -2 to ensure that width and height are both even, a requirement for the mp4 codec
        "-vf", "scale='if (gte (iw/512\, ih/384)\, 512) + ifnot(gte(iw/512\, ih/384)\, -2): if (gte(ih/384\, iw/512)\, 384) + ifnot(gte(ih/384\, iw/512)\, -2)'",
        # Overwrite output files without asking.
        '-y',
        '-strict', 'experimental', # since AAC audio encoding is considered experimental, we need this flag
        # output filename
        file.path_with_extension("mp4")
    ], stderr=stderr, stdout=stdout)

    return mp4_code


def convert_video_to_ogv(file):
    """
    Convert a video to ogv
    Returns 0 on success.
    """    
      
    stderr = open(file.path_with_extension("log"), "a")
    stdout = stderr

    if settings.TEST:
        stderr = open("/tmp/vcp.log", "w")
        stdout = stderr

    ogv_code = subprocess.call([
        "ffmpeg",
        "-i", file.file.path, # input file
        "-b:v", "700k", # bitrate of video
        "-r", "30", # fps
        "-f", "ogg", # force the output to be ogg
        "-vcodec", "libtheora", # video codec
        "-acodec", "libvorbis", # audio codec
        "-g", "30", # don't know what this is for
        # video filter: scale using -2 to ensure that width and height are both even, a requirement for the mp4 codec
        "-vf", "scale='if (gte (iw/512\, ih/384)\, 512) + ifnot(gte(iw/512\, ih/384)\, -2): if (gte(ih/384\, iw/512)\, 384) + ifnot(gte(ih/384\, iw/512)\, -2)'",
        # Overwrite output files without asking.
        '-y',
        file.path_with_extension("ogv")
    ], stderr=stderr, stdout=stdout)

    return ogv_code