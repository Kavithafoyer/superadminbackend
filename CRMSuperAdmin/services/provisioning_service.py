import re
import logging
from django.db import connections
from django.db.models import Q
from django.conf import settings
from psycopg2 import sql

logger = logging.getLogger(__name__)

BASE_DOMAIN = "pegatto.com"

# Standard product code to subdomain slug mapping
PRODUCT_SUBDOMAIN_MAP = {
    'CRM': 'crm',
    'PEGATTOCRM': 'crm',
    'HRM': 'hrm',
    'FELIX': 'hrm',
    'BOLTMM': 'bolt',
    'BOLT': 'bolt',
    'QINTRASA': 'qintrasa',
    'QINTRA': 'qintrasa',
    'RETAIL': 'retail',
    'EDUCATION': 'education',
    'IT': 'it',
    'REALESTATE': 'realestate',
}

# Standard product code to DATABASES connection alias mapping
PRODUCT_DB_ALIAS_MAP = {
    'CRM': 'Product_CRM',
    'PEGATTOCRM': 'Product_CRM',
    'HRM': 'Product_FelixHR',
    'FELIX': 'Product_FelixHR',
    'BOLTMM': 'Product_Bolt',
    'BOLT': 'Product_Bolt',
    'QINTRASA': 'Product_Qintra',
    'QINTRA': 'Product_Qintra',
}


def normalize_product_code(product) -> str:
    """
    Extracts and normalizes product code from:
    - ProductMaster instance
    - Integer ID (looks up ProductMaster)
    - String code/name (e.g. 'CRM', 'HRM', 'boltMM')
    """
    if not product:
        return 'CRM'

    if hasattr(product, 'Product_Code') and product.Product_Code:
        return str(product.Product_Code).strip().upper()

    if isinstance(product, int):
        try:
            from CRMSuperAdmin.models import ProductMaster
            p = ProductMaster.objects.filter(id=product).first()
            if p and p.Product_Code:
                return str(p.Product_Code).strip().upper()
        except Exception as e:
            logger.warning(f"Failed to lookup ProductMaster by ID {product}: {e}")

    code_str = str(product).strip()
    # Check if numeric string
    if code_str.isdigit():
        try:
            from CRMSuperAdmin.models import ProductMaster
            p = ProductMaster.objects.filter(id=int(code_str)).first()
            if p and p.Product_Code:
                return str(p.Product_Code).strip().upper()
        except Exception:
            pass

    return code_str.upper()


def resolve_product_subdomain(tenant_slug: str, product=None, base_domain: str = BASE_DOMAIN) -> str:
    """
    Generates standard product-specific subdomain:
    - CRM    -> <tenant_slug>.crm.pegatto.com
    - HRM    -> <tenant_slug>.hrm.pegatto.com
    - boltMM -> <tenant_slug>.bolt.pegatto.com
    """
    if not tenant_slug:
        return ""

    tenant_slug = str(tenant_slug).strip().lower()

    # If it's already a full domain with pegatto.com, return it cleanly
    if tenant_slug.endswith(f".{base_domain}"):
        return tenant_slug

    prod_code = normalize_product_code(product)
    subdomain_slug = PRODUCT_SUBDOMAIN_MAP.get(prod_code, prod_code.lower())

    # Sanitize tenant slug: remove protocol, slashes, whitespace, and product prefixes if redundant
    cleaned_slug = re.sub(r'^(https?://)', '', tenant_slug)
    cleaned_slug = re.sub(r'[^a-z0-9\-]', '', cleaned_slug)
    cleaned_slug = cleaned_slug.strip('-')

    # Avoid duplicating product slug if user passed "acme.crm" or "acme-crm"
    if cleaned_slug.endswith(f".{subdomain_slug}"):
        cleaned_slug = cleaned_slug[:-len(f".{subdomain_slug}")]
    elif cleaned_slug.endswith(f"-{subdomain_slug}"):
        cleaned_slug = cleaned_slug[:-len(f"-{subdomain_slug}")]

    return f"{cleaned_slug}.{subdomain_slug}.{base_domain}"


def get_product_db_alias(product=None) -> str:
    """
    Resolves product to target database settings alias in DATABASES.
    Defaults to 'Product_CRM' if unmapped.
    """
    prod_code = normalize_product_code(product)
    alias = PRODUCT_DB_ALIAS_MAP.get(prod_code)

    # Check if alias exists in Django settings.DATABASES
    if alias and alias in settings.DATABASES:
        return alias

    return 'Product_CRM'


def sanitize_database_name(db_name: str, prefix: str = "") -> str:
    """
    Ensures safe PostgreSQL database name containing only alphanumeric characters and underscores.
    """
    clean_name = re.sub(r'[^a-zA-Z0-9_]', '_', str(db_name).strip()).lower()
    clean_name = re.sub(r'_+', '_', clean_name).strip('_')
    if prefix and not clean_name.startswith(f"{prefix}_"):
        clean_name = f"{prefix}_{clean_name}"
    return clean_name


def create_tenant_database(database_name: str, product=None) -> dict:
    """
    Dynamically creates a tenant database on the appropriate product DB server.
    """
    if not database_name:
        raise ValueError("database_name is required")

    sanitized_db = sanitize_database_name(database_name)
    db_alias = get_product_db_alias(product)

    conn = connections[db_alias]
    conn.ensure_connection()

    prev_autocommit = conn.connection.autocommit
    conn.connection.autocommit = True
    try:
        with conn.connection.cursor() as cursor:
            # Check if database already exists
            cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", [sanitized_db])
            if cursor.fetchone():
                logger.info(f"Tenant database '{sanitized_db}' already exists on '{db_alias}'.")
                return {
                    'success': True,
                    'created': False,
                    'database_name': sanitized_db,
                    'db_alias': db_alias,
                    'host': conn.settings_dict.get('HOST')
                }

            # Create database using quoted identifier
            cursor.execute(sql.SQL('CREATE DATABASE {}').format(sql.Identifier(sanitized_db)))
            logger.info(f"Successfully created tenant database '{sanitized_db}' on '{db_alias}' ({conn.settings_dict.get('HOST')}).")
            return {
                'success': True,
                'created': True,
                'database_name': sanitized_db,
                'db_alias': db_alias,
                'host': conn.settings_dict.get('HOST')
            }
    finally:
        conn.connection.autocommit = prev_autocommit


def get_request_product_id(request):
    """
    Extracts product identifier from incoming request.
    Supports:
    - Headers: HTTP_X_PRODUCT_ID, HTTP_X_PRODUCT_CODE, X-Product-Id, X-Product-Code
    - Query Params: product_id, product, product_code, Product_Id
    Returns:
        int (ProductMaster id) or None if 'all' / omitted / invalid.
    """
    if not request:
        return None

    # Check query params first
    query_params = getattr(request, 'query_params', None)
    if query_params is None and hasattr(request, 'GET'):
        query_params = request.GET

    raw_val = None
    if query_params:
        raw_val = (
            query_params.get('product_id') or
            query_params.get('Product_Id') or
            query_params.get('product_code') or
            query_params.get('product')
        )

    # Check headers if not found in query params
    if not raw_val:
        headers = getattr(request, 'headers', None)
        if headers:
            raw_val = (
                headers.get('X-Product-Id') or
                headers.get('X-Product-Code') or
                headers.get('x-product-id') or
                headers.get('x-product-code')
            )
        if not raw_val and hasattr(request, 'META'):
            raw_val = request.META.get('HTTP_X_PRODUCT_ID') or request.META.get('HTTP_X_PRODUCT_CODE')

    if not raw_val or str(raw_val).strip().lower() in ('', 'all', 'null', 'undefined', '0'):
        return None

    raw_val = str(raw_val).strip()
    if raw_val.isdigit():
        return int(raw_val)

    # Try resolving product code/name to ID
    try:
        from CRMSuperAdmin.models import ProductMaster
        prod = ProductMaster.objects.filter(
            Q(Product_Code__iexact=raw_val) | Q(Product_Name__iexact=raw_val)
        ).first()
        if prod:
            return prod.id
    except Exception:
        pass

    return None


def filter_by_product(queryset, request, field_override=None):
    """
    Applies product scoping filter on a Django queryset if a specific product is selected in request.
    If 'all' or no product is selected, returns the unfiltered queryset.
    Handles:
    - Plan (Product_id)
    - AddonMaster (Products__id)
    - Invoice (Product_Id_id, Products__id, items__Product_Id_id)
    - Subscriptions, Payments, Instance_Creation, InstanceRequest, etc. (Product_Id_id)
    """
    prod_id = get_request_product_id(request)
    if not prod_id:
        return queryset

    model = getattr(queryset, 'model', None)
    model_name = model.__name__ if model else ''

    if field_override:
        return queryset.filter(**{field_override: prod_id}).distinct()

    if model_name == 'Plan':
        return queryset.filter(Product_id=prod_id)
    elif model_name == 'AddonMaster':
        return queryset.filter(Products__id=prod_id).distinct()
    elif model_name == 'Invoice':
        return queryset.filter(
            Q(Product_Id_id=prod_id) | Q(Products__id=prod_id) | Q(items__Product_Id_id=prod_id)
        ).distinct()
    else:
        # Check standard model fields
        if hasattr(model, 'Product_Id'):
            return queryset.filter(Product_Id_id=prod_id)
        elif hasattr(model, 'Product'):
            return queryset.filter(Product_id=prod_id)
        elif hasattr(model, 'Products'):
            return queryset.filter(Products__id=prod_id).distinct()
        return queryset

