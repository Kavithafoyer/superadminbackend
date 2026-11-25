# # done by shajitha
# # Pegatto Academy - after upload: read duration + make thumbnail, then mark Ready
# import json
# import os
# import subprocess
# import tempfile

# from celery import shared_task

# from . import storage
# from .models import TrainingVideo


# @shared_task
# def process_training_video(video_pk):
#     video = TrainingVideo.objects.filter(id=video_pk, Is_Deleted=False).first()
#     if not video:
#         return
#     try:
#         # ffprobe / ffmpeg can read straight from a signed link, no need to download the full file
#         src = storage.presigned_get(video.Video_Key, 3600)

#         probe = subprocess.run(
#             ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", src],
#             capture_output=True, text=True, check=True, timeout=300)
#         video.Duration_Seconds = int(float(json.loads(probe.stdout)["format"]["duration"]))

#         with tempfile.TemporaryDirectory() as tmp:
#             thumb = os.path.join(tmp, "thumb.jpg")
#             subprocess.run(
#                 ["ffmpeg", "-y", "-ss", "3", "-i", src, "-frames:v", "1", "-vf", "scale=480:-1", thumb],
#                 capture_output=True, check=True, timeout=300)
#             key = storage.thumbnail_key(video.Video_Id)
#             storage.get_s3_client().upload_file(
#                 thumb, storage.get_bucket(), key, ExtraArgs={"ContentType": "image/jpeg"})
#             video.Thumbnail_Key = key

#         video.Upload_Status = "Ready"
#         video.Processing_Error = None
#     except Exception as e:
#         video.Upload_Status = "Failed"
#         video.Processing_Error = str(e)[:2000]
#     video.save()



