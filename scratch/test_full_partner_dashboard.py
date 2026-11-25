import os, sys, json
sys.path.insert(0, r'D:\Shajitha\BACKEND\SUPERADMIN\superadmin_user_useradmin_be')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CRM.settings')
import django
django.setup()

from partner.models import Partner, PartnerTeamMember
from partneracademy.models import VideoProgress, ModuleEnrollment, Certificate, AcademyNotification
from partneracademy.views import _get_partner, _partner_products, _product_summary, _certificate_info, _video_brief, _hours_minutes, _num, _reply, _user, _error

p = Partner.objects.first()
print('Testing Partner:', p.id)

# Run logic
partner_prods = _partner_products(p)
team_members_qs = PartnerTeamMember.objects.filter(Partner_Id=p, Is_Deleted=False).order_by('-pk')
print('Team members count:', team_members_qs.count())

for m in team_members_qs:
    m_products = []
    for prod in partner_prods:
        m_prog, m_st, m_tot, m_done, m_curr = _product_summary(p, prod, team_member=m)
        m_products.append({'prod': prod, 'tot': m_tot, 'done': m_done})
    print(f'Member {m.First_Name} products:', m_products)

print('SUCCESS!')
