import os, sys, django
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CRM.settings')
django.setup()

from CRMSuperAdmin.models import AddonPriceHistory, AddonPricing, UserAdmin
from django.utils import timezone

user = UserAdmin.objects.first()

# Clear existing non-deleted to prevent duplicates
AddonPriceHistory.objects.all().delete()

pricing_map = {p.Addon_Name: p for p in AddonPricing.objects.all()}

history_data = [
    # WhatsApp CRM Integration (pricing id 4)
    {
        'addon_name': 'WhatsApp CRM Integration',
        'aph_id': 'APH000000001',
        'old_price': 499.00,
        'new_price': 499.00,
        'date': '2026-08-01 10:00:00',
        'reason': 'Initial product pricing setup for marketplace release',
    },
    {
        'addon_name': 'WhatsApp CRM Integration',
        'aph_id': 'APH000000002',
        'old_price': 499.00,
        'new_price': 599.00,
        'date': '2026-08-15 11:30:00',
        'reason': 'High-volume WhatsApp messaging API upgrade',
    },
    {
        'addon_name': 'WhatsApp CRM Integration',
        'aph_id': 'APH000000003',
        'old_price': 599.00,
        'new_price': 799.00,
        'date': '2026-10-01 14:00:00',
        'reason': 'Meta multi-agent WhatsApp broadcast support',
    },
    # AI Lead Scoring (pricing id 1)
    {
        'addon_name': 'AI Lead Scoring',
        'aph_id': 'APH000000004',
        'old_price': 299.00,
        'new_price': 399.00,
        'date': '2026-06-01 09:00:00',
        'reason': 'Advanced neural scoring model release',
    },
    {
        'addon_name': 'AI Lead Scoring',
        'aph_id': 'APH000000005',
        'old_price': 399.00,
        'new_price': 499.00,
        'date': '2026-08-01 10:00:00',
        'reason': 'Real-time enrichment pipeline integration',
    },
    # AI Sales Prediction (pricing id 2)
    {
        'addon_name': 'AI Sales Prediction',
        'aph_id': 'APH000000006',
        'old_price': 599.00,
        'new_price': 699.00,
        'date': '2026-07-01 12:00:00',
        'reason': 'Expanded enterprise forecast horizon',
    },
    {
        'addon_name': 'AI Sales Prediction',
        'aph_id': 'APH000000007',
        'old_price': 699.00,
        'new_price': 799.00,
        'date': '2026-09-01 15:30:00',
        'reason': 'Custom multi-pipeline prediction algorithms',
    },
    # AI CRM Assistant (pricing id 3)
    {
        'addon_name': 'AI CRM Assistant',
        'aph_id': 'APH000000008',
        'old_price': 199.00,
        'new_price': 299.00,
        'date': '2026-09-10 10:45:00',
        'reason': 'Autonomous bot assistant workflow engine',
    },
    # Document Generator (pricing id 5)
    {
        'addon_name': 'Document Generator',
        'aph_id': 'APH000000009',
        'old_price': 1299.00,
        'new_price': 999.00,
        'date': '2026-10-15 16:20:00',
        'reason': 'Promotional price cut & infra cost reduction',
    },
    # AI Bug Fixing Agent (pricing id 6)
    {
        'addon_name': 'AI Bug Fixing Agent',
        'aph_id': 'APH000000010',
        'old_price': 1299.00,
        'new_price': 1499.00,
        'date': '2026-11-05 17:00:00',
        'reason': 'Deep static analysis & AST rewrite engine update',
    },
]

created = 0
for item in history_data:
    pricing = pricing_map.get(item['addon_name'])
    if not pricing:
        pricing = AddonPricing.objects.first()
    
    dt = timezone.make_aware(datetime.strptime(item['date'], '%Y-%m-%d %H:%M:%S'))
    aph = AddonPriceHistory.objects.create(
        AddonPriceHistory_Id=item['aph_id'],
        Addon_Pricing=pricing,
        Old_Base_Price=item['old_price'],
        New_Base_Price=item['new_price'],
        Reason=item['reason'],
        Changed_By=user,
        Change_Date=dt,
        Is_Deleted=False,
    )
    created += 1

print(f"Successfully seeded {created} AddonPriceHistory records into DB!")
