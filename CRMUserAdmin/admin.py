from django.contrib import admin

# Register your models here.
from .models import *



admin.site.register(Useraddress)
admin.site.register(Userrole)
admin.site.register(CRMUsers)
admin.site.register(Userorganizationmaster)
# admin.site.register(Ticket)
# admin.site.register(TicketResponse)
admin.site.register(CRMBusinessHours)
# admin.site.register(TransactionalSeries)
admin.site.register(Template)
admin.site.register(Notification)
admin.site.register(Userlookup)
admin.site.register(Taskuser)
admin.site.register(Company)
admin.site.register(FormMaster)
admin.site.register(FormPermission)

