import logging

from django.conf import settings
from django.db import connection, connections
from django.http import Http404
from psycopg2 import sql

from utils.threadlocal import (
    set_current_tenant,
    set_current_product,
    set_current_tenant_id,
    set_current_db_alias,   # add this function in threadlocal.py
)

logger = logging.getLogger(__name__)

DEFAULT_DB_NAME = settings.DATABASES["default"]["NAME"]


class TenantMiddleware:

    FIXED_TENANT_DB_MAPPING = {
        "crmfarmsa": "default",
        "partner": "default",
        "hrmsa": "hrmsa",
        "mmsa": "mmsa",
        "qintrasa":"qintrasa",
        "pegatto_superadmin":"pegatto_superadmin",
    }

    EXCLUDED_PATHS = (
        "/favicon.ico",
        "/static/",
        "/media/",
        "/prometheus/",
        "/partner/",
        "/partneracademy/",
        "/token/",
        "/auth/",
        "/api/",
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def switch_database(self, db_name):
        try:
            if connection.settings_dict.get('NAME') != db_name or connection.connection is None:
                connection.close()
                connection.settings_dict['NAME'] = db_name
                connection.connect()
                logger.info(f"Switched to DB : {db_name}")
        except Exception as e:
            logger.error(f"DB Switch Error : {str(e)}")
            raise

    def __call__(self, request):

        path = request.path

        # =====================================
        # SKIP STATIC / MEDIA / FAVICON
        # =====================================
        if (
            path == "/favicon.ico"
            or path.startswith("/static/")
            or path.startswith("/media/")
            or path.startswith("/prometheus/")
            or path.startswith("/partner/")
            or path.startswith("/partneracademy/")
            or path.startswith("/token/")
            or path.startswith("/auth/")
            or path.startswith("/api/")
            or "/partner/" in path
            or "/partneracademy/" in path
            or "/api/" in path
            or "/token/" in path
            or "/auth/" in path
        ):
            return self.get_response(request)

        try:

            path_parts = path.strip("/").split("/")

            if not path_parts or not path_parts[0]:
                return self.get_response(request)

            tenant = path_parts[0].lower()

            logger.info(f"Tenant: {tenant}")

            set_current_tenant(tenant)

            # =====================================
            # FIXED TENANTS
            # =====================================
            if tenant in self.FIXED_TENANT_DB_MAPPING:

                db_alias = self.FIXED_TENANT_DB_MAPPING[tenant]

                request.db_alias = db_alias

                set_current_db_alias(db_alias)

                request.Product = tenant.upper()

                set_current_product(tenant.upper())
                set_current_tenant_id(None)

                target_db = DEFAULT_DB_NAME if db_alias == "default" else db_alias
                self.switch_database(target_db)

                logger.info(
                    f"Tenant={tenant} DB Alias={db_alias} DB Name={target_db}"
                )

                return self.get_response(request)

            # =====================================
            # DYNAMIC TENANT LOOKUP
            # =====================================
            self.switch_database(DEFAULT_DB_NAME)

            with connections["default"].cursor() as cursor:

                query = sql.SQL("""
                    SELECT *
                    FROM {}
                    WHERE {} = %s
                    LIMIT 1
                """).format(
                    sql.Identifier("Instance_CreationUserAdmin"),
                    sql.Identifier("Domain_Name"),
                )

                cursor.execute(query, [tenant])

                row = cursor.fetchone()

                if not row:
                    raise Http404(
                        f"Tenant '{tenant}' not found"
                    )

                columns = [
                    col.name
                    for col in cursor.description
                ]

                data = dict(zip(columns, row))

            db_alias = data.get("Database_Name")

            if not db_alias:
                raise Http404(
                    f"No database configured for tenant '{tenant}'"
                )

            request.db_alias = db_alias

            set_current_db_alias(db_alias)

            request.Product = data.get("Product")

            set_current_product(
                data.get("Product")
            )

            set_current_tenant_id(
                data.get("id")
            )

            self.switch_database(db_alias)

            logger.info(
                f"Tenant={tenant} DB Alias={db_alias}"
            )

            return self.get_response(request)

        except Http404:
            raise

        except Exception as e:

            logger.exception(
                f"Tenant Middleware Error: {str(e)}"
            )

            raise Http404(
                "Unable to process tenant request."
				)