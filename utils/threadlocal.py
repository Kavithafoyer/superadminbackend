import threading

_thread_locals = threading.local()

def get_current_tenant():
    return getattr(_thread_locals, 'tenant', None)

def set_current_tenant(tenant):
    _thread_locals.tenant = tenant

#================================================================#
# :white_check_mark: Tenant Set/Get
def set_current_tenant_id(tenant_id):
    _thread_locals.tenant_id = tenant_id

def get_current_tenant_id():
    return getattr(_thread_locals, 'tenant_id', None)
#================================================================#

# :white_check_mark: Product Set/Get
def set_current_product(product):
    _thread_locals.product = product
    
def get_current_product():
    return getattr(_thread_locals, 'product', None)

#=================================================================#
def set_current_db_alias(value):
    _thread_locals.db_alias = value

def get_current_db_alias():
    return getattr(_thread_locals, "db_alias", "default")