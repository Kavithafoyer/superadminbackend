# # done by shajitha
# # Pegatto Academy - S3 helpers used by the training video APIs
# import boto3
# from botocore.config import Config
# from django.conf import settings

# _client = None


# def get_s3_client():
#     global _client
#     if _client is None:
#         _client = boto3.client(
#             "s3",
#             aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
#             aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
#             region_name=getattr(settings, "AWS_S3_REGION_NAME", None),
#             endpoint_url=getattr(settings, "AWS_S3_ENDPOINT_URL", None),   # only for S3-compatible storage
#             config=Config(signature_version="s3v4"))
#     return _client


# def get_bucket():
#     return settings.AWS_STORAGE_BUCKET_NAME


# def original_key(video_id):
#     return f"academy/videos/{video_id}/original.mp4"


# def thumbnail_key(video_id):
#     return f"academy/videos/{video_id}/thumbnail.jpg"


# def presigned_get(key, expires, content_type=None):
#     params = {"Bucket": get_bucket(), "Key": key}
#     if content_type:
#         params["ResponseContentType"] = content_type
#     return get_s3_client().generate_presigned_url("get_object", Params=params, ExpiresIn=expires)



