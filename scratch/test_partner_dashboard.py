import os, sys
sys.path.insert(0, r'D:\Shajitha\BACKEND\SUPERADMIN\superadmin_user_useradmin_be')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CRM.settings')
import django
django.setup()

from partner.models import Partner, PartnerTeamMember
from partneracademy.views import PartnerDashboard
from rest_framework.test import APIRequestFactory

p = Partner.objects.first()
print('Partner:', p.id, p.Partner_Id, p.Legal_Name)
team = PartnerTeamMember.objects.filter(Partner_Id=p)
print('Team count:', team.count())

factory = APIRequestFactory()
view = PartnerDashboard.as_view()
req = factory.get(f'/partneracademy/PartnerDashboard/?Partner={p.id}')
res = view(req)
print('Status:', res.status_code)
print('Keys:', list(res.data.get('data', {}).keys()))
