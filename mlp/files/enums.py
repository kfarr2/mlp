from arc import ChoiceEnum

VIDEO_FILE_MIME_TYPES = set([
    'video/x-flv',
    'video/mp4',
    'video/MP2T',
    'video/3gpp',
    'video/quicktime',
    'video/x-msvideo',
    'video/x-ms-wmv',
])

AUDIO_FILE_MIME_TYPES = set([
    'audio/basic',
    'audio/mid',
    'audio/mpeg',
    'audio/mp4',
    'audio/x-aiff',
    'audio/ogg',
    'audio/vorbis',
    'audio/vnd.wav',
])

class FileType(ChoiceEnum):
    UNKNOWN = 0
    VIDEO = 1
    AUDIO = 2

    _choices = (
        (UNKNOWN, "Unknown"),
        (VIDEO, "Video"),
        (AUDIO, "Audio"),
    )

class FileStatus(ChoiceEnum):
    UPLOADED = 1
    READY = 2
    FAILED = 4
    IMPORTED = 8

    _choices = (
        (FAILED, "Failed"),
        (UPLOADED, "Uploaded"),
        (READY, "Ready"),
        (IMPORTED, "Imported"),        
    )
