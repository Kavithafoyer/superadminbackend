
import os
import boto3
from dotenv import load_dotenv

load_dotenv()

BUCKET_NAME = os.getenv("R2_BUCKET_NAME")
ENDPOINT_URL = os.getenv("R2_ENDPOINT_URL")
ACCESS_KEY = os.getenv("R2_ACCESS_KEY_ID")
SECRET_KEY = os.getenv("R2_SECRET_ACCESS_KEY")

s3 = boto3.client(
    "s3",
    endpoint_url=ENDPOINT_URL,
    aws_access_key_id=ACCESS_KEY,
    aws_secret_access_key=SECRET_KEY,
    region_name="auto",
)

try:
    s3.put_object(
        Bucket=BUCKET_NAME,
        Key="connection-test.txt",
        Body=b"Hello from Django project!"
    )

    print("SUCCESS! Cloudflare R2 connected.")

except Exception as e:
    print("ERROR:", e)
