import os, sys, json
sys.path.insert(0, r'D:\Shajitha\BACKEND\SUPERADMIN\superadmin_user_useradmin_be')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CRM.settings')
import django
django.setup()

from partner.models import Partner, PartnerTeamMember
from partneracademy.models import VideoProgress, ModuleEnrollment, Certificate
from partneracademy.views import _partner_products, _product_summary, _certificate_info, _video_brief, _hours_minutes, _num

p = Partner.objects.first()
team_members = PartnerTeamMember.objects.filter(Partner_Id=p, Is_Deleted=False)
print('Testing for Partner:', p.id, p.Trade_Name or p.Legal_Name)
print('Team Members:', [m.First_Name for m in team_members])

prods = _partner_products(p)
print('Partner products:', prods)
for m in team_members:
    for prod in prods:
        progress, states, total, done, current = _product_summary(p, prod, team_member=m)
        print(f'Member {m.First_Name} - Prod {prod}: total={total}, done={done}')
print('SUCCESS!')
