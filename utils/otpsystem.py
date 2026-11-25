import secrets
import bcrypt

from django.utils import timezone
from datetime import timedelta


def generate_otp():
    return f"{secrets.randbelow(10**6):06d}"


def hash_otp(otp):
    hashed = bcrypt.hashpw(otp.encode(),bcrypt.gensalt())
    return hashed.decode()


def verify_otp(otp, otp_hash):
    return bcrypt.checkpw(otp.encode(),otp_hash.encode())


def otp_expiry_time():
    return timezone.now() + timedelta(minutes=5)