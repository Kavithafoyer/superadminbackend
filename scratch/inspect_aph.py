import os, sys, django

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CRM.settings')
django.setup()

from django.db import connection
cursor = connection.cursor()
cursor.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'AddonPriceHistory'")
print("Columns in AddonPriceHistory:")
for col in cursor.fetchall():
    print(col)
