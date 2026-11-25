import json
import os
import subprocess
import tempfile
import uuid

from django.conf import settings
from django.core.files.storage import storages
from django.db import transaction
from django.db.models import Max, Q
from django.http import HttpResponse
from rest_framework import status
from rest_framework.generics import ListAPIView
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView

from CRMSuperAdmin.views import requestget
from .models import *
from .serializer import *


# done by shajitha
# Pegatto Academy - Super Admin video upload APIs (Cloudflare R2 storage)


def _storage():
    """Cloudflare R2 bucket for academy videos (STORAGES['academy_videos'] in settings.py)."""
    return storages["academy_videos"]


def _reply(data, code=status.HTTP_200_OK):
    return HttpResponse(JSONRenderer().render(data), content_type="application/json", status=code)


def _error(message, code=status.HTTP_400_BAD_REQUEST):
    return _reply({"Error": message}, code)


def _user(request):
    return request.user if getattr(request.user, "is_authenticated", False) else None


def _get_video(video_id):
    if not video_id:
        return None
    return TrainingVideo.objects.filter(id=video_id, Is_Deleted=False).first()


def _truthy(value):
    return str(value).strip().lower() in ("1", "true", "yes", "on")


def _media_url(request, key):
    """Signed (temporary) R2 link for a stored video."""
    if not key:
        return None
    return _storage().url(key)


def _video_key(video_id):
    return f"academy/videos/{video_id}/original.mp4"


def _read_duration(file):
    """Reads video length in seconds from the UPLOADED file with ffprobe (before it goes to R2).
    Returns None if ffprobe is not installed / fails."""
    tmp_path = None
    try:
        if hasattr(file, "temporary_file_path"):          # big uploads are already on disk
            src = file.temporary_file_path()
        else:                                             # small uploads are in memory -> write a temp copy
            with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
                for chunk in file.chunks():
                    tmp.write(chunk)
                tmp_path = src = tmp.name
        probe = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", src],
            capture_output=True, text=True, check=True, timeout=60)
        return int(float(json.loads(probe.stdout)["format"]["duration"]))
    except Exception:
        return None
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)
        try:
            file.seek(0)                                  # rewind so the full file is uploaded
        except Exception:
            pass


# ---------------------------------------------------------------------------
# shared checks used by both "upload file" and "stream URL"
# ---------------------------------------------------------------------------
def _resolve_module(data):
    """Returns (existing_module, new_module_values, error). Creates nothing."""
    if data.get("Module"):
        module = TrainingProductModule.objects.filter(id=data.get("Module"), Is_Deleted=False).first()
        if not module:
            return None, None, "Module not found"
        return module, None, None

    product = (data.get("Product_Name") or "").strip()
    code = (data.get("Module_Code") or "").strip()
    name = (data.get("Module_Name") or "").strip()
    if not product:
        return None, None, "Product_Name is required"
    if not code:
        return None, None, "Module_Code is required"
    if not name:
        return None, None, "Module_Name is required"

    found = TrainingProductModule.objects.filter(Module_Code=code).first()
    if found:
        if found.Is_Deleted:
            return None, None, "Module_Code is already used by a deleted module"
        if found.Product_Name != product:
            return None, None, f"Module_Code {code} belongs to another product"
        if (found.Module_Name or "").strip() != name:
            return None, None, f"Module_Code {code} is already used for '{found.Module_Name}'"
        return found, None, None                       # same module, just another video

    # sequence is checked against ALL rows (deleted ones also keep their number)
    same_product = TrainingProductModule.objects.filter(Product_Name=product)
    mseq = data.get("Module_Sequence_No")
    if mseq in (None, ""):
        mseq = (same_product.aggregate(m=Max("Sequence_No"))["m"] or 0) + 1
    else:
        try:
            mseq = int(mseq)
        except (TypeError, ValueError):
            return None, None, "Module_Sequence_No must be a number"
        if mseq < 1:
            return None, None, "Module_Sequence_No must be 1 or more"
        if same_product.filter(Sequence_No=mseq).exists():
            return None, None, f"Module_Sequence_No {mseq} is already used in {product}"
    return None, dict(Product_Name=product, Product_Code=data.get("Product_Code"),
                      Module_Code=code, Module_Name=name, Title=data.get("Title"),
                      Description=data.get("Module_Description"), Sequence_No=mseq, Status="Draft"), None


def _video_sequence(module, raw):
    existing = TrainingVideo.objects.filter(Module=module, Is_Deleted=False) if module else TrainingVideo.objects.none()
    if raw in (None, ""):
        return (existing.aggregate(m=Max("Sequence_No"))["m"] or 0) + 1, None
    try:
        seq = int(raw)
    except (TypeError, ValueError):
        return None, "Sequence_No must be a number"
    if seq < 1:
        return None, "Sequence_No must be 1 or more"
    if existing.filter(Sequence_No=seq).exists():
        return None, f"Sequence_No {seq} is already used in this module"
    return seq, None


def _min_watch(raw):
    if raw in (None, ""):
        raw = 90
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return None, "Min_Watch_Percentage must be a number"
    if not 1 <= value <= 100:
        return None, "Min_Watch_Percentage must be between 1 and 100"
    return value, None


def _minutes(raw, required):
    if raw in (None, ""):
        if required:
            return None, "Duration_Minutes is required and must be a number"
        return None, None
    try:
        minutes = float(raw)
    except (TypeError, ValueError):
        return None, "Duration_Minutes must be a number"
    if minutes <= 0:
        return None, "Duration_Minutes must be more than 0"
    return minutes, None


def _publish_module(module, user):
    if module and module.Status != "Published":
        module.Status = "Published"
        module.Updated_By = user
        module.save()


def _module_reply(request, module, new_module, video):
    return {
        "Module": module.id, "Module_Id": module.TrainingProduct_Id, "Module_Created": new_module is not None,
        "id": video.id, "Video_Id": video.Video_Id, "Sequence_No": video.Sequence_No,
        "Video_Source": video.Video_Source, "Duration_Seconds": video.Duration_Seconds,
        "Upload_Status": video.Upload_Status, "Status": video.Status,
        "Play_URL": video.Video_URL if video.Video_Source == "URL" else _media_url(request, video.Video_Key)}


# ---------------------------------------------------------------------------
# A. Stream URL  ->  POST  /api/training-video/create-from-url/   (JSON or form-data)
#    One request saves BOTH tables.
# ---------------------------------------------------------------------------
class TrainingVideoCreateFromUrl(APIView):
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def post(self, request, *args, **kwargs):
        try:
            data = request.data
            module, new_module, err = _resolve_module(data)
            if err:
                return _error(err)
            title = (data.get("Video_Title") or "").strip()
            url = (data.get("Video_URL") or "").strip()
            if not title:
                return _error("Video_Title is required")
            if not url.lower().startswith(("http://", "https://")) or " " in url or len(url) > 1000:
                return _error("Video_URL must be a valid http or https link")
            minutes, err = _minutes(data.get("Duration_Minutes"), required=True)
            if err:
                return _error(err)
            seq, err = _video_sequence(module, data.get("Sequence_No"))
            if err:
                return _error(err)
            min_watch, err = _min_watch(data.get("Min_Watch_Percentage"))
            if err:
                return _error(err)
            publish = _truthy(data.get("Publish", True))

            user = _user(request)
            with transaction.atomic():
                if new_module:
                    module = TrainingProductModule.objects.create(Created_By=user, Updated_By=user, **new_module)
                video = TrainingVideo.objects.create(
                    Module=module, Video_Title=title, Description=data.get("Description"),
                    Sequence_No=seq, Video_Source="URL", Video_URL=url,
                    Duration_Seconds=int(round(minutes * 60)),
                    Min_Watch_Percentage=min_watch,
                    Allow_Rewatch=_truthy(data.get("Allow_Rewatch", False)),
                    Upload_Status="Ready", Status="Published" if publish else "Draft",
                    Created_By=user, Updated_By=user)
                if publish:
                    _publish_module(module, user)
            return _reply(_module_reply(request, module, new_module, video), status.HTTP_201_CREATED)
        except Exception as e:
            return _error(str(e))


# ---------------------------------------------------------------------------
# B. Upload file  ->  POST  /api/training-video/upload/   (form-data, file key = "video")
#    File is saved in Cloudflare R2: academy/videos/<Video_Id>/original.mp4
#    DB stores only the path in Video_Key.
# ---------------------------------------------------------------------------
class TrainingVideoUpload(APIView):
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, *args, **kwargs):
        saved_key = None
        try:
            data = request.data
            module, new_module, err = _resolve_module(data)
            if err:
                return _error(err)
            title = (data.get("Video_Title") or "").strip()
            file = request.FILES.get("video")
            if not title:
                return _error("Video_Title is required")
            if not file:
                return _error("video file is required")
            if not file.name.lower().endswith(".mp4"):
                return _error("Only MP4 videos are allowed")
            max_bytes = getattr(settings, "ACADEMY_MAX_VIDEO_BYTES", 2 * 1024 ** 3)
            if file.size > max_bytes:
                return _error(f"File is too large. Maximum is {max_bytes // (1024 ** 2)} MB")
            minutes, err = _minutes(data.get("Duration_Minutes"), required=False)
            if err:
                return _error(err)
            seq, err = _video_sequence(module, data.get("Sequence_No"))
            if err:
                return _error(err)
            min_watch, err = _min_watch(data.get("Min_Watch_Percentage"))
            if err:
                return _error(err)
            publish = _truthy(data.get("Publish", False))

            # duration: from the form, else read it from the uploaded file, else ask for it
            # (checked BEFORE uploading, so a failed request never leaves a file in R2)
            if minutes:
                duration = int(round(minutes * 60))
            else:
                duration = _read_duration(file)
                if not duration:
                    return _error("Could not read video length. Please send Duration_Minutes.")

            user = _user(request)
            with transaction.atomic():
                if new_module:
                    module = TrainingProductModule.objects.create(Created_By=user, Updated_By=user, **new_module)
                video = TrainingVideo(
                    Module=module, Video_Title=title, Description=data.get("Description"),
                    Sequence_No=seq, Min_Watch_Percentage=min_watch,
                    Allow_Rewatch=_truthy(data.get("Allow_Rewatch", False)),
                    Video_Source="Upload", Original_Filename=file.name, File_Size_Bytes=file.size,
                    Duration_Seconds=duration,
                    Upload_Status="Ready", Status="Published" if publish else "Draft",
                    Created_By=user, Updated_By=user)

                saved_key = _storage().save(_video_key(video.Video_Id), file)     # file goes to Cloudflare R2
                video.Video_Key = saved_key
                video.save()
                if publish:
                    _publish_module(module, user)
            return _reply(_module_reply(request, module, new_module, video), status.HTTP_201_CREATED)
        except Exception as e:
            if saved_key:                                   # DB failed -> remove the orphan file from R2
                try:
                    _storage().delete(saved_key)
                except Exception:
                    pass
            return _error(str(e))


# ---------------------------------------------------------------------------
# C. Replace file of an existing uploaded video
#    POST /api/training-video/replace-file/   (form-data: id, video)
# ---------------------------------------------------------------------------
class TrainingVideoReplaceFile(APIView):
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, *args, **kwargs):
        try:
            video = _get_video(request.data.get("id"))
            if not video:
                return _error("Video not found", status.HTTP_404_NOT_FOUND)
            file = request.FILES.get("video")
            if not file:
                return _error("video file is required")
            if not file.name.lower().endswith(".mp4"):
                return _error("Only MP4 videos are allowed")
            max_bytes = getattr(settings, "ACADEMY_MAX_VIDEO_BYTES", 2 * 1024 ** 3)
            if file.size > max_bytes:
                return _error(f"File is too large. Maximum is {max_bytes // (1024 ** 2)} MB")
            minutes, err = _minutes(request.data.get("Duration_Minutes"), required=False)
            if err:
                return _error(err)

            duration = int(round(minutes * 60)) if minutes else (_read_duration(file) or video.Duration_Seconds)

            old_key = video.Video_Key if video.Video_Source == "Upload" else None
            new_key = _storage().save(_video_key(video.Video_Id), file)     # upload the new file FIRST
            video.Video_Key = new_key
            video.Video_Source = "Upload"
            video.Video_URL = None
            video.Original_Filename = file.name
            video.File_Size_Bytes = file.size
            video.Duration_Seconds = duration
            video.Upload_Status = "Ready"
            video.Processing_Error = None
            video.Updated_By = _user(request)
            video.save()

            if old_key and old_key != new_key:                               # then remove the old one
                try:
                    _storage().delete(old_key)
                except Exception:
                    pass
            return _reply(_module_reply(request, video.Module, None, video))
        except Exception as e:
            return _error(str(e))


# ---------------------------------------------------------------------------
# D. DIRECT UPLOAD (big files): browser -> Cloudflare R2. Django never touches the video bytes.
#    1) POST TrainingVideoDirectUploadStart/    (JSON or form-data, NO file)
#         same fields as upload/  + File_Name, File_Size, Duration_Seconds (browser reads it)
#       -> creates the video row (Upload_Status = Uploading) and returns Upload_URL
#    2) Browser sends the file:  PUT Upload_URL   with header  Content-Type: video/mp4
#    3) POST TrainingVideoDirectUploadFinish/   {"id": 7, "Publish": true}
#       or {"id": 7, "Error": "<reason>"} when the browser upload failed / was cancelled
# ---------------------------------------------------------------------------
DIRECT_UPLOAD_EXPIRES = 3600          # Upload_URL is valid for 1 hour
DIRECT_UPLOAD_CONTENT_TYPE = "video/mp4"


def _presigned_put(key, content_type=DIRECT_UPLOAD_CONTENT_TYPE):
    """Temporary link the browser can PUT one file to."""
    storage = _storage()
    client = storage.bucket.meta.client
    return client.generate_presigned_url(
        "put_object",
        Params={"Bucket": storage.bucket_name, "Key": key, "ContentType": content_type},
        ExpiresIn=DIRECT_UPLOAD_EXPIRES)


def _duration_seconds(data):
    """Duration_Seconds (read by the browser) or Duration_Minutes. One of them is required."""
    raw = data.get("Duration_Seconds")
    if raw not in (None, ""):
        try:
            seconds = int(round(float(raw)))
        except (TypeError, ValueError):
            return None, "Duration_Seconds must be a number"
        if seconds <= 0:
            return None, "Duration_Seconds must be more than 0"
        return seconds, None
    minutes, err = _minutes(data.get("Duration_Minutes"), required=True)
    if err:
        return None, err
    return int(round(minutes * 60)), None


def _fail_direct_upload(video, reason, user):
    """Removes the R2 file and hides the row (Is_Deleted frees its Sequence_No for the next try)."""
    try:
        _storage().delete(video.Video_Key)
    except Exception:
        pass
    video.Upload_Status = "Failed"
    video.Processing_Error = str(reason)[:1000]
    video.Is_Deleted = True
    video.Updated_By = user
    video.save()


class TrainingVideoDirectUploadStart(APIView):
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def post(self, request, *args, **kwargs):
        try:
            data = request.data
            module, new_module, err = _resolve_module(data)
            if err:
                return _error(err)
            title = (data.get("Video_Title") or "").strip()
            if not title:
                return _error("Video_Title is required")
            file_name = (data.get("File_Name") or "").strip()
            if not file_name:
                return _error("File_Name is required")
            if not file_name.lower().endswith(".mp4"):
                return _error("Only MP4 videos are allowed")
            try:
                file_size = int(data.get("File_Size") or 0)
            except (TypeError, ValueError):
                return _error("File_Size must be a number")
            if file_size <= 0:
                return _error("File_Size is required")
            max_bytes = getattr(settings, "ACADEMY_MAX_VIDEO_BYTES", 2 * 1024 ** 3)
            if file_size > max_bytes:
                return _error(f"File is too large. Maximum is {max_bytes // (1024 ** 2)} MB")
            duration, err = _duration_seconds(data)
            if err:
                return _error(err)
            seq, err = _video_sequence(module, data.get("Sequence_No"))
            if err:
                return _error(err)
            min_watch, err = _min_watch(data.get("Min_Watch_Percentage"))
            if err:
                return _error(err)

            user = _user(request)
            with transaction.atomic():
                if new_module:
                    module = TrainingProductModule.objects.create(Created_By=user, Updated_By=user, **new_module)
                video = TrainingVideo(
                    Module=module, Video_Title=title, Description=data.get("Description"),
                    Sequence_No=seq, Min_Watch_Percentage=min_watch,
                    Allow_Rewatch=_truthy(data.get("Allow_Rewatch", False)),
                    Video_Source="Upload", Original_Filename=file_name[:255], File_Size_Bytes=file_size,
                    Duration_Seconds=duration,
                    Upload_Status="Uploading", Status="Draft",          # partners only see Ready + Published
                    Created_By=user, Updated_By=user)
                video.Video_Key = f"academy/videos/{video.Video_Id}/{uuid.uuid4().hex}.mp4"
                video.save()

            return _reply({
                "Module": module.id, "Module_Id": module.TrainingProduct_Id, "Module_Created": new_module is not None,
                "id": video.id, "Video_Id": video.Video_Id, "Sequence_No": video.Sequence_No,
                "Upload_Status": video.Upload_Status,
                "Upload_URL": _presigned_put(video.Video_Key),
                "Upload_Method": "PUT",
                "Upload_Headers": {"Content-Type": DIRECT_UPLOAD_CONTENT_TYPE},
                "Expires_In_Seconds": DIRECT_UPLOAD_EXPIRES}, status.HTTP_201_CREATED)
        except Exception as e:
            return _error(str(e))


def _finish_replace(request, video, data):
    """Swaps in the file the browser just uploaded (TrainingVideoUpdate direct mode). Old file is removed after."""
    new_key = data.get("New_Key").strip()
    if not new_key.startswith(f"academy/videos/{video.Video_Id}/") or new_key == video.Video_Key:
        return _error("Invalid New_Key")
    user = _user(request)
    storage = _storage()

    if data.get("Error"):                                         # browser upload failed -> keep the old video
        try:
            storage.delete(new_key)
        except Exception:
            pass
        return _reply({"id": video.id, "Upload_Status": video.Upload_Status,
                       "Message": "Upload cancelled. The current video is unchanged."})

    if not storage.exists(new_key):
        return _error("File not found in storage. Upload the file to Upload_URL first, then call finish.")
    size = storage.size(new_key)
    if size > _max_video_bytes():
        storage.delete(new_key)
        return _error(f"File is too large. Maximum is {_max_video_bytes() // (1024 ** 2)} MB")
    duration = None
    if data.get("Duration_Seconds") not in (None, "") or data.get("Duration_Minutes") not in (None, ""):
        duration, err = _duration_seconds(data)
        if err:
            return _error(err)

    old_key = video.Video_Key if (video.Video_Source or "").upper() == "UPLOAD" else None
    with transaction.atomic():
        video.Video_Key = new_key
        video.Video_Source = "Upload"
        video.Video_URL = None
        if data.get("File_Name"):
            video.Original_Filename = str(data.get("File_Name"))[:255]
        video.File_Size_Bytes = size
        if duration:
            video.Duration_Seconds = duration
        video.Upload_Status = "Ready"
        video.Processing_Error = None
        if "Publish" in data:
            video.Status = "Published" if _truthy(data.get("Publish")) else "Draft"
        video.Updated_By = user
        video.save()
        if video.Status == "Published":
            _publish_module(video.Module, user)
    if old_key and old_key != new_key:
        try:
            storage.delete(old_key)
        except Exception:
            pass
    return _reply(_module_reply(request, video.Module, None, video))


class TrainingVideoDirectUploadFinish(APIView):
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def post(self, request, *args, **kwargs):
        try:
            data = request.data
            video = _get_video(data.get("id"))
            if not video:
                return _error("Video not found", status.HTTP_404_NOT_FOUND)
            if (data.get("New_Key") or "").strip():                  # Edit page: new file for an existing video
                return _finish_replace(request, video, data)
            if video.Upload_Status == "Ready":                       # already finished (double click)
                return _reply(_module_reply(request, video.Module, None, video))
            if video.Upload_Status != "Uploading":
                return _error(f"This upload is {video.Upload_Status}. Start a new upload.")

            user = _user(request)
            if data.get("Error"):                                    # browser upload failed / cancelled
                _fail_direct_upload(video, data.get("Error"), user)
                return _reply({"id": video.id, "Upload_Status": "Failed",
                               "Message": "Upload cancelled. You can upload the video again."})

            storage = _storage()
            if not storage.exists(video.Video_Key):
                return _error("File not found in storage. Upload the file to Upload_URL first, then call finish.")
            size = storage.size(video.Video_Key)
            max_bytes = getattr(settings, "ACADEMY_MAX_VIDEO_BYTES", 2 * 1024 ** 3)
            if size > max_bytes:
                _fail_direct_upload(video, "File is larger than the allowed size", user)
                return _error(f"File is too large. Maximum is {max_bytes // (1024 ** 2)} MB")

            publish = _truthy(data.get("Publish", False))
            with transaction.atomic():
                video.File_Size_Bytes = size                          # real size from R2
                video.Upload_Status = "Ready"
                video.Status = "Published" if publish else "Draft"
                video.Processing_Error = None
                video.Updated_By = user
                video.save()
                if publish:
                    _publish_module(video.Module, user)
            return _reply(_module_reply(request, video.Module, None, video))
        except Exception as e:
            return _error(str(e))


# ===========================================================================
# E. THE 4 MAIN TRAINING VIDEO APIs  (database + Cloudflare R2 together)
#
#   1. POST   TrainingVideoSave/      create   (Video_Source = "URL" or "Upload")
#   2. GET    TrainingVideoGet/       one video (?id=) or a list, with Play_URL from R2
#   3. POST   TrainingVideoUpdate/    edit     ("id" + only the fields that changed; PUT / PATCH also work)
#   4. DELETE TrainingVideoDelete/    delete   (?id=)  row marked deleted + file removed from R2
#
#   Save / Update with a file: send form-data with the file in "video" -> ONE call does DB + R2.
#   Optional for very big files: send File_Name + File_Size instead of the file -> Upload_URL is
#   returned, the browser PUTs the file to R2, then POST TrainingVideoDirectUploadFinish/.
#
#   Video_Source = "URL"    : Video_URL + Duration_Minutes (or Duration_Seconds)  -> saved, done
#   Video_Source = "Upload" :
#       a) form-data with the file in "video"      -> Django saves it to R2       -> saved, done (small files)
#       b) NO file, send File_Name + File_Size + Duration_Seconds                  (any size, recommended)
#            -> response has Upload_URL (+ New_Key on edit)
#            -> browser PUTs the file to Upload_URL with the Upload_Headers
#            -> POST TrainingVideoDirectUploadFinish/ {id, Publish}            (create)
#                                                     {id, New_Key, File_Name, Duration_Seconds}  (edit)
#   Formats: MP4, WebM, MOV  |  max size: ACADEMY_MAX_VIDEO_BYTES (default 2 GB)
# ===========================================================================
VIDEO_CONTENT_TYPES = {"mp4": "video/mp4", "webm": "video/webm", "mov": "video/quicktime"}


def _max_video_bytes():
    return getattr(settings, "ACADEMY_MAX_VIDEO_BYTES", 2 * 1024 ** 3)


def _video_ext(file_name):
    ext = os.path.splitext(file_name or "")[1].lower().lstrip(".")
    return ext if ext in VIDEO_CONTENT_TYPES else None


def _new_video_key(video, ext):
    return f"academy/videos/{video.Video_Id}/{uuid.uuid4().hex}.{ext}"


def _check_url(raw):
    url = (raw or "").strip()
    if not url.lower().startswith(("http://", "https://")) or " " in url or len(url) > 1000:
        return None, "Video_URL must be a valid http or https link"
    return url, None


def _check_upload_input(request):
    """Returns (mode, info, error). mode = 'file' (file sent to Django) or 'direct' (browser -> R2)."""
    data = request.data
    max_bytes = _max_video_bytes()
    file = request.FILES.get("video")
    if file:
        name, size = file.name, file.size
    else:
        name = (data.get("File_Name") or "").strip()
        if not name:
            return None, None, "Choose a video file (send 'video', or File_Name + File_Size for a direct upload)"
        try:
            size = int(data.get("File_Size") or 0)
        except (TypeError, ValueError):
            return None, None, "File_Size must be a number"
        if size <= 0:
            return None, None, "File_Size is required"
    ext = _video_ext(name)
    if not ext:
        return None, None, "Only MP4, WebM or MOV videos are allowed"
    if size > max_bytes:
        return None, None, f"File is too large. Maximum is {max_bytes // (1024 ** 2)} MB"
    return ("file" if file else "direct"), {"file": file, "name": name, "size": size, "ext": ext}, None


def _has_duration(data):
    return data.get("Duration_Seconds") not in (None, "") or data.get("Duration_Minutes") not in (None, "")


def _direct_upload_reply(video, key, ext):
    content_type = VIDEO_CONTENT_TYPES[ext]
    return {
        "Upload_URL": _presigned_put(key, content_type),
        "Upload_Method": "PUT",
        "Upload_Headers": {"Content-Type": content_type},
        "Expires_In_Seconds": DIRECT_UPLOAD_EXPIRES,
        "Next_Step": "PUT the file to Upload_URL, then call TrainingVideoDirectUploadFinish/"}


class TrainingVideoSave(APIView):
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def post(self, request, *args, **kwargs):
        saved_key = None
        try:
            data = request.data
            source = (data.get("Video_Source") or "").strip().upper()
            if source not in ("URL", "UPLOAD"):
                return _error("Video_Source must be URL or Upload")
            module, new_module, err = _resolve_module(data)
            if err:
                return _error(err)
            title = (data.get("Video_Title") or "").strip()
            if not title:
                return _error("Video_Title is required")
            seq, err = _video_sequence(module, data.get("Sequence_No"))
            if err:
                return _error(err)
            min_watch, err = _min_watch(data.get("Min_Watch_Percentage"))
            if err:
                return _error(err)
            publish = _truthy(data.get("Publish", True))

            url = mode = info = None
            if source == "URL":
                url, err = _check_url(data.get("Video_URL"))
                if err:
                    return _error(err)
                duration, err = _duration_seconds(data)
            else:
                mode, info, err = _check_upload_input(request)
                if err:
                    return _error(err)
                if _has_duration(data):
                    duration, err = _duration_seconds(data)
                else:
                    duration = _read_duration(info["file"]) if mode == "file" else None
                    err = None if duration else "Video length is required. Send Duration_Seconds or Duration_Minutes."
            if err:
                return _error(err)

            user = _user(request)
            with transaction.atomic():
                if new_module:
                    module = TrainingProductModule.objects.create(Created_By=user, Updated_By=user, **new_module)
                video = TrainingVideo(
                    Module=module, Video_Title=title, Description=data.get("Description"),
                    Sequence_No=seq, Min_Watch_Percentage=min_watch,
                    Allow_Rewatch=_truthy(data.get("Allow_Rewatch", False)),
                    Duration_Seconds=duration, Created_By=user, Updated_By=user)
                if source == "URL":
                    video.Video_Source = "URL"
                    video.Video_URL = url
                    video.Upload_Status = "Ready"
                    video.Status = "Published" if publish else "Draft"
                else:
                    video.Video_Source = "Upload"
                    video.Original_Filename = info["name"][:255]
                    video.File_Size_Bytes = info["size"]
                    video.Video_Key = _new_video_key(video, info["ext"])
                    if mode == "file":
                        saved_key = _storage().save(video.Video_Key, info["file"])     # Django -> R2
                        video.Video_Key = saved_key
                        video.Upload_Status = "Ready"
                        video.Status = "Published" if publish else "Draft"
                    else:
                        video.Upload_Status = "Uploading"      # becomes Ready in DirectUploadFinish
                        video.Status = "Draft"
                video.save()
                if video.Status == "Published":
                    _publish_module(module, user)

            output = _module_reply(request, module, new_module, video)
            if mode == "direct":
                output["Play_URL"] = None
                output.update(_direct_upload_reply(video, video.Video_Key, info["ext"]))
            return _reply(output, status.HTTP_201_CREATED)
        except Exception as e:
            if saved_key:                                   # DB failed -> remove the orphan file from R2
                try:
                    _storage().delete(saved_key)
                except Exception:
                    pass
            return _error(str(e))


class TrainingVideoUpdate(APIView):
    """Edit Video page. Always send "id"; send only the fields that changed."""
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def put(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        new_saved = None
        try:
            data = request.data
            video = _get_video(data.get("id"))
            if not video:
                return _error("Video not found", status.HTTP_404_NOT_FOUND)
            if video.Upload_Status == "Uploading":
                return _error("This video is still uploading. Finish or cancel that upload first.")
            current_source = (video.Video_Source or "").upper()

            # ---- validate everything first, change nothing yet ----
            module = video.Module
            if data.get("Module") not in (None, "") and str(data.get("Module")) != str(video.Module_id):
                module = TrainingProductModule.objects.filter(id=data.get("Module"), Is_Deleted=False).first()
                if not module:
                    return _error("Module not found")
            others = TrainingVideo.objects.filter(Module=module, Is_Deleted=False).exclude(id=video.id)
            seq = video.Sequence_No
            if data.get("Sequence_No") not in (None, ""):
                try:
                    seq = int(data.get("Sequence_No"))
                except (TypeError, ValueError):
                    return _error("Sequence_No must be a number")
                if seq < 1:
                    return _error("Sequence_No must be 1 or more")
            elif module.id != video.Module_id:
                seq = (others.aggregate(m=Max("Sequence_No"))["m"] or 0) + 1
            if others.filter(Sequence_No=seq).exists():
                return _error(f"Sequence_No {seq} is already used in this module")

            title = video.Video_Title
            if "Video_Title" in data:
                title = (data.get("Video_Title") or "").strip()
                if not title:
                    return _error("Video_Title is required")
            min_watch = video.Min_Watch_Percentage
            if data.get("Min_Watch_Percentage") not in (None, ""):
                min_watch, err = _min_watch(data.get("Min_Watch_Percentage"))
                if err:
                    return _error(err)

            source = (data.get("Video_Source") or current_source).strip().upper()
            url = mode = info = None
            if source == "URL":
                if data.get("Video_URL") not in (None, "") or current_source != "URL":
                    url, err = _check_url(data.get("Video_URL"))
                    if err:
                        return _error(err)
            elif source == "UPLOAD":
                if request.FILES.get("video") or data.get("File_Name"):
                    mode, info, err = _check_upload_input(request)
                    if err:
                        return _error(err)
                elif current_source != "UPLOAD":
                    return _error("Choose a video file to switch this lesson to Upload")
            else:
                return _error("Video_Source must be URL or Upload")

            duration = video.Duration_Seconds
            if _has_duration(data) and mode != "direct":         # direct: duration is sent to finish with the file
                duration, err = _duration_seconds(data)
                if err:
                    return _error(err)
            elif mode == "file":
                duration = _read_duration(info["file"]) or duration

            # ---- apply ----
            user = _user(request)
            old_key = None
            new_key = None
            with transaction.atomic():
                video.Module = module
                video.Sequence_No = seq
                video.Video_Title = title
                if "Description" in data:
                    video.Description = data.get("Description")
                video.Min_Watch_Percentage = min_watch
                if "Allow_Rewatch" in data:
                    video.Allow_Rewatch = _truthy(data.get("Allow_Rewatch"))
                video.Duration_Seconds = duration

                if url:                                              # new / changed stream link
                    if current_source == "UPLOAD":
                        old_key = video.Video_Key                    # uploaded file is no longer needed
                    video.Video_Source = "URL"
                    video.Video_URL = url
                    video.Video_Key = None
                    video.Original_Filename = None
                    video.File_Size_Bytes = None
                elif mode == "file":                                 # new file sent through Django
                    new_saved = _storage().save(_new_video_key(video, info["ext"]), info["file"])
                    if current_source == "UPLOAD":
                        old_key = video.Video_Key
                    video.Video_Source = "Upload"
                    video.Video_URL = None
                    video.Video_Key = new_saved
                    video.Original_Filename = info["name"][:255]
                    video.File_Size_Bytes = info["size"]
                elif mode == "direct":                               # file comes later from the browser
                    new_key = _new_video_key(video, info["ext"])

                video.Upload_Status = "Ready"
                video.Processing_Error = None
                if "Publish" in data:
                    video.Status = "Published" if _truthy(data.get("Publish")) else "Draft"
                video.Updated_By = user
                video.save()
                if video.Status == "Published":
                    _publish_module(module, user)

            if old_key and old_key != video.Video_Key:               # remove the replaced file from R2
                try:
                    _storage().delete(old_key)
                except Exception:
                    pass

            output = _module_reply(request, module, None, video)
            if mode == "direct":
                output["New_Key"] = new_key
                output.update(_direct_upload_reply(video, new_key, info["ext"]))
            return _reply(output)
        except Exception as e:
            if new_saved:
                try:
                    _storage().delete(new_saved)
                except Exception:
                    pass
            return _error(str(e))


def _video_details(request, video, check_file=False):
    """One video with its module details and a playable link (signed R2 link for uploaded files)."""
    output = dict(TrainingVideoSerializers(video).data)
    module = video.Module
    output.update({
        "Product_Name": module.Product_Name if module else None,
        "Product_Code": module.Product_Code if module else None,
        "Module_Name": module.Module_Name if module else None,
        "Module_Code": module.Module_Code if module else None,
        "Course_Title": module.Title if module else None,
        "Duration_Minutes": round(video.Duration_Seconds / 60, 2) if video.Duration_Seconds else None,
        "Play_URL": _play_url(request, video),
        "Thumbnail_URL": _media_url(request, video.Thumbnail_Key)})
    if check_file and (video.Video_Source or "").upper() == "UPLOAD":
        try:
            output["File_Exists"] = bool(video.Video_Key) and _storage().exists(video.Video_Key)
        except Exception:
            output["File_Exists"] = None
    return output


# ---------------------------------------------------------------------------
# GET  TrainingVideoGet/?id=10                    -> one video (+ File_Exists check in R2)
#      TrainingVideoGet/                          -> all videos
#      TrainingVideoGet/?Module=3                 -> videos of one module
#      TrainingVideoGet/?Product_Name=Pegatto CRM -> videos of one product
#      TrainingVideoGet/?search=lead&Status=Published   (filters can be combined)
# Play_URL = signed Cloudflare R2 link (uploaded file) or the stream URL
# ---------------------------------------------------------------------------
class TrainingVideoGet(APIView):
    def get(self, request, *args, **kwargs):
        try:
            params = request.query_params
            if params.get("id"):
                video = _get_video(params.get("id"))
                if not video:
                    return _error("Video not found", status.HTTP_404_NOT_FOUND)
                return _reply(_video_details(request, video, check_file=True))

            videos = TrainingVideo.objects.filter(Is_Deleted=False).select_related("Module")
            if params.get("Module"):
                videos = videos.filter(Module_id=params.get("Module"))
            if params.get("Product_Name"):
                videos = videos.filter(Module__Product_Name=params.get("Product_Name"))
            if params.get("Status"):
                videos = videos.filter(Status=params.get("Status"))
            if params.get("Video_Source"):
                videos = videos.filter(Video_Source__iexact=params.get("Video_Source"))
            search = (params.get("search") or "").strip()
            if search:
                videos = videos.filter(
                    Q(Video_Id__icontains=search) | Q(Video_Title__icontains=search) |
                    Q(Module__Module_Name__icontains=search) | Q(Module__Module_Code__icontains=search) |
                    Q(Module__Product_Name__icontains=search) | Q(Module__Title__icontains=search))
            videos = videos.order_by("Module__Product_Name", "Module__Sequence_No", "Module_id", "Sequence_No", "id")

            rows = [_video_details(request, video) for video in videos]
            return _reply({
                "Total_Videos": len(rows),
                "Total_Duration_Seconds": sum(v.Duration_Seconds or 0 for v in videos),
                "Total_Modules": len({v.Module_id for v in videos if v.Module_id}),
                "Total_Products": len({v.Module.Product_Name for v in videos if v.Module}),
                "Videos": rows})
        except Exception as e:
            return _error(str(e))


# ---------------------------------------------------------------------------
# DELETE TrainingVideoDelete/?id=10     (POST {"id": 10} also works)
# Marks the row deleted (partner progress history is kept) and removes the video
# file + thumbnail from Cloudflare R2. Stream-URL videos have no file in R2.
# ---------------------------------------------------------------------------
class TrainingVideoDelete(APIView):
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def delete(self, request, *args, **kwargs):
        return self._delete(request, request.query_params.get("id") or request.data.get("id"))

    def post(self, request, *args, **kwargs):
        return self._delete(request, request.data.get("id") or request.query_params.get("id"))

    def _delete(self, request, video_id):
        try:
            video = _get_video(video_id)
            if not video:
                return _error("Video not found or already deleted", status.HTTP_404_NOT_FOUND)
            keys = [video.Thumbnail_Key]
            if (video.Video_Source or "").upper() == "UPLOAD":
                keys.append(video.Video_Key)

            video.Is_Deleted = True
            video.Updated_By = _user(request)
            video.save()

            removed, failed = [], []
            for key in keys:
                if not key:
                    continue
                try:
                    _storage().delete(key)
                    removed.append(key)
                except Exception:
                    failed.append(key)
            return _reply({
                "id": video.id, "Video_Id": video.Video_Id, "Video_Title": video.Video_Title,
                "Deleted": True,
                "Removed_From_Storage": removed,
                "Storage_Delete_Failed": failed,
                "Message": "Video deleted" + (" (file could not be removed from storage)" if failed else "")})
        except Exception as e:
            return _error(str(e))


# ---------------------------------------------------------------------------
# Common: publish, preview, list videos of a module
# ---------------------------------------------------------------------------
# POST /api/training-video/publish/   {"id": 1, "action": "publish"}
class TrainingVideoPublish(APIView):
    def post(self, request, *args, **kwargs):
        try:
            video = _get_video(request.data.get("id"))
            if not video:
                return _error("Video not found", status.HTTP_404_NOT_FOUND)
            action = (request.data.get("action") or "publish").lower()
            user = _user(request)
            with transaction.atomic():
                if action == "publish":
                    if video.Upload_Status != "Ready":
                        return _error("Video is not ready yet")
                    video.Status = "Published"
                    _publish_module(video.Module, user)
                elif action == "unpublish":
                    video.Status = "Draft"
                else:
                    return _error("action must be publish or unpublish")
                video.Updated_By = user
                video.save()
            return _reply(TrainingVideoSerializers(video).data)
        except Exception as e:
            return _error(str(e))


# GET /api/training-video/preview/?id=1
class TrainingVideoPreview(APIView):
    def get(self, request, *args, **kwargs):
        try:
            video = _get_video(request.query_params.get("id"))
            if not video:
                return _error("Video not found", status.HTTP_404_NOT_FOUND)
            if video.Video_Source == "URL":
                return _reply({"id": video.id, "Video_Source": "URL", "Play_URL": video.Video_URL,
                               "Duration_Seconds": video.Duration_Seconds})
            if not video.Video_Key or not _storage().exists(video.Video_Key):
                return _error("Video file not found on server", status.HTTP_404_NOT_FOUND)
            return _reply({"id": video.id, "Video_Source": "Upload",
                           "Play_URL": _media_url(request, video.Video_Key),
                           "Duration_Seconds": video.Duration_Seconds})
        except Exception as e:
            return _error(str(e))


# GET /api/training-video/module-videos/?Module=1    (videos of one module in order, with Play_URL)
class TrainingVideoByModule(APIView):
    def get(self, request, *args, **kwargs):
        try:
            module_id = request.query_params.get("Module")
            if not module_id:
                return _error("Module is required")
            videos = TrainingVideo.objects.filter(Module_id=module_id, Is_Deleted=False).order_by("Sequence_No")
            if _truthy(request.query_params.get("Published_Only", False)):
                videos = videos.filter(Status="Published")
            output = []
            for video in videos:
                output.append({
                    "id": video.id, "Video_Id": video.Video_Id, "Video_Title": video.Video_Title,
                    "Description": video.Description, "Sequence_No": video.Sequence_No,
                    "Video_Source": video.Video_Source, "Duration_Seconds": video.Duration_Seconds,
                    "Min_Watch_Percentage": video.Min_Watch_Percentage, "Allow_Rewatch": video.Allow_Rewatch,
                    "Upload_Status": video.Upload_Status, "Status": video.Status,
                    "Play_URL": video.Video_URL if video.Video_Source == "URL" else _media_url(request, video.Video_Key)})
            return _reply(output)
        except Exception as e:
            return _error(str(e))


# ---------------------------------------------------------------------------
# TrainingProductModule
# ---------------------------------------------------------------------------
class TrainingProductModuleCRUD(APIView):
    def post(self, request, *args, **kwargs):
        try:
            data = request.data
            serializer = TrainingProductModuleSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                output = JSONRenderer().render(serializer.data)
                return HttpResponse(output, content_type='application/json', status=status.HTTP_201_CREATED)
            output = JSONRenderer().render(serializer.errors)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, *args, **kwargs):
        try:
            data = request.query_params
            id = data['id']
            module = TrainingProductModule.objects.get(id=id)
            serializer = TrainingProductModuleSerializers(module)
            output = JSONRenderer().render(serializer.data)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, *args, **kwargs):
        try:
            data = request.data
            id = data['id']
            module = TrainingProductModule.objects.get(id=id)
            serializer = TrainingProductModuleSerializer(instance=module, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                output = JSONRenderer().render(serializer.data)
                return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
            output = JSONRenderer().render(serializer.errors)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        try:
            data = request.query_params
            id = data['id']
            module = TrainingProductModule.objects.get(id=id)
            serializer = TrainingProductModuleSerializer(module, {"Is_Deleted": True}, partial=True)
            if serializer.is_valid():
                serializer.save()
                # module deleted -> its videos are deleted too, and their files are removed from Cloudflare R2
                videos = TrainingVideo.objects.filter(Module=module, Is_Deleted=False)
                r2_keys = []
                for video in videos:
                    r2_keys.append(video.Thumbnail_Key)
                    if video.Video_Source == "Upload":
                        r2_keys.append(video.Video_Key)
                videos.update(Is_Deleted=True)
                for key in r2_keys:
                    if key:
                        try:
                            _storage().delete(key)
                        except Exception:
                            pass
            output = JSONRenderer().render(serializer.data)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, *args, **kwargs):
        try:
            data = request.data
            if not data:
                raise TypeError("Request data cannot be empty")
            id = data.get('id')
            module = TrainingProductModule.objects.get(id=id)
            serializer = TrainingProductModuleSerializer(instance=module, data=data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        except TrainingProductModule.DoesNotExist as e:
            return Response({"Error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"Error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class TrainingProductModuleSearch(ListAPIView):
    queryset = TrainingProductModule.objects.filter(Is_Deleted=False)
    serializer_class = TrainingProductModuleSerializers

    def get_queryset(self):
        try:
            search = self.request.GET.get("search")
            queryset = TrainingProductModule.objects.filter(Is_Deleted=False)
            if search:
                queryset = queryset.filter(
                    Q(TrainingProduct_Id__icontains=search) |
                    Q(Product_Name__icontains=search) |
                    Q(Product_Code__icontains=search) |
                    Q(Module_Code__icontains=search) |
                    Q(Module_Name__icontains=search) |
                    Q(Title__icontains=search) |
                    Q(Status__icontains=search))
            return queryset.order_by("-id")
        except Exception as e:
            raise Exception(f"Error while fetching TrainingProductModule: {str(e)}")


class TrainingProductModuleFilter(APIView):
    def post(self, request, *args, **kwargs):
        try:
            data = request.data
            filters = {"Is_Deleted": False}
            if data.get("Product_Code"):
                filters["Product_Code__icontains"] = data["Product_Code"]
            if data.get("Product_Name"):
                filters["Product_Name__icontains"] = data["Product_Name"]
            if data.get("Module_Code"):
                filters["Module_Code__icontains"] = data["Module_Code"]
            if data.get("Status"):
                filters["Status"] = data["Status"]
            if data.get("Created_Date"):
                filters["Created_Date__range"] = data["Created_Date"]
            page = data.get("page", 1)
            return requestget(
                model=TrainingProductModule,
                serializer=TrainingProductModuleSerializers,
                data=filters,
                page=page,
                Operator="and")
        except Exception as e:
            return _error(f"Error while filtering TrainingProductModule: {str(e)}")


class TrainingProductModuleList(ListAPIView):
    queryset = TrainingProductModule.objects.all()
    serializer_class = TrainingProductModuleSerializers

    def get_queryset(self):
        try:
            module = TrainingProductModule.objects.filter(Q(Is_Deleted=False)).order_by('-id')
            return module
        except Exception as e:
            raise Exception(f"Error while fetching module: {str(e)}")


class TrainingProductModuleWithoutPagination(APIView):
    def get(self, request, *args, **kwargs):
        try:
            module = TrainingProductModule.objects.filter(Q(Is_Deleted__exact=False)).order_by('-id')
            serialize = TrainingProductModuleSerializers(module, many=True)
            output = JSONRenderer().render(serialize.data)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)


# ---------------------------------------------------------------------------
# TrainingVideo
# ---------------------------------------------------------------------------
class TrainingVideoCRUD(APIView):
    # NOTE: create videos through create-from-url / upload, not this POST
    def post(self, request, *args, **kwargs):
        try:
            data = request.data
            serializer = TrainingVideoSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                output = JSONRenderer().render(serializer.data)
                return HttpResponse(output, content_type='application/json', status=status.HTTP_201_CREATED)
            output = JSONRenderer().render(serializer.errors)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, *args, **kwargs):
        try:
            data = request.query_params
            id = data['id']
            video = TrainingVideo.objects.get(id=id)
            serializer = TrainingVideoSerializers(video)
            output = serializer.data
            output["Play_URL"] = video.Video_URL if video.Video_Source == "URL" else _media_url(request, video.Video_Key)
            return HttpResponse(JSONRenderer().render(output), content_type='application/json', status=status.HTTP_200_OK)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, *args, **kwargs):
        try:
            data = request.data
            id = data['id']
            video = TrainingVideo.objects.get(id=id)
            serializer = TrainingVideoSerializer(instance=video, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                output = JSONRenderer().render(serializer.data)
                return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
            output = JSONRenderer().render(serializer.errors)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        try:
            data = request.query_params
            id = data['id']
            video = TrainingVideo.objects.get(id=id)
            r2_keys = [video.Thumbnail_Key]
            if video.Video_Source == "Upload":
                r2_keys.append(video.Video_Key)
            serializer = TrainingVideoSerializer(video, {"Is_Deleted": True}, partial=True)
            if serializer.is_valid():
                serializer.save()
                # row stays (soft delete keeps partner progress history), the file is removed from Cloudflare R2
                for key in r2_keys:
                    if key:
                        try:
                            _storage().delete(key)
                        except Exception:
                            pass
            output = JSONRenderer().render(serializer.data)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, *args, **kwargs):
        try:
            data = request.data
            if not data:
                raise TypeError("Request data cannot be empty")
            id = data.get('id')
            video = TrainingVideo.objects.get(id=id)
            serializer = TrainingVideoSerializer(instance=video, data=data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        except TrainingVideo.DoesNotExist as e:
            return Response({"Error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"Error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class TrainingVideoSearch(ListAPIView):
    queryset = TrainingVideo.objects.filter(Is_Deleted=False)
    serializer_class = TrainingVideoSerializers

    def get_queryset(self):
        try:
            search = self.request.GET.get("search")
            queryset = TrainingVideo.objects.filter(Is_Deleted=False)
            if search:
                queryset = queryset.filter(
                    Q(Video_Id__icontains=search) |
                    Q(Video_Title__icontains=search) |
                    Q(Module__Module_Name__icontains=search) |
                    Q(Module__Module_Code__icontains=search) |
                    Q(Upload_Status__icontains=search) |
                    Q(Status__icontains=search))
            return queryset.order_by("-id")
        except Exception as e:
            raise Exception(f"Error while fetching TrainingVideo: {str(e)}")


class TrainingVideoFilter(APIView):
    def post(self, request, *args, **kwargs):
        try:
            data = request.data
            filters = {"Is_Deleted": False}
            if data.get("Module"):
                filters["Module_id"] = data["Module"]
            if data.get("Video_Title"):
                filters["Video_Title__icontains"] = data["Video_Title"]
            if data.get("Video_Source"):
                filters["Video_Source"] = data["Video_Source"]
            if data.get("Upload_Status"):
                filters["Upload_Status"] = data["Upload_Status"]
            if data.get("Status"):
                filters["Status"] = data["Status"]
            if data.get("Created_Date"):
                filters["Created_Date__range"] = data["Created_Date"]
            page = data.get("page", 1)
            return requestget(
                model=TrainingVideo,
                serializer=TrainingVideoSerializers,
                data=filters,
                page=page,
                Operator="and")
        except Exception as e:
            return _error(f"Error while filtering TrainingVideo: {str(e)}")


class TrainingVideoList(ListAPIView):
    queryset = TrainingVideo.objects.all()
    serializer_class = TrainingVideoSerializers

    def get_queryset(self):
        try:
            video = TrainingVideo.objects.filter(Q(Is_Deleted=False)).order_by('-id')
            return video
        except Exception as e:
            raise Exception(f"Error while fetching video: {str(e)}")


class TrainingVideoWithoutPagination(APIView):
    def get(self, request, *args, **kwargs):
        try:
            video = TrainingVideo.objects.filter(Q(Is_Deleted__exact=False)).order_by('-id')
            serialize = TrainingVideoSerializers(video, many=True)
            output = JSONRenderer().render(serialize.data)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)


# used to get the  module wise videos of the specific product alone by passing the product name and the optional if published is true
# Partner screen: also pass Partner=<partner id>  -> only published videos, and every video gets that partner's
#                 State (Completed / In Progress / Available / Locked), Can_Play, Watch_Percentage, Last_Position_Seconds.
#                 Play_URL is hidden for locked videos (the player gets it from PartnerVideoPlay).

class ListOfProductWiseVideos(APIView):
    def get(self, request, *args, **kwargs):
        try:
            data = request.query_params
            product_name = (data.get('Product_Name') or '').strip()
            if not product_name:
                output = JSONRenderer().render({"Error": "Product_Name is required"})
                return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

            # partner view (optional)
            partner = None
            team_member = _get_team_member(request)
            states, progress = {}, {}
            if data.get('Partner') or data.get('Partner_Id') or team_member:
                partner = _get_partner(request)
                if not partner:
                    output = JSONRenderer().render({"Error": "Partner not found"})
                    return HttpResponse(output, content_type='application/json', status=status.HTTP_404_NOT_FOUND)
                if product_name not in _partner_products(partner):
                    output = JSONRenderer().render({"Error": "This product is not assigned to you"})
                    return HttpResponse(output, content_type='application/json', status=status.HTTP_403_FORBIDDEN)
                progress, state_list, total, done, current = _product_summary(partner, product_name, team_member=team_member)
                states = {video.id: state for video, state in state_list}

            published_only = partner is not None or str(data.get('Published_Only', '')).lower() in ('1', 'true', 'yes')
            modules = TrainingProductModule.objects.filter(Product_Name=product_name, Is_Deleted=False)
            if published_only:
                modules = modules.filter(Status="Published")
            modules = modules.order_by('Sequence_No', 'id')

            module_list = []
            total_videos = 0
            completed_videos = 0
            for module in modules:
                videos = TrainingVideo.objects.filter(Module=module, Is_Deleted=False).order_by('Sequence_No', 'id')
                if published_only:
                    videos = videos.filter(Status="Published")

                video_list = []
                for video in videos:
                    video_data = TrainingVideoSerializer(video).data
                    video_data["Play_URL"] = video.Video_URL if video.Video_Source == "URL" else _media_url(request, video.Video_Key)
                    if partner:
                        state = states.get(video.id, "Locked")
                        row = progress.get(video.id)
                        video_data["State"] = state
                        video_data["Can_Play"] = state in ("Available", "In Progress")      # completed / locked: never
                        video_data["Watch_Percentage"] = float(row.Watch_Percentage) if row else 0
                        video_data["Last_Position_Seconds"] = row.Last_Position_Seconds if row else 0
                        video_data["Furthest_Watched_Seconds"] = row.Watched_Seconds if row else 0
                        if not video_data["Can_Play"]:
                            video_data["Play_URL"] = None
                        if state == "Completed":
                            completed_videos += 1
                    video_list.append(video_data)

                module_data = TrainingProductModuleSerializer(module).data
                module_data["Total_Videos"] = len(video_list)
                module_data["Total_Duration_Seconds"] = sum(v.Duration_Seconds or 0 for v in videos)
                if partner:
                    done_here = sum(1 for v in video_list if v["State"] == "Completed")
                    module_data["Completed_Videos"] = done_here
                    if video_list and done_here == len(video_list):
                        module_data["State"] = "Completed"
                    elif all(v["State"] == "Locked" for v in video_list):
                        module_data["State"] = "Locked"
                    else:
                        module_data["State"] = "In Progress"
                module_data["Videos"] = video_list
                module_list.append(module_data)
                total_videos += len(video_list)

            result = {
                "Product_Name": product_name,
                "Total_Modules": len(module_list),
                "Total_Videos": total_videos,
                "Modules": module_list}
            if partner:
                result["Partner"] = partner.id
                result["Completed_Videos"] = completed_videos
                result["Progress_Percentage"] = round(completed_videos * 100 / total_videos) if total_videos else 0
                result["Current_Video"] = _video_brief(current)
                result["Product_Completed"] = bool(total_videos) and completed_videos >= total_videos
                result.update(_certificate_info(partner, product_name, total, done, team_member=team_member))
            output = JSONRenderer().render(result)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)





# ModuleEnrollment

class ModuleEnrollmentCRUD(APIView):
    def post(self, request, *args, **kwargs):
        try:
            data = request.data
            serializer = ModuleEnrollmentSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                output = JSONRenderer().render(serializer.data)
                return HttpResponse(output, content_type='application/json', status=status.HTTP_201_CREATED)
            output = JSONRenderer().render(serializer.errors)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, *args, **kwargs):
        try:
            data = request.query_params
            id = data['id']
            module = ModuleEnrollment.objects.get(id=id)
            serializer = ModuleEnrollmentSerializers(module)
            output = JSONRenderer().render(serializer.data)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, *args, **kwargs):
        try:
            data = request.data
            id = data['id']
            module = ModuleEnrollment.objects.get(id=id)
            serializer = ModuleEnrollmentSerializer(instance=module, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                output = JSONRenderer().render(serializer.data)
                return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
            output = JSONRenderer().render(serializer.errors)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        try:
            data = request.query_params
            id = data['id']
            module = ModuleEnrollment.objects.get(id=id)
            serializer = ModuleEnrollmentSerializer(module, {"Is_Deleted": True}, partial=True)
            if serializer.is_valid():
                serializer.save()
            output = JSONRenderer().render(serializer.data)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, *args, **kwargs):
        try:
            data = request.data
            if not data:
                raise TypeError("Request data cannot be empty")
            id = data.get('id')
            module = ModuleEnrollment.objects.get(id=id)
            serializer = ModuleEnrollmentSerializer(instance=module, data=data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        except ModuleEnrollment.DoesNotExist as e:
            return Response({"Error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"Error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ModuleEnrollmentSearch(ListAPIView):
    queryset = ModuleEnrollment.objects.filter(Is_Deleted=False)
    serializer_class = ModuleEnrollmentSerializers

    def get_queryset(self):
        try:
            search = self.request.GET.get("search")
            queryset = ModuleEnrollment.objects.filter(Is_Deleted=False)
            if search:
                queryset = queryset.filter(
                    Q(Enrollment_Id__icontains=search) |
                    Q(Module__Module_Name__icontains=search) |
                    Q(Module__Module_Code__icontains=search) |
                    Q(Status__icontains=search))
            return queryset.order_by("-id")
        except Exception as e:
            raise Exception(f"Error while fetching ModuleEnrollment: {str(e)}")


class ModuleEnrollmentFilter(APIView):
    def post(self, request, *args, **kwargs):
        try:
            data = request.data
            filters = {"Is_Deleted": False}
            if data.get("Partner"):
                filters["Partner_id"] = data["Partner"]
            if data.get("Module"):
                filters["Module_id"] = data["Module"]
            if data.get("Status"):
                filters["Status"] = data["Status"]
            if data.get("Started_Date"):
                filters["Started_Date__date"] = data["Started_Date"]
            if data.get("Completed_Date"):
                filters["Completed_Date__date"] = data["Completed_Date"]
            if data.get("Created_Date"):
                filters["Created_Date__range"] = data["Created_Date"]
            page = data.get("page", 1)
            return requestget(
                model=ModuleEnrollment,
                serializer=ModuleEnrollmentSerializers,
                data=filters,
                page=page,
                Operator="and")
        except Exception as e:
            return _error(f"Error while filtering ModuleEnrollment: {str(e)}")


class ModuleEnrollmentList(ListAPIView):
    queryset = ModuleEnrollment.objects.all()
    serializer_class = ModuleEnrollmentSerializers

    def get_queryset(self):
        try:
            module = ModuleEnrollment.objects.filter(Q(Is_Deleted=False)).order_by('-id')
            return module
        except Exception as e:
            raise Exception(f"Error while fetching module: {str(e)}")


class ModuleEnrollmentWithoutPagination(APIView):
    def get(self, request, *args, **kwargs):
        try:
            module = ModuleEnrollment.objects.filter(Q(Is_Deleted__exact=False)).order_by('-id')
            serialize = ModuleEnrollmentSerializers(module, many=True)
            output = JSONRenderer().render(serialize.data)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)


# VideoProgress

class VideoProgressCRUD(APIView):
    def post(self, request, *args, **kwargs):
        try:
            data = request.data
            serializer = VideoProgressSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                output = JSONRenderer().render(serializer.data)
                return HttpResponse(output, content_type='application/json', status=status.HTTP_201_CREATED)
            output = JSONRenderer().render(serializer.errors)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, *args, **kwargs):
        try:
            data = request.query_params
            id = data['id']
            module = VideoProgress.objects.get(id=id)
            serializer = VideoProgressSerializers(module)
            output = JSONRenderer().render(serializer.data)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, *args, **kwargs):
        try:
            data = request.data
            id = data['id']
            module = VideoProgress.objects.get(id=id)
            serializer = VideoProgressSerializer(instance=module, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                output = JSONRenderer().render(serializer.data)
                return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
            output = JSONRenderer().render(serializer.errors)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        try:
            data = request.query_params
            id = data['id']
            module = VideoProgress.objects.get(id=id)
            serializer = VideoProgressSerializer(module, {"Is_Deleted": True}, partial=True)
            if serializer.is_valid():
                serializer.save()
            output = JSONRenderer().render(serializer.data)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, *args, **kwargs):
        try:
            data = request.data
            if not data:
                raise TypeError("Request data cannot be empty")
            id = data.get('id')
            module = VideoProgress.objects.get(id=id)
            serializer = VideoProgressSerializer(instance=module, data=data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        except VideoProgress.DoesNotExist as e:
            return Response({"Error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"Error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class VideoProgressSearch(ListAPIView):
    queryset = VideoProgress.objects.filter(Is_Deleted=False)
    serializer_class = VideoProgressSerializers

    def get_queryset(self):
        try:
            search = self.request.GET.get("search")
            queryset = VideoProgress.objects.filter(Is_Deleted=False)
            if search:
                queryset = queryset.filter(
                    Q(VideoProgress_Id__icontains=search) |
                    Q(Video__Video_Title__icontains=search) |
                    Q(Status__icontains=search) |
                    Q(Completion_Method__icontains=search))
            return queryset.order_by("-id")
        except Exception as e:
            raise Exception(f"Error while fetching VideoProgress: {str(e)}")


class VideoProgressFilter(APIView):
    def post(self, request, *args, **kwargs):
        try:
            data = request.data
            filters = {"Is_Deleted": False}
            if data.get("Enrollment"):
                filters["Enrollment_id"] = data["Enrollment"]
            if data.get("Video"):
                filters["Video_id"] = data["Video"]
            if data.get("Status"):
                filters["Status"] = data["Status"]
            if data.get("Completion_Method"):
                filters["Completion_Method"] = data["Completion_Method"]
            if data.get("Completed_Date"):
                filters["Completed_Date__date"] = data["Completed_Date"]
            if data.get("Created_Date"):
                filters["Created_Date__range"] = data["Created_Date"]
            page = data.get("page", 1)
            return requestget(
                model=VideoProgress,
                serializer=VideoProgressSerializers,
                data=filters,
                page=page,
                Operator="and")
        except Exception as e:
            return _error(f"Error while filtering VideoProgress: {str(e)}")


class VideoProgressList(ListAPIView):
    queryset = VideoProgress.objects.all()
    serializer_class = VideoProgressSerializers

    def get_queryset(self):
        try:
            module = VideoProgress.objects.filter(Q(Is_Deleted=False)).order_by('-id')
            return module
        except Exception as e:
            raise Exception(f"Error while fetching module: {str(e)}")


class VideoProgressWithoutPagination(APIView):
    def get(self, request, *args, **kwargs):
        try:
            module = VideoProgress.objects.filter(Q(Is_Deleted__exact=False)).order_by('-id')
            serialize = VideoProgressSerializers(module, many=True)
            output = JSONRenderer().render(serialize.data)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)


# VideoWatchSession

class VideoWatchSessionCRUD(APIView):
    def post(self, request, *args, **kwargs):
        try:
            data = request.data
            serializer = VideoWatchSessionSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                output = JSONRenderer().render(serializer.data)
                return HttpResponse(output, content_type='application/json', status=status.HTTP_201_CREATED)
            output = JSONRenderer().render(serializer.errors)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, *args, **kwargs):
        try:
            data = request.query_params
            id = data['id']
            module = VideoWatchSession.objects.get(id=id)
            serializer = VideoWatchSessionSerializers(module)
            output = JSONRenderer().render(serializer.data)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, *args, **kwargs):
        try:
            data = request.data
            id = data['id']
            module = VideoWatchSession.objects.get(id=id)
            serializer = VideoWatchSessionSerializer(instance=module, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                output = JSONRenderer().render(serializer.data)
                return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
            output = JSONRenderer().render(serializer.errors)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        try:
            data = request.query_params
            id = data['id']
            module = VideoWatchSession.objects.get(id=id)
            serializer = VideoWatchSessionSerializer(module, {"Is_Deleted": True}, partial=True)
            if serializer.is_valid():
                serializer.save()
            output = JSONRenderer().render(serializer.data)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, *args, **kwargs):
        try:
            data = request.data
            if not data:
                raise TypeError("Request data cannot be empty")
            id = data.get('id')
            module = VideoWatchSession.objects.get(id=id)
            serializer = VideoWatchSessionSerializer(instance=module, data=data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        except VideoWatchSession.DoesNotExist as e:
            return Response({"Error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"Error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class VideoWatchSessionSearch(ListAPIView):
    queryset = VideoWatchSession.objects.filter(Is_Deleted=False)
    serializer_class = VideoWatchSessionSerializers

    def get_queryset(self):
        try:
            search = self.request.GET.get("search")
            queryset = VideoWatchSession.objects.filter(Is_Deleted=False)
            if search:
                queryset = queryset.filter(
                    Q(VideoWatchSession_Id__icontains=search) |
                    Q(Progress__VideoProgress_Id__icontains=search) |
                    Q(Status__icontains=search))
            return queryset.order_by("-id")
        except Exception as e:
            raise Exception(f"Error while fetching VideoWatchSession: {str(e)}")


class VideoWatchSessionFilter(APIView):
    def post(self, request, *args, **kwargs):
        try:
            data = request.data
            filters = {"Is_Deleted": False}
            if data.get("Progress"):
                filters["Progress_id"] = data["Progress"]
            if data.get("Status"):
                filters["Status"] = data["Status"]
            if data.get("Started_Date"):
                filters["Started_Date__date"] = data["Started_Date"]
            if data.get("Created_Date"):
                filters["Created_Date__range"] = data["Created_Date"]
            page = data.get("page", 1)
            return requestget(
                model=VideoWatchSession,
                serializer=VideoWatchSessionSerializers,
                data=filters,
                page=page,
                Operator="and")
        except Exception as e:
            return _error(f"Error while filtering VideoWatchSession: {str(e)}")


class VideoWatchSessionList(ListAPIView):
    queryset = VideoWatchSession.objects.all()
    serializer_class = VideoWatchSessionSerializers

    def get_queryset(self):
        try:
            module = VideoWatchSession.objects.filter(Q(Is_Deleted=False)).order_by('-id')
            return module
        except Exception as e:
            raise Exception(f"Error while fetching module: {str(e)}")


class VideoWatchSessionWithoutPagination(APIView):
    def get(self, request, *args, **kwargs):
        try:
            module = VideoWatchSession.objects.filter(Q(Is_Deleted__exact=False)).order_by('-id')
            serialize = VideoWatchSessionSerializers(module, many=True)
            output = JSONRenderer().render(serialize.data)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)


# VideoWatchInterval

class VideoWatchIntervalCRUD(APIView):
    def post(self, request, *args, **kwargs):
        try:
            data = request.data
            serializer = VideoWatchIntervalSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                output = JSONRenderer().render(serializer.data)
                return HttpResponse(output, content_type='application/json', status=status.HTTP_201_CREATED)
            output = JSONRenderer().render(serializer.errors)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, *args, **kwargs):
        try:
            data = request.query_params
            id = data['id']
            module = VideoWatchInterval.objects.get(id=id)
            serializer = VideoWatchIntervalSerializers(module)
            output = JSONRenderer().render(serializer.data)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, *args, **kwargs):
        try:
            data = request.data
            id = data['id']
            module = VideoWatchInterval.objects.get(id=id)
            serializer = VideoWatchIntervalSerializer(instance=module, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                output = JSONRenderer().render(serializer.data)
                return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
            output = JSONRenderer().render(serializer.errors)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        try:
            data = request.query_params
            id = data['id']
            module = VideoWatchInterval.objects.get(id=id)
            serializer = VideoWatchIntervalSerializer(module, {"Is_Deleted": True}, partial=True)
            if serializer.is_valid():
                serializer.save()
            output = JSONRenderer().render(serializer.data)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, *args, **kwargs):
        try:
            data = request.data
            if not data:
                raise TypeError("Request data cannot be empty")
            id = data.get('id')
            module = VideoWatchInterval.objects.get(id=id)
            serializer = VideoWatchIntervalSerializer(instance=module, data=data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        except VideoWatchInterval.DoesNotExist as e:
            return Response({"Error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"Error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class VideoWatchIntervalSearch(ListAPIView):
    queryset = VideoWatchInterval.objects.filter(Is_Deleted=False)
    serializer_class = VideoWatchIntervalSerializers

    def get_queryset(self):
        try:
            search = self.request.GET.get("search")
            queryset = VideoWatchInterval.objects.filter(Is_Deleted=False)
            if search:
                queryset = queryset.filter(
                    Q(VideoWatchInterval_Id__icontains=search) |
                    Q(Session__VideoWatchSession_Id__icontains=search) |
                    Q(Progress__VideoProgress_Id__icontains=search))
            return queryset.order_by("-id")
        except Exception as e:
            raise Exception(f"Error while fetching VideoWatchInterval: {str(e)}")


class VideoWatchIntervalFilter(APIView):
    def post(self, request, *args, **kwargs):
        try:
            data = request.data
            filters = {"Is_Deleted": False}
            if data.get("Session"):
                filters["Session_id"] = data["Session"]
            if data.get("Progress"):
                filters["Progress_id"] = data["Progress"]
            if data.get("Created_Date"):
                filters["Created_Date__range"] = data["Created_Date"]
            page = data.get("page", 1)
            return requestget(
                model=VideoWatchInterval,
                serializer=VideoWatchIntervalSerializers,
                data=filters,
                page=page,
                Operator="and")
        except Exception as e:
            return _error(f"Error while filtering VideoWatchInterval: {str(e)}")


class VideoWatchIntervalList(ListAPIView):
    queryset = VideoWatchInterval.objects.all()
    serializer_class = VideoWatchIntervalSerializers

    def get_queryset(self):
        try:
            module = VideoWatchInterval.objects.filter(Q(Is_Deleted=False)).order_by('-id')
            return module
        except Exception as e:
            raise Exception(f"Error while fetching module: {str(e)}")


class VideoWatchIntervalWithoutPagination(APIView):
    def get(self, request, *args, **kwargs):
        try:
            module = VideoWatchInterval.objects.filter(Q(Is_Deleted__exact=False)).order_by('-id')
            serialize = VideoWatchIntervalSerializers(module, many=True)
            output = JSONRenderer().render(serialize.data)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)


# Certificate

class CertificateCRUD(APIView):
    def post(self, request, *args, **kwargs):
        try:
            data = request.data
            serializer = CertificateSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                output = JSONRenderer().render(serializer.data)
                return HttpResponse(output, content_type='application/json', status=status.HTTP_201_CREATED)
            output = JSONRenderer().render(serializer.errors)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, *args, **kwargs):
        try:
            data = request.query_params
            id = data['id']
            module = Certificate.objects.get(id=id)
            serializer = CertificateSerializers(module)
            output = JSONRenderer().render(serializer.data)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, *args, **kwargs):
        try:
            data = request.data
            id = data['id']
            module = Certificate.objects.get(id=id)
            serializer = CertificateSerializer(instance=module, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                output = JSONRenderer().render(serializer.data)
                return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
            output = JSONRenderer().render(serializer.errors)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        try:
            data = request.query_params
            id = data['id']
            module = Certificate.objects.get(id=id)
            serializer = CertificateSerializer(module, {"Is_Deleted": True}, partial=True)
            if serializer.is_valid():
                serializer.save()
            output = JSONRenderer().render(serializer.data)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, *args, **kwargs):
        try:
            data = request.data
            if not data:
                raise TypeError("Request data cannot be empty")
            id = data.get('id')
            module = Certificate.objects.get(id=id)
            serializer = CertificateSerializer(instance=module, data=data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Certificate.DoesNotExist as e:
            return Response({"Error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"Error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class CertificateSearch(ListAPIView):
    queryset = Certificate.objects.filter(Is_Deleted=False)
    serializer_class = CertificateSerializers

    def get_queryset(self):
        try:
            search = self.request.GET.get("search")
            queryset = Certificate.objects.filter(Is_Deleted=False)
            if search:
                queryset = queryset.filter(
                    Q(Certificate_Id__icontains=search) |
                    Q(Certificate_Number__icontains=search) |
                    Q(Product_Name__icontains=search) |
                    Q(Status__icontains=search))
            return queryset.order_by("-id")
        except Exception as e:
            raise Exception(f"Error while fetching Certificate: {str(e)}")


class CertificateFilter(APIView):
    def post(self, request, *args, **kwargs):
        try:
            data = request.data
            filters = {"Is_Deleted": False}
            if data.get("Partner"):
                filters["Partner_id"] = data["Partner"]
            if data.get("Product"):
                filters["Product_id"] = data["Product"]
            if data.get("Product_Name"):
                filters["Product_Name__icontains"] = data["Product_Name"]
            if data.get("Status"):
                filters["Status"] = data["Status"]
            if data.get("Issued_Date"):
                filters["Issued_Date__date"] = data["Issued_Date"]
            if data.get("Expiry_Date"):
                filters["Expiry_Date__date"] = data["Expiry_Date"]
            if data.get("Created_Date"):
                filters["Created_Date__range"] = data["Created_Date"]
            page = data.get("page", 1)
            return requestget(
                model=Certificate,
                serializer=CertificateSerializers,
                data=filters,
                page=page,
                Operator="and")
        except Exception as e:
            return _error(f"Error while filtering Certificate: {str(e)}")


class CertificateList(ListAPIView):
    queryset = Certificate.objects.all()
    serializer_class = CertificateSerializers

    def get_queryset(self):
        try:
            module = Certificate.objects.filter(Q(Is_Deleted=False)).order_by('-id')
            return module
        except Exception as e:
            raise Exception(f"Error while fetching module: {str(e)}")


class CertificateWithoutPagination(APIView):
    def get(self, request, *args, **kwargs):
        try:
            module = Certificate.objects.filter(Q(Is_Deleted__exact=False)).order_by('-id')
            serialize = CertificateSerializers(module, many=True)
            output = JSONRenderer().render(serialize.data)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)



# done by shajitha
class PartnerCertificateList(APIView):

    # GET - Certificate list of a partner
    def get(self, request, *args, **kwargs):
        try:
            data = request.query_params

            module = Certificate.objects.filter(
                Partner_id=data['partner_id'],
                Is_Deleted=False
            ).order_by('-id')

            serialize = CertificateSerializer(module, many=True)
            output = JSONRenderer().render(serialize.data)

            return HttpResponse(
                output,
                content_type="application/json",
                status=status.HTTP_200_OK
            )

        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(
                output,
                content_type="application/json",
                status=status.HTTP_400_BAD_REQUEST
            )

# done by shajitha
class PartnerTeamMemberCertificateList(APIView):

    # GET - Certificate list of a partner team member
    def get(self, request, *args, **kwargs):
        try:
            data = request.query_params

            module = Certificate.objects.filter(
                PartnerTeamMember_id=data['team_member_id'],
                Is_Deleted=False
            ).order_by('-id')

            serialize = CertificateSerializer(module, many=True)
            output = JSONRenderer().render(serialize.data)

            return HttpResponse(
                output,
                content_type="application/json",
                status=status.HTTP_200_OK
            )

        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(
                output,
                content_type="application/json",
                status=status.HTTP_400_BAD_REQUEST
            )



# AcademyNotification

class AcademyNotificationCRUD(APIView):
    def post(self, request, *args, **kwargs):
        try:
            data = request.data
            serializer = AcademyNotificationSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                output = JSONRenderer().render(serializer.data)
                return HttpResponse(output, content_type='application/json', status=status.HTTP_201_CREATED)
            output = JSONRenderer().render(serializer.errors)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, *args, **kwargs):
        try:
            data = request.query_params
            id = data['id']
            module = AcademyNotification.objects.get(id=id)
            serializer = AcademyNotificationSerializers(module)
            output = JSONRenderer().render(serializer.data)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, *args, **kwargs):
        try:
            data = request.data
            id = data['id']
            module = AcademyNotification.objects.get(id=id)
            serializer = AcademyNotificationSerializer(instance=module, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                output = JSONRenderer().render(serializer.data)
                return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
            output = JSONRenderer().render(serializer.errors)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        try:
            data = request.query_params
            id = data['id']
            module = AcademyNotification.objects.get(id=id)
            serializer = AcademyNotificationSerializer(module, {"Is_Deleted": True}, partial=True)
            if serializer.is_valid():
                serializer.save()
            output = JSONRenderer().render(serializer.data)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, *args, **kwargs):
        try:
            data = request.data
            if not data:
                raise TypeError("Request data cannot be empty")
            id = data.get('id')
            module = AcademyNotification.objects.get(id=id)
            serializer = AcademyNotificationSerializer(instance=module, data=data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        except AcademyNotification.DoesNotExist as e:
            return Response({"Error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"Error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class AcademyNotificationSearch(ListAPIView):
    queryset = AcademyNotification.objects.filter(Is_Deleted=False)
    serializer_class = AcademyNotificationSerializers

    def get_queryset(self):
        try:
            search = self.request.GET.get("search")
            queryset = AcademyNotification.objects.filter(Is_Deleted=False)
            if search:
                queryset = queryset.filter(
                    Q(AcademyNotification_Id__icontains=search) |
                    Q(Title__icontains=search) |
                    Q(Message__icontains=search) |
                    Q(Notification_Type__icontains=search))
            return queryset.order_by("-id")
        except Exception as e:
            raise Exception(f"Error while fetching AcademyNotification: {str(e)}")


class AcademyNotificationFilter(APIView):
    def post(self, request, *args, **kwargs):
        try:
            data = request.data
            filters = {"Is_Deleted": False}
            if data.get("Recipient"):
                filters["Recipient_id"] = data["Recipient"]
            if data.get("Partner"):
                filters["Partner_id"] = data["Partner"]
            if data.get("Notification_Type"):
                filters["Notification_Type"] = data["Notification_Type"]
            if data.get("Is_Read") is not None and data.get("Is_Read") != "":
                filters["Is_Read"] = data["Is_Read"]
            if data.get("Created_Date"):
                filters["Created_Date__range"] = data["Created_Date"]
            page = data.get("page", 1)
            return requestget(
                model=AcademyNotification,
                serializer=AcademyNotificationSerializers,
                data=filters,
                page=page,
                Operator="and")
        except Exception as e:
            return _error(f"Error while filtering AcademyNotification: {str(e)}")


class AcademyNotificationList(ListAPIView):
    queryset = AcademyNotification.objects.all()
    serializer_class = AcademyNotificationSerializers

    def get_queryset(self):
        try:
            module = AcademyNotification.objects.filter(Q(Is_Deleted=False)).order_by('-id')
            return module
        except Exception as e:
            raise Exception(f"Error while fetching module: {str(e)}")


class AcademyNotificationWithoutPagination(APIView):
    def get(self, request, *args, **kwargs):
        try:
            module = AcademyNotification.objects.filter(Q(Is_Deleted__exact=False)).order_by('-id')
            serialize = AcademyNotificationSerializers(module, many=True)
            output = JSONRenderer().render(serialize.data)
            return HttpResponse(output, content_type='application/json', status=status.HTTP_200_OK)
        except Exception as e:
            output = JSONRenderer().render({"Error": str(e)})
            return HttpResponse(output, content_type='application/json', status=status.HTTP_400_BAD_REQUEST)



# ===========================================================================
# PARTNER PORTAL - My Training
# Paste this whole block at the BOTTOM of your academy views.py
# (it uses _reply, _error, _user, _truthy, _media_url already defined at the top)
#
#   GET  PartnerTrainingProducts/?Partner=1                        -> left menu: products + %
#   GET  ListOfProductWiseVideos/?Partner=1&Product_Name=...       -> modules + videos + lock state (your existing API)
#   POST PartnerVideoPlay/         {Partner, Video, Position?}      -> started / resumed (session row)
#   POST PartnerVideoStop/         {Partner, Session, Position, Reason}  -> paused / stopped / refreshed ...
#   POST PartnerVideoComplete/     {Partner, Video, Session?, Position?} -> completed + Next_Video
#   GET  PartnerVideoActivity/     ?Partner=&Video=                 -> every start / stop row
#
# Rules
#   - Videos of a product play in order: module Sequence_No, then video Sequence_No.
#     Next video / next module opens only after the current one is Completed.
#   - Completed = Watch_Percentage >= Min_Watch_Percentage.
#     Watch_Percentage comes from VideoWatchInterval (real seconds watched, overlaps merged),
#     so skipping forward does not count.
#   - Resume: Last_Position_Seconds (where the partner stopped) is saved on every Stop and returned by PartnerVideoPlay.
#     Going back to rewatch is allowed; moving forward is allowed only up to Furthest_Watched_Seconds.
#   - A completed video can never be opened again (rewatch is blocked for every video).
#   - All videos of a product completed -> Certificate row = Eligible.
# ===========================================================================
import hashlib
import secrets
from datetime import timedelta

from django.utils import timezone
from partner.models import Partner

HEARTBEAT_MAX_SPEED = 1.0          # watched seconds may grow at most 1x real time (no fast-forward, no speed-up)
HEARTBEAT_GRACE_SECONDS = 5        # network delay allowance
SESSION_EXPIRE_MINUTES = 30        # no heartbeat for 30 min -> session expired, reopen the video
RESUME_RESET_SECONDS = 5           # stopped in the last 5 sec -> resume from 0


def _hash(token):
    return hashlib.sha256(token.encode()).hexdigest()


def _ip(request):
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    return (forwarded.split(",")[0].strip() if forwarded else request.META.get("REMOTE_ADDR")) or None


def _num(value):
    return float(value) if value is not None else 0


def _get_team_member(request):
    """PartnerTeamMember from 'PartnerTeamMember', 'PartnerTeamMember_Id', or 'PartnerTeamUser_Id' in body / query.
    Fallback: PartnerTeamMember whose Email = logged-in Django user's email."""
    member_id = (
        request.data.get("PartnerTeamMember")
        or request.data.get("PartnerTeamMember_Id")
        or request.data.get("PartnerTeamUser_Id")
        or request.data.get("partnerTeamUser_id")
        or request.data.get("team_member_id")
        or request.query_params.get("PartnerTeamMember")
        or request.query_params.get("PartnerTeamMember_Id")
        or request.query_params.get("PartnerTeamUser_Id")
        or request.query_params.get("partnerTeamUser_id")
        or request.query_params.get("team_member_id")
    )
    if member_id:
        import re
        clean_id = re.sub(r'\D', '', str(member_id))
        if clean_id:
            member = PartnerTeamMember.objects.filter(id=clean_id, Is_Deleted=False).first()
            if member:
                return member
        member = PartnerTeamMember.objects.filter(
            Q(PartnerTeamMember_id=member_id) | Q(User_Id=member_id) if hasattr(PartnerTeamMember, 'User_Id') else Q(PartnerTeamMember_id=member_id),
            Is_Deleted=False
        ).first()
        if member:
            return member
    email = getattr(request.user, "email", None)
    if email:
        return PartnerTeamMember.objects.filter(Email__iexact=email, Is_Deleted=False).first()
    return None


def _get_partner(request):
    """Partner from 'Partner' (id) in body / query (partner portal sends the id it got from PartnerLogin).
    Fallback: partner whose Primary_Email = logged-in Django user's email, or team member's partner."""
    partner_id = request.data.get("Partner") or request.query_params.get("Partner")
    partners = Partner.objects.filter(Is_Deleted=False)
    if partner_id:
        import re
        clean_id = re.sub(r'\D', '', str(partner_id))
        p = partners.filter(id=clean_id).first() if clean_id else None
        if not p:
            p = partners.filter(Partner_Id=partner_id).first()
        if p:
            return p
    team_member = _get_team_member(request)
    if team_member and team_member.Partner_Id:
        return team_member.Partner_Id
    email = getattr(request.user, "email", None)
    if email:
        tm = PartnerTeamMember.objects.filter(Email__iexact=email, Is_Deleted=False).first()
        if tm and tm.Partner_Id:
            return tm.Partner_Id
        return partners.filter(Primary_Email__iexact=email).first()
    return None


def _partner_products(partner):
    """Products the partner signed up for (PartnerApplication.target_products)."""
    application = partner.PartnerApplication_Id
    products = application.target_products if application and application.target_products else []
    return [p for p in products if p]


def _product_videos(product_name):
    """All playable videos of a product in learning order."""
    return list(TrainingVideo.objects.filter(
        Module__Product_Name=product_name, Module__Status="Published", Module__Is_Deleted=False,
        Status="Published", Upload_Status="Ready", Is_Deleted=False,
    ).select_related("Module").order_by("Module__Sequence_No", "Module__id", "Sequence_No", "id"))


def _progress_map(partner, videos, team_member=None):
    if team_member:
        rows = VideoProgress.objects.filter(Enrollment__PartnerTeamMember=team_member, Video__in=videos, Is_Deleted=False)
    else:
        rows = VideoProgress.objects.filter(Enrollment__Partner=partner, Enrollment__PartnerTeamMember__isnull=True, Video__in=videos, Is_Deleted=False)
    return {row.Video_id: row for row in rows}


def _video_states(videos, progress):
    """[(video, state)] in order. First not-completed video is open, everything after it is Locked."""
    states, blocked = [], False
    for video in videos:
        row = progress.get(video.id)
        if row and row.Status == "Completed":
            states.append((video, "Completed"))
        elif blocked:
            states.append((video, "Locked"))
        else:
            states.append((video, "In Progress" if row and row.Watched_Seconds > 0 else "Available"))
            blocked = True
    return states


def _product_summary(partner, product_name, team_member=None):
    videos = _product_videos(product_name)
    progress = _progress_map(partner, videos, team_member=team_member)
    states = _video_states(videos, progress)
    total = len(states)
    done = sum(1 for _, state in states if state == "Completed")
    current = next((video for video, state in states if state in ("Available", "In Progress")), None)
    return progress, states, total, done, current


def _video_brief(video):
    if not video:
        return None
    return {
        "id": video.id, "Video_Id": video.Video_Id, "Video_Title": video.Video_Title,
        "Module": video.Module_id, "Module_Name": video.Module.Module_Name if video.Module else None,
        "Sequence_No": video.Sequence_No, "Duration_Seconds": video.Duration_Seconds,
        "Min_Watch_Percentage": _num(video.Min_Watch_Percentage), "Allow_Rewatch": video.Allow_Rewatch}


def _play_url(request, video):
    return video.Video_URL if video.Video_Source == "URL" else _media_url(request, video.Video_Key)


def _enrollment(partner, module, user, team_member=None):
    if team_member:
        enrollment = ModuleEnrollment.objects.filter(PartnerTeamMember=team_member, Module=module, Is_Deleted=False).first()
        if not enrollment:
            now = timezone.now()
            enrollment = ModuleEnrollment.objects.create(
                Partner=partner, PartnerTeamMember=team_member, Module=module, Status="In Progress", Started_Date=now,
                Last_Accessed_Date=now, Created_By=user, Updated_By=user)
        return enrollment
    else:
        # Auth Login (Partner Admin alone - strictly PartnerTeamMember__isnull=True)
        enrollment = ModuleEnrollment.objects.filter(Partner=partner, PartnerTeamMember__isnull=True, Module=module, Is_Deleted=False).first()
        if not enrollment:
            now = timezone.now()
            enrollment = ModuleEnrollment.objects.create(
                Partner=partner, Module=module, Status="In Progress", Started_Date=now,
                Last_Accessed_Date=now, Created_By=user, Updated_By=user)
        return enrollment


def _refresh_enrollment(enrollment, user):
    videos = TrainingVideo.objects.filter(Module=enrollment.Module, Status="Published",
                                          Upload_Status="Ready", Is_Deleted=False)
    total = videos.count()
    done = VideoProgress.objects.filter(Enrollment=enrollment, Video__in=videos,
                                        Status="Completed", Is_Deleted=False).count()
    now = timezone.now()
    enrollment.Completion_Percentage = round(done * 100 / total, 2) if total else 0
    enrollment.Last_Accessed_Date = now
    if total and done >= total:
        enrollment.Status = "Completed"
        enrollment.Completed_Date = enrollment.Completed_Date or now
    else:
        enrollment.Status = "In Progress"
    enrollment.Updated_By = user
    enrollment.save()


def _covered_seconds(progress):
    """Real seconds watched: merge overlapping intervals (0-300 watched twice = 300)."""
    rows = progress.intervals.filter(Is_Deleted=False).order_by("Start_Second").values_list("Start_Second", "End_Second")
    total, cur_start, cur_end = 0, None, None
    for start, end in rows:
        if cur_end is None or start > cur_end:
            if cur_end is not None:
                total += cur_end - cur_start
            cur_start, cur_end = start, end
        else:
            cur_end = max(cur_end, end)
    if cur_end is not None:
        total += cur_end - cur_start
    return total


def _complete(progress, method, user):
    """Marks one video Completed. Returns True only the first time."""
    if progress.Status == "Completed":
        return False
    progress.Status = "Completed"
    progress.Completed_Date = timezone.now()
    progress.Completion_Method = method
    progress.Updated_By = user
    progress.save()
    _refresh_enrollment(progress.Enrollment, user)
    return True


def _certificate_info(partner, product, total, done, team_member=None):
    """Certificate state of one product, worked out live (no row is created here).
    Locked   = videos still pending
    Eligible = all videos completed, "Issue Certificate" button not clicked yet
    Issued   = row created by PartnerCertificateGenerate  (Revoked / Expired come from the row too)"""
    if team_member:
        certificate = Certificate.objects.filter(PartnerTeamMember=team_member, Product_Name=product[:50], Is_Deleted=False).first()
    else:
        certificate = Certificate.objects.filter(Partner=partner, PartnerTeamMember__isnull=True, Product_Name=product[:50], Is_Deleted=False).first()
    if certificate and certificate.Status in ("Issued", "Revoked", "Expired"):
        state = certificate.Status
    elif total and done >= total:
        state = "Eligible"
    else:
        state = "Locked"
    return {
        "Certificate_Status": state,
        "Can_Issue_Certificate": state == "Eligible",          # show "Issue Certificate" button
        "Can_View_Certificate": state == "Issued",             # show "View Certificate" button
        "Certificate": certificate.id if certificate and state == "Issued" else None,
        "Certificate_Number": certificate.Certificate_Number if certificate and state == "Issued" else None}


def _after_complete(request, partner, video, notify, team_member=None):
    """Finds the next video and sends notifications. The certificate row is NOT created here:
    it is created only when the partner clicks "Issue Certificate" (PartnerCertificateGenerate)."""
    user = _user(request)
    product = video.Module.Product_Name
    _, _, total, done, next_video = _product_summary(partner, product, team_member=team_member)

    if notify and next_video:
        AcademyNotification.objects.create(
            Partner=partner, Recipient=user, Title="Next video unlocked",
            Message=f"{next_video.Video_Title} is now available in {product}.",
            Notification_Type="Video Unlocked", Created_By=user, Updated_By=user)

    product_completed = bool(total) and done >= total
    if product_completed and notify:
        AcademyNotification.objects.create(
            Partner=partner, Recipient=user, Title="Certificate ready to claim",
            Message=f"You completed all videos of {product}. Click 'Issue Certificate' to get your certificate.",
            Notification_Type="Certificate", Created_By=user, Updated_By=user)

    output = {
        "Next_Video": _video_brief(next_video),
        "Next_Is_New_Module": bool(next_video and next_video.Module_id != video.Module_id),
        "Product_Total_Videos": total, "Product_Completed_Videos": done,
        "Product_Progress_Percentage": round(done * 100 / total) if total else 0,
        "Product_Completed": product_completed}
    output.update(_certificate_info(partner, product, total, done, team_member=team_member))
    return output


def _open_video(partner, video_id):
    """Returns (video, error_message, http_code)."""
    video = TrainingVideo.objects.filter(id=video_id, Status="Published", Upload_Status="Ready",
                                         Is_Deleted=False).select_related("Module").first()
    if not video or not video.Module:
        return None, "Video not found", status.HTTP_404_NOT_FOUND
    if video.Module.Product_Name not in _partner_products(partner):
        return None, "This product is not assigned to you", status.HTTP_403_FORBIDDEN
    return video, None, None


# ---------------------------------------------------------------------------
# 1. Left menu: products with progress
#    GET /PartnerTrainingProducts/?Partner=1
# ---------------------------------------------------------------------------
class PartnerTrainingProducts(APIView):
    def get(self, request, *args, **kwargs):
        try:
            partner = _get_partner(request)
            if not partner:
                return _error("Partner not found", status.HTTP_404_NOT_FOUND)
            team_member = _get_team_member(request)
            output, all_total, all_done = [], 0, 0
            for product in _partner_products(partner):
                _, _, total, done, current = _product_summary(partner, product, team_member=team_member)
                all_total += total
                all_done += done
                if total and done >= total:
                    product_status = "Completed"
                elif done:
                    product_status = "In Progress"
                else:
                    product_status = "Not Started"
                row = {
                    "Product_Name": product,
                    "Total_Videos": total, "Completed_Videos": done,
                    "Progress_Percentage": round(done * 100 / total) if total else 0,
                    "Status": product_status,
                    "Current_Video": _video_brief(current)}
                row.update(_certificate_info(partner, product, total, done, team_member=team_member))
                output.append(row)
            return _reply({
                "Partner": partner.id, "Partner_Name": partner.Trade_Name or partner.Legal_Name,
                "Overall_Percentage": round(all_done * 100 / all_total) if all_total else 0,
                "Products": output})
        except Exception as e:
            return _error(str(e))


# ===========================================================================
# VIDEO TRACKING  (event based - one API call per real action, every call is saved in DB)
#
#   POST PartnerVideoPlay/       {Partner, Video}                   play / resume  -> new VideoWatchSession "Playing"
#   POST PartnerVideoStop/       {Partner, Session, Position, Reason}  pause / stop / refresh / close
#
#   Strict rules (enforced here, not in the browser)
#     - a Completed video can never be played again
#     - Play resumes from the second where the partner last stopped; going back to rewatch is allowed
#     - Stop only accepts what was really watched: skipping ahead is not saved
#   POST PartnerVideoComplete/   {Partner, Video, Session?, Position?} video ended  -> Completed + next video
#   GET  PartnerVideoActivity/?Partner=1&Video=5                    every start / stop row (for analysis)
#
#   Tables
#     ModuleEnrollment   one per partner per module   (created on first Play in that module)
#     VideoProgress      one per partner per video    (status, watch %, last stop second = resume point)
#     VideoWatchSession  one per Play -> Stop         (Status: Playing / Paused / Stopped /
#                                                       Refreshed / Closed / Completed / Interrupted)
#     VideoWatchInterval ONE per partner per video   (0 -> furthest second really watched, grows on every Stop)
# ===========================================================================
STOP_REASONS = {
    "pause": "Paused", "stop": "Stopped",
    "refresh": "Refreshed", "close": "Closed", "ended": "Completed"}


def _mmss(seconds):
    seconds = int(seconds or 0)
    return f"{seconds // 60}:{seconds % 60:02d}"


def _int(value, default=0):
    try:
        return max(0, int(float(value)))
    except (TypeError, ValueError):
        return default


def _recalculate(progress, position, user, now):
    """Watch % from the watched range + resume point.
    The resume point = the second where the partner stopped (it can go BACK when they rewatch an earlier part).
    The watch % only grows: it comes from the furthest second really watched."""
    video = progress.Video
    duration = video.Duration_Seconds or 0
    watched = _covered_seconds(progress)
    progress.Watched_Seconds = watched
    progress.Watch_Percentage = round(min(100, watched * 100 / duration), 2) if duration else 0
    position = min(position, duration) if duration else position
    progress.Last_Position_Seconds = position
    progress.Last_Watched_Date = now
    progress.Updated_By = user
    progress.save()


def _progress_interval(progress, session, user):
    """The ONE VideoWatchInterval row of this partner for this video: 0 -> furthest second really watched.
    (Moving forward is only allowed up to this second, so the watched part is always one continuous range.)"""
    interval = progress.intervals.filter(Is_Deleted=False).order_by("id").first()
    if not interval:
        interval = VideoWatchInterval.objects.create(
            Session=session, Progress=progress, Start_Second=0,
            End_Second=progress.Last_Position_Seconds or 0, Created_By=user, Updated_By=user)
    return interval


def _session_start(session):
    """Second where this session started playing (saved in Device_Info by PartnerVideoPlay)."""
    info = session.Device_Info if isinstance(session.Device_Info, dict) else {}
    start = info.get("Start_Second")
    if start is None:                                    # sessions created before this change
        old = session.session_intervals.filter(Is_Deleted=False).order_by("id").first()
        start = old.Start_Second if old else session.Last_Position_Seconds
    return int(start or 0)


def _close_session(session, position, status_label, user, now):
    """Ends a Playing session.
    - Going BACK is allowed (rewatching an earlier part of a video that is not completed):
      the partner resumes next time from the second where they stopped, even if it is earlier.
    - Going FORWARD past the furthest second really watched is cut to the real time that passed
      (1x speed + 5 sec network delay), so skipping ahead never counts.
    - The watch % only grows: the interval keeps the furthest second really watched."""
    progress = session.Progress
    duration = progress.Video.Duration_Seconds or 0
    if duration:
        position = min(position, duration)
    start = _session_start(session)
    interval = _progress_interval(progress, session, user)     # same row every time
    furthest_before = interval.End_Second or 0

    # the furthest second this session can honestly reach
    elapsed = (now - (session.Started_Date or now)).total_seconds()
    # (new seconds beyond the furthest point can never be more than the real time this session lasted)
    reachable = max(furthest_before, start) + int(elapsed * HEARTBEAT_MAX_SPEED) + HEARTBEAT_GRACE_SECONDS
    end = min(position, reachable)                              # validated stop second (resume point)

    interval.End_Second = max(furthest_before, end)            # watched range only grows
    interval.Session = session                                  # last session that added to it
    interval.Updated_By = user
    interval.save()

    session.Status = status_label
    session.Ended_Date = now
    session.Last_Heartbeat_Date = now
    session.Last_Position_Seconds = end          # validated stop second (not the raw player position)
    session.Updated_By = user
    session.save()
    _recalculate(progress, end, user, now)
    return max(0, interval.End_Second - furthest_before)        # new seconds added to the watched range


def _session_for(partner, session_id):
    return VideoWatchSession.objects.select_related(
        "Progress__Video__Module", "Progress__Enrollment").filter(
        id=session_id, Progress__Enrollment__Partner=partner, Is_Deleted=False).first()


# ---------------------------------------------------------------------------
# 3. PLAY  (first play, resume after coming back, or play again after a pause)
#    POST /PartnerVideoPlay/   {"Partner": 1, "Video": 5}
#    Always starts from the saved second. Completed videos cannot be played again.
# ---------------------------------------------------------------------------
class PartnerVideoPlay(APIView):
    def post(self, request, *args, **kwargs):
        try:
            partner = _get_partner(request)
            if not partner:
                return _error("Partner not found", status.HTTP_404_NOT_FOUND)
            video, err, code = _open_video(partner, request.data.get("Video"))
            if err:
                return _error(err, code)

            team_member = _get_team_member(request)
            progress_map, states, total, done, current = _product_summary(partner, video.Module.Product_Name, team_member=team_member)
            state = next((s for v, s in states if v.id == video.id), None)
            if state == "Locked":
                return _error("Complete the previous videos first", status.HTTP_403_FORBIDDEN)
            if state == "Completed":
                return _error("You have already completed this video. Rewatching is not allowed.", status.HTTP_403_FORBIDDEN)

            user = _user(request)
            now = timezone.now()
            duration = video.Duration_Seconds or 0
            with transaction.atomic():
                enrollment = _enrollment(partner, video.Module, user, team_member=team_member)
                progress = progress_map.get(video.id)
                first_time = progress is None
                if first_time:
                    progress = VideoProgress.objects.create(
                        Enrollment=enrollment, Video=video, Status="In Progress",
                        Unlocked_Date=now, First_Started_Date=now, Last_Watched_Date=now,
                        Created_By=user, Updated_By=user)
                elif progress.Status != "Completed":
                    progress.Status = "In Progress"
                    progress.Last_Watched_Date = now
                    progress.Updated_By = user
                    progress.save()

                # a session still "Playing" = page was refreshed / closed before Stop reached us
                progress.sessions.filter(Status="Playing").update(Status="Interrupted", Ended_Date=now)

                position = progress.Last_Position_Seconds or 0            # always the saved second
                if duration:
                    position = min(position, duration)

                # one session per Play -> Stop (activity log: when it started / stopped and from which second)
                session = VideoWatchSession.objects.create(
                    Progress=progress, Status="Playing", Last_Heartbeat_Date=now, Last_Position_Seconds=position,
                    Device_Info={"User_Agent": request.META.get("HTTP_USER_AGENT", "")[:500],
                                 "Start_Second": position},
                    IP_Address=_ip(request), Created_By=user, Updated_By=user)
                # one interval row per video (created on first play, extended on every stop)
                interval = _progress_interval(progress, session, user)
                interval.Session = session
                interval.save(update_fields=["Session", "Updated_Date"])
                enrollment.Last_Accessed_Date = now
                enrollment.save()

            index = next(i for i, (v, _) in enumerate(states) if v.id == video.id)
            next_video = states[index + 1][0] if index + 1 < len(states) else None
            module_videos = [v for v, _ in states if v.Module_id == video.Module_id]
            return _reply({
                "Event": "Started",
                "Message": ("Video started" if first_time and position == 0 else f"Video resumed at {_mmss(position)}"),
                "Session": session.id,
                "Session_Id": session.VideoWatchSession_Id,
                **_video_brief(video),
                "Description": video.Description,
                "Product_Name": video.Module.Product_Name,
                "Position_In_Module": module_videos.index(video) + 1,
                "Module_Total_Videos": len(module_videos),
                "Video_Source": video.Video_Source,
                "Play_URL": _play_url(request, video),
                "Resume_At_Seconds": position,
                "Furthest_Watched_Seconds": progress.Watched_Seconds,     # player may not move forward past this
                "Status": progress.Status,
                "Watched_Seconds": progress.Watched_Seconds,
                "Watch_Percentage": _num(progress.Watch_Percentage),
                "Can_Complete": progress.Status == "Completed" or _num(progress.Watch_Percentage) >= _num(video.Min_Watch_Percentage),
                "Up_Next": _video_brief(next_video)}, status.HTTP_201_CREATED)
        except Exception as e:
            return _error(str(e))


# ---------------------------------------------------------------------------
# 4. STOP  (pause / stop / refresh / close)
#    POST /PartnerVideoStop/   {"Partner": 1, "Session": 12, "Position": 125, "Reason": "pause"}
#    Reason: pause | stop | refresh | close
#    Position is checked: only seconds really watched since Play are saved.
# ---------------------------------------------------------------------------
class PartnerVideoStop(APIView):
    parser_classes = [JSONParser, FormParser, MultiPartParser]

    def post(self, request, *args, **kwargs):
        try:
            partner = _get_partner(request)
            if not partner:
                return _error("Partner not found", status.HTTP_404_NOT_FOUND)
            reason = (request.data.get("Reason") or "pause").strip().lower()
            if reason not in STOP_REASONS or reason == "ended":
                return _error("Reason must be pause, stop, refresh or close")
            session = _session_for(partner, request.data.get("Session"))
            if not session:
                return _error("Session not found", status.HTTP_404_NOT_FOUND)
            progress = session.Progress
            video = progress.Video

            if session.Status != "Playing":                      # already recorded (double click / repeated event)
                return _reply({
                    "Event": session.Status, "Message": f"Already recorded as {session.Status} at {_mmss(session.Last_Position_Seconds)}",
                    "Session": session.id, "Stopped_At_Seconds": session.Last_Position_Seconds,
                    "Watch_Percentage": _num(progress.Watch_Percentage), "Status": progress.Status,
                    "Can_Complete": progress.Status == "Completed" or _num(progress.Watch_Percentage) >= _num(video.Min_Watch_Percentage)})

            user = _user(request)
            now = timezone.now()
            position = _int(request.data.get("Position"), session.Last_Position_Seconds)
            label = STOP_REASONS[reason]
            with transaction.atomic():
                counted = _close_session(session, position, label, user, now)

            message = f"Video {label.lower()} at {_mmss(session.Last_Position_Seconds)}"
            if position > session.Last_Position_Seconds:
                message += ". Skipped part was not saved; you will resume from here"
            return _reply({
                "Event": label,
                "Message": message,
                "Session": session.id,
                "Session_Id": session.VideoWatchSession_Id,
                "Stopped_At_Seconds": session.Last_Position_Seconds,
                "Furthest_Watched_Seconds": progress.Watched_Seconds,
                "Counted_Seconds": counted,
                "Watched_Seconds": progress.Watched_Seconds,
                "Watch_Percentage": _num(progress.Watch_Percentage),
                "Min_Watch_Percentage": _num(video.Min_Watch_Percentage),
                "Status": progress.Status,
                "Can_Complete": progress.Status == "Completed" or _num(progress.Watch_Percentage) >= _num(video.Min_Watch_Percentage)})
        except Exception as e:
            return _error(str(e))


# ---------------------------------------------------------------------------
# 5. COMPLETE  (video ended, or "Complete & Next Video" button)
#    POST /PartnerVideoComplete/   {"Partner": 1, "Video": 5, "Session": 12, "Position": 240}
#    Session / Position: send them when the video just ended while playing (closes that session).
# # ---------------------------------------------------------------------------
# class PartnerVideoComplete(APIView):
#     def post(self, request, *args, **kwargs):
#         try:
#             partner = _get_partner(request)
#             if not partner:
#                 return _error("Partner not found", status.HTTP_404_NOT_FOUND)
#             video, err, code = _open_video(partner, request.data.get("Video"))
#             if err:
#                 return _error(err, code)
#             progress = VideoProgress.objects.filter(
#                 Enrollment__Partner=partner, Video=video, Is_Deleted=False).select_related("Enrollment", "Video").first()
#             if not progress:
#                 return _error("Start the video first")

#             user = _user(request)
#             now = timezone.now()
#             just_completed = False
#             with transaction.atomic():
#                 session = _session_for(partner, request.data.get("Session")) if request.data.get("Session") else None
#                 if session and session.Progress_id == progress.id and session.Status == "Playing":
#                     position = _int(request.data.get("Position"), video.Duration_Seconds or session.Last_Position_Seconds)
#                     _close_session(session, position, "Completed", user, now)
#                     progress.refresh_from_db()

#                 if progress.Status != "Completed":
#                     if _num(progress.Watch_Percentage) < _num(video.Min_Watch_Percentage):
#                         return _error(
#                             f"Watch at least {_num(video.Min_Watch_Percentage):g}% of this video to complete it. "
#                             f"You have watched {_num(progress.Watch_Percentage):g}%.")
#                     just_completed = _complete(progress, "Video", user)
#                 progress.sessions.filter(Status="Playing").update(Status="Completed", Ended_Date=now)

#             output = {"Event": "Completed", "id": video.id, "Video_Title": video.Video_Title,
#                       "Status": "Completed", "Just_Completed": just_completed,
#                       "Watch_Percentage": _num(progress.Watch_Percentage)}
#             output.update(_after_complete(request, partner, video, notify=just_completed))
#             if output["Next_Video"]:
#                 output["Message"] = f"Video completed. Next: {output['Next_Video']['Video_Title']}"
#             elif output["Product_Completed"]:
#                 output["Message"] = f"All videos of {video.Module.Product_Name} completed. You can get your certificate."
#             else:
#                 output["Message"] = "Video completed."
#             return _reply(output)
#         except Exception as e:
#             return _error(str(e))


# ---------------------------------------------------------------------------
# 5. COMPLETE  (frontend decides the video is completed)
#    POST /PartnerVideoComplete/   {"Partner": 1, "Video": 5, "Session": 12, "Position": 240}
#    No percentage check here: whatever the frontend sends as completed is saved as Completed.
#    Session / Position are optional (the open session is closed as "Completed").
# ---------------------------------------------------------------------------
class PartnerVideoComplete(APIView):
    def post(self, request, *args, **kwargs):
        try:
            partner = _get_partner(request)
            if not partner:
                return _error("Partner not found", status.HTTP_404_NOT_FOUND)
            video, err, code = _open_video(partner, request.data.get("Video"))
            if err:
                return _error(err, code)

            team_member = _get_team_member(request)
            user = _user(request)
            now = timezone.now()
            just_completed = False
            with transaction.atomic():
                progress_qs = VideoProgress.objects.select_for_update().filter(Video=video, Is_Deleted=False)
                if team_member:
                    progress_qs = progress_qs.filter(Enrollment__PartnerTeamMember=team_member)
                else:
                    progress_qs = progress_qs.filter(Enrollment__Partner=partner, Enrollment__PartnerTeamMember__isnull=True)
                progress = progress_qs.select_related("Enrollment", "Video").first()
                if not progress:
                    return _error("Start the video first")

                position = _int(request.data.get("Position"), progress.Last_Position_Seconds or 0)

                # close the open session(s) of this video as Completed
                progress.sessions.filter(Status="Playing").update(
                    Status="Completed", Ended_Date=now, Last_Heartbeat_Date=now,
                    Last_Position_Seconds=position, Updated_By=user)

                # save as Completed (only the first time)
                if progress.Status != "Completed":
                    progress.Last_Position_Seconds = position
                    progress.Last_Watched_Date = now
                    progress.save()
                    just_completed = _complete(progress, "Video", user)

            output = {"Event": "Completed", "id": video.id, "Video_Title": video.Video_Title,
                      "Status": "Completed", "Just_Completed": just_completed}
            output.update(_after_complete(request, partner, video, notify=just_completed, team_member=team_member))
            if output["Next_Video"]:
                output["Message"] = f"Video completed. Next: {output['Next_Video']['Video_Title']}"
            elif output["Product_Completed"]:
                output["Message"] = f"All videos of {video.Module.Product_Name} completed. You can get your certificate."
            else:
                output["Message"] = "Video completed."
            return _reply(output)
        except Exception as e:
            return _error(str(e))

# ---------------------------------------------------------------------------
# ACTIVITY  (analysis: every start / stop of a partner, optionally one video)
#    GET /PartnerVideoActivity/?Partner=1&Video=5
# ---------------------------------------------------------------------------
class PartnerVideoActivity(APIView):
    def get(self, request, *args, **kwargs):
        try:
            partner = _get_partner(request)
            if not partner:
                return _error("Partner not found", status.HTTP_404_NOT_FOUND)
            sessions = VideoWatchSession.objects.filter(
                Progress__Enrollment__Partner=partner, Is_Deleted=False
            ).select_related("Progress__Video").order_by("-id")
            video_id = request.query_params.get("Video")
            if video_id:
                sessions = sessions.filter(Progress__Video_id=video_id)
            rows = []
            for s in sessions[:200]:
                start = _session_start(s)
                stopped = s.Last_Position_Seconds if s.Status not in ("Playing", "Interrupted") else None
                rows.append({
                    "Session": s.id, "Session_Id": s.VideoWatchSession_Id,
                    "Video": s.Progress.Video_id, "Video_Title": s.Progress.Video.Video_Title,
                    "Status": s.Status,
                    "Started_Date": s.Started_Date, "Ended_Date": s.Ended_Date,
                    "Started_At_Second": start, "Stopped_At_Second": stopped,
                    "Counted_Seconds": max(0, stopped - start) if stopped is not None else 0})
            output = {"Partner": partner.id, "Total_Sessions": len(rows), "Sessions": rows}
            if video_id:
                progress = VideoProgress.objects.filter(Enrollment__Partner=partner, Video_id=video_id, Is_Deleted=False).first()
                output["Progress"] = {
                    "Status": progress.Status, "Watch_Percentage": _num(progress.Watch_Percentage),
                    "Watched_Seconds": progress.Watched_Seconds, "Resume_At_Seconds": progress.Last_Position_Seconds,
                    "First_Started_Date": progress.First_Started_Date, "Completed_Date": progress.Completed_Date,
                } if progress else None
            return _reply(output)
        except Exception as e:
            return _error(str(e))




# ---------------------------------------------------------------------------
# 6. "Get Certificate" button (end of the product's video list)
#    POST /PartnerCertificateGenerate/   {"Partner": 1, "Product_Name": "Pegatto CRM"}
#    - checks every published video of the product is Completed by this partner
#    - first click: Status Eligible -> Issued, sets Certificate_Number and Issued_Date (no expiry)
#    - next clicks: returns the same certificate (safe to call again to display it)
# ---------------------------------------------------------------------------
def _certificate_reply(certificate, partner, total, modules):
    return {
        "id": certificate.id,
        "Certificate_Id": certificate.Certificate_Id,
        "Certificate_Number": certificate.Certificate_Number,
        "Status": certificate.Status,
        "Partner": partner.id,
        "Partner_Name": partner.Trade_Name or partner.Legal_Name,
        "Partner_Code": partner.Partner_Code,
        "Product_Name": certificate.Product_Name,
        "Total_Modules": modules,
        "Total_Videos": total,
        "Issued_Date": certificate.Issued_Date}


class PartnerCertificateGenerate(APIView):
    def post(self, request, *args, **kwargs):
        try:
            partner = _get_partner(request)
            if not partner:
                return _error("Partner not found", status.HTTP_404_NOT_FOUND)
            product = (request.data.get("Product_Name") or "").strip()
            if not product:
                return _error("Product_Name is required")
            if product not in _partner_products(partner):
                return _error("This product is not assigned to you", status.HTTP_403_FORBIDDEN)

            team_member = _get_team_member(request)
            _, states, total, done, _ = _product_summary(partner, product, team_member=team_member)
            if not total:
                return _error("This product has no published videos yet")
            if done < total:
                return _error(f"Complete all videos of {product} first. Completed {done} of {total}.",
                              status.HTTP_403_FORBIDDEN)
            modules = len({video.Module_id for video, _ in states})

            user = _user(request)
            now = timezone.now()
            with transaction.atomic():
                cert_qs = Certificate.objects.select_for_update().filter(
                    Product_Name=product[:50], Is_Deleted=False)
                if team_member:
                    cert_qs = cert_qs.filter(PartnerTeamMember=team_member)
                else:
                    cert_qs = cert_qs.filter(Partner=partner, PartnerTeamMember__isnull=True)
                certificate = cert_qs.first()
                if certificate and certificate.Status == "Issued":
                    return _reply(_certificate_reply(certificate, partner, total, modules))     # already issued
                if certificate and certificate.Status == "Revoked":
                    return _error("This certificate was revoked. Contact support.", status.HTTP_403_FORBIDDEN)
                if not certificate:
                    certificate = Certificate(
                        Partner=partner,
                        PartnerTeamMember=team_member if team_member else None,
                        Product_Name=product[:50],
                        Created_By=user
                    )
                certificate.Status = "Issued"
                certificate.Issued_Date = now
                certificate.Updated_By = user
                certificate.save()
                if not certificate.Certificate_Number:
                    certificate.Certificate_Number = f"PEG-{now.year}-{certificate.id:06d}"
                    certificate.save(update_fields=["Certificate_Number"])
                AcademyNotification.objects.create(
                    Partner=partner, Recipient=user, Title="Certificate issued",
                    Message=f"Your {product} certificate {certificate.Certificate_Number} is ready.",
                    Notification_Type="Certificate", Created_By=user, Updated_By=user)
            return _reply(_certificate_reply(certificate, partner, total, modules), status.HTTP_201_CREATED)
        except Exception as e:
            return _error(str(e))


# ---------------------------------------------------------------------------
# 6b. "View Certificate" button
#     GET /PartnerCertificateView/?Partner=1&Product_Name=Pegatto CRM
#     GET /PartnerCertificateView/?Partner=1&Certificate=4
#     Returns the issued certificate with live details for the certificate screen.
# ---------------------------------------------------------------------------
class PartnerCertificateView(APIView):
    def get(self, request, *args, **kwargs):
        try:
            partner = _get_partner(request)
            if not partner:
                return _error("Partner not found", status.HTTP_404_NOT_FOUND)
            team_member = _get_team_member(request)
            params = request.query_params
            certificates = Certificate.objects.filter(Is_Deleted=False)
            if team_member:
                certificates = certificates.filter(PartnerTeamMember=team_member)
            else:
                certificates = certificates.filter(Partner=partner, PartnerTeamMember__isnull=True)

            if params.get("Certificate"):
                certificate = certificates.filter(id=params.get("Certificate")).first()
            elif params.get("Product_Name"):
                certificate = certificates.filter(Product_Name=params.get("Product_Name").strip()[:50]).first()
            else:
                return _error("Product_Name or Certificate is required")
            if not certificate or certificate.Status != "Issued":
                return _error("Certificate is not issued yet. Complete all videos and click 'Issue Certificate'.",
                              status.HTTP_404_NOT_FOUND)

            _, states, total, done, _ = _product_summary(partner, certificate.Product_Name, team_member=team_member)
            modules = []
            for video, _ in states:
                if not modules or modules[-1]["Module"] != video.Module_id:
                    modules.append({"Module": video.Module_id, "Module_Name": video.Module.Module_Name,
                                    "Module_Code": video.Module.Module_Code, "Videos": 0, "Duration_Seconds": 0})
                modules[-1]["Videos"] += 1
                modules[-1]["Duration_Seconds"] += video.Duration_Seconds or 0
            output = _certificate_reply(certificate, partner, total, len(modules))
            output.update({
                "Completed_Videos": done,
                "Total_Duration_Seconds": sum(m["Duration_Seconds"] for m in modules),
                "Total_Duration": _hours_minutes(sum(m["Duration_Seconds"] for m in modules)),
                "Modules": modules})
            return _reply(output)
        except Exception as e:
            return _error(str(e))



# ---------------------------------------------------------------------------
# 7. Partner dashboard (one call for the whole Dashboard page)
#    GET /PartnerDashboard/?Partner=1
# ---------------------------------------------------------------------------
def _hours_minutes(seconds):
    seconds = int(seconds or 0)
    hours, minutes = seconds // 3600, (seconds % 3600) // 60
    return f"{hours}h {minutes}m" if hours else f"{minutes}m"


class PartnerDashboard(APIView):
    def get(self, request, *args, **kwargs):
        try:
            partner = _get_partner(request)
            if not partner:
                return _error("Partner not found", status.HTTP_404_NOT_FOUND)
            user = _user(request)

            # products ------------------------------------------------------------
            products = []
            all_total = all_done = 0
            for product in _partner_products(partner):
                progress, states, total, done, current = _product_summary(partner, product)
                all_total += total
                all_done += done
                watched = sum(row.Watched_Seconds for row in progress.values())
                if total and done >= total:
                    product_status = "Completed"
                elif progress:
                    product_status = "In Progress"
                else:
                    product_status = "Not Started"
                products.append({
                    **_certificate_info(partner, product, total, done),
                    "Product_Name": product,
                    "Total_Modules": len({video.Module_id for video, _ in states}),
                    "Total_Videos": total,
                    "Completed_Videos": done,
                    "Progress_Percentage": round(done * 100 / total) if total else 0,
                    "Total_Duration_Seconds": sum(video.Duration_Seconds or 0 for video, _ in states),
                    "Watched_Seconds": watched,
                    "Status": product_status,
                    "Next_Video": _video_brief(current)})

            # progress rows of this partner ---------------------------------------
            rows = VideoProgress.objects.filter(Enrollment__Partner=partner, Is_Deleted=False).select_related("Video__Module")
            total_watched = sum(row.Watched_Seconds for row in rows)

            # continue watching: last video started but not completed
            last = rows.filter(Status="In Progress", Video__Is_Deleted=False, Video__Status="Published") \
                       .order_by("-Last_Watched_Date").first()
            continue_watching = None
            if last and last.Video.Module and last.Video.Module.Product_Name in _partner_products(partner):
                video = last.Video
                continue_watching = {
                    **_video_brief(video),
                    "Product_Name": video.Module.Product_Name,
                    "Watch_Percentage": _num(last.Watch_Percentage),
                    "Resume_At_Seconds": last.Last_Position_Seconds,
                    "Last_Watched_Date": last.Last_Watched_Date}

            # recent activity: last 5 completed videos
            recent = [{
                "Video": row.Video_id, "Video_Title": row.Video.Video_Title,
                "Product_Name": row.Video.Module.Product_Name if row.Video.Module else None,
                "Completed_Date": row.Completed_Date}
                for row in rows.filter(Status="Completed").order_by("-Completed_Date")[:5]]

            # modules ---------------------------------------------------------------
            enrollments = ModuleEnrollment.objects.filter(Partner=partner, Is_Deleted=False)

            # certificates ----------------------------------------------------------
            certificates = [{
                "id": c.id, "Certificate_Number": c.Certificate_Number, "Product_Name": c.Product_Name,
                "Status": c.Status, "Issued_Date": c.Issued_Date}
                for c in Certificate.objects.filter(Partner=partner, Is_Deleted=False,
                                                    Status__in=("Issued", "Revoked", "Expired")).order_by("-id")]

            # notifications (for the logged-in user) --------------------------------
            notes = AcademyNotification.objects.filter(Partner=partner, Is_Deleted=False)
            unread = notes.filter(Is_Read=False).count()
            latest = [{
                "id": n.id, "Title": n.Title, "Message": n.Message,
                "Notification_Type": n.Notification_Type, "Is_Read": n.Is_Read,
                "Created_Date": n.Created_Date}
                for n in notes.order_by("-id")[:5]]

            return _reply({
                "Partner": partner.id,
                "Partner_Id": partner.Partner_Id,
                "Partner_Name": partner.Trade_Name or partner.Legal_Name,
                "Partner_Code": partner.Partner_Code,
                "Tier": partner.Tier,
                "Summary": {
                    "Overall_Percentage": round(all_done * 100 / all_total) if all_total else 0,
                    "Total_Products": len(products),
                    "Products_Completed": sum(1 for p in products if p["Status"] == "Completed"),
                    "Products_In_Progress": sum(1 for p in products if p["Status"] == "In Progress"),
                    "Total_Videos": all_total,
                    "Videos_Completed": all_done,
                    "Modules_Completed": enrollments.filter(Status="Completed").count(),
                    "Modules_In_Progress": enrollments.filter(Status="In Progress").count(),
                    "Total_Watch_Seconds": total_watched,
                    "Total_Watch_Time": _hours_minutes(total_watched),
                    "Certificates_Issued": sum(1 for c in certificates if c["Status"] == "Issued"),
                    "Certificates_Ready_To_Claim": sum(1 for p in products if p["Certificate_Status"] == "Eligible"),
                    "Unread_Notifications": unread},
                "Continue_Watching": continue_watching,
                "Products": products,
                "Certificates": certificates,
                "Recent_Activity": recent,
                "Notifications": latest})
        except Exception as e:
            return _error(str(e))



