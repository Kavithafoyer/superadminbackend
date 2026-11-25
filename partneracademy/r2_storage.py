import os
import uuid
from django.core.files.storage import storages

ALLOWED_VIDEO_EXTENSIONS = {"mp4", "webm", "mov", "m4v"}
ALLOWED_IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}
MAX_VIDEO_SIZE = 2 * 1024 * 1024 * 1024   # 2 GB
MAX_IMAGE_SIZE = 5 * 1024 * 1024          # 5 MB


def _storage():
    return storages["academy_videos"]


def _ext(filename):
    return os.path.splitext(filename)[1].lower().lstrip(".")


def validate_file(file, allowed_exts, max_size, label="File"):
    ext = _ext(file.name)
    if ext not in allowed_exts:
        raise ValueError(f"{label} type '.{ext}' is not allowed. Allowed: {', '.join(sorted(allowed_exts))}")
    if file.size > max_size:
        raise ValueError(f"{label} is too large. Max size is {max_size // (1024 * 1024)} MB")


def upload_to_r2(file, folder):
    """Saves the file to R2 and returns the object key to store in the DB."""
    key = f"{folder}/{uuid.uuid4().hex}.{_ext(file.name)}"
    return _storage().save(key, file)


def get_signed_url(key):
    """Temporary playback link (expires after 1 hour by default)."""
    if not key:
        return None
    return _storage().url(key)


def delete_from_r2(key):
    if key:
        try:
            _storage().delete(key)
        except Exception:
            pass