from django.db import connections, DEFAULT_DB_ALIAS, connection
from django.db.utils import ConnectionHandler, ProgrammingError
from django.core.management import call_command
from django.conf import settings
from psycopg2 import sql
import psycopg2
from django.conf import settings
import os
import subprocess
import pandas as pd
from django.contrib.auth import get_user_model
User = get_user_model()
from shutil import which
from django.conf import settings
from utils.threadlocal import get_current_tenant, get_current_product
from CRMSuperAdmin.services.provisioning_service import (
    create_tenant_database as dynamic_create_tenant_database,
    resolve_product_subdomain,
    get_product_db_alias,
    sanitize_database_name,
)


def create_tenant_database(database_name, product=None): #,User_Name,SU_Password,SU_Email_ID
    try:
        # Determine product if not explicitly provided
        if not product:
            product = get_current_product() or get_current_tenant()
        
        result = dynamic_create_tenant_database(database_name, product=product)
        print("Tenant database created/verified:", result)
        return result
    except Exception as e:
        import traceback
        traceback.print_exc()
        print("Error creating tenant database:", e)
        raise e
    finally:
        set_current_tenant(None)
# def print_default_connection_settings():
#     default_connection = connections['default']
#     settings_dict = default_connection.settings_dict
#     print("Current default database connection settings:")
#     for key, value in settings_dict.items():
#         print(f"{key}: {value}")