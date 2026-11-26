import os, sys, django

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CRM.settings')
django.setup()

from django.db import connection
cursor = connection.cursor()
cursor.execute('ALTER TABLE "AddonPriceHistory" ADD COLUMN IF NOT EXISTS "Reason" text;')
print("Added Reason column successfully!")
