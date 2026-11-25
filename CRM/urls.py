"""CRM URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
import os
from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import (TokenObtainPairView,TokenRefreshView,)
from django.conf import settings
from django.conf.urls.static import static
from django.http import Http404
from django.views.static import serve
from CRMUserAdmin import urls
from CRMSuperAdmin import urls
from CRMSuperAdmin.views import PartnerAssignMailAPI




def dynamic_serve_media(request, tenant_name, path):
    # Construct the full path to the media file based on tenant_name
    full_path = os.path.join(settings.MEDIA_ROOT, path)
    print("full_path",full_path)
    # Check if the requested file exists
    if os.path.exists(full_path):
        # Serve the requested file
        serv=serve(request, path, document_root=os.path.join(settings.MEDIA_ROOT))
        return serv
    else:
        # Raise a 404 error if the file doesn't exist
        raise Http404("Media file does not exist")

"""CRM URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
import os
from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import (TokenObtainPairView,TokenRefreshView,)
from django.conf import settings
from django.conf.urls.static import static
from django.http import Http404
from django.views.static import serve
from CRMUserAdmin import urls
from CRMSuperAdmin import urls
from CRMSuperAdmin.views import PartnerAssignMailAPI




def dynamic_serve_media(request, tenant_name, path):
    # Construct the full path to the media file based on tenant_name
    full_path = os.path.join(settings.MEDIA_ROOT, path)
    print("full_path",full_path)
    # Check if the requested file exists
    if os.path.exists(full_path):
        # Serve the requested file
        serv=serve(request, path, document_root=os.path.join(settings.MEDIA_ROOT))
        return serv
    else:
        # Raise a 404 error if the file doesn't exist
        raise Http404("Media file does not exist")



urlpatterns = [
                path('prometheus/', include('django_prometheus.urls')),
                path("partner-assign-mail/", PartnerAssignMailAPI.as_view(), name='root-partner-assign-mail'),
                path("<str:tenant_name>/partner-assign-mail/", PartnerAssignMailAPI.as_view(), name='tenant-partner-assign-mail'),
                path("<str:tenant_name>/useradmin/",include('CRMUserAdmin.urls')),
                path("<str:tenant_name>/chatsystem/",include('CRMchat.urls')),
                path("<str:tenant_name>/superadmin/",include('CRMSuperAdmin.urls')),
                path("<str:tenant_name>/auth/",include('authapp.urls')),
                path('<str:tenant_name>/token/', TokenObtainPairView.as_view()),
                # path('<str:tenant_name>/token/', CustomTokenObtainPairView.as_view()),
                path('<str:tenant_name>/token/refresh/', TokenRefreshView.as_view()),
                path('<str:tenant_name>/media/<path:path>',dynamic_serve_media),
                path("partneracademy/", include('partneracademy.urls')),
                path("partner/", include('partner.urls')),
                path("<str:tenant_name>/partneracademy/",include('partneracademy.urls')),
                path("<str:tenant_name>/partner/",include('partner.urls')),
              ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) + static(settings.STATIC_URL,document_root=settings.STATIC_ROOT)
