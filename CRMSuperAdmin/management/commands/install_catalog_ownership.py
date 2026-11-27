from django.core.management.base import BaseCommand, CommandError
from django.db import DEFAULT_DB_ALIAS, connections, transaction

from CRMSuperAdmin.SW_DB_Middleware_User import TenantMiddleware
from CRMSuperAdmin.models import ModuleMaster, ProductEdition, ProductFeature


class Command(BaseCommand):
    help = "Install the module and feature ownership fields and missing catalog relationship tables."

    def add_arguments(self, parser):
        target = parser.add_mutually_exclusive_group()
        target.add_argument("--database", default=DEFAULT_DB_ALIAS)
        target.add_argument(
            "--tenant", choices=sorted(TenantMiddleware.FIXED_TENANT_DB_MAPPING),
            help="Use the same database as requests with this fixed tenant URL prefix.",
        )
        parser.add_argument(
            "--require-edition", nargs=2, type=int, metavar=("PRODUCT_ID", "EDITION_ID"),
            help="Verify this product and edition before making any schema changes.",
        )
        parser.add_argument("--check", action="store_true", help="Report missing schema without changing it.")

    def handle(self, *args, **options):
        alias = options["database"]
        connection = connections[alias]
        tenant = options["tenant"]
        if tenant:
            database = TenantMiddleware.FIXED_TENANT_DB_MAPPING[tenant]
            if database != DEFAULT_DB_ALIAS:
                connection.close()
                connection.settings_dict["NAME"] = database
        label = f"tenant {tenant} (alias {alias})" if tenant else f"alias {alias}"
        if options["require_edition"]:
            product_id, edition_id = options["require_edition"]
            if not ProductEdition.objects.using(alias).filter(
                pk=edition_id, Product_Id_id=product_id, Is_Deleted=False,
            ).exists():
                raise CommandError(
                    f"Edition {edition_id} for product {product_id} was not found on {label}."
                )

        fields = {
            ModuleMaster: (
                "ProductCategory", "ProductCategory_id", "Product_Id",
                "Product_Edition_id", "ProductFeature_id",
            ),
            ProductFeature: ("ProductCategory_id", "Module_Id", "Edition_Ids"),
        }
        missing_fields = []
        with connection.cursor() as cursor:
            tables = set(connection.introspection.table_names(cursor))
            for model, names in fields.items():
                table = model._meta.db_table
                if table not in tables:
                    raise CommandError(f"Missing base table {table} on {label}.")
                columns = {
                    column.name for column in connection.introspection.get_table_description(cursor, table)
                }
                for name in names:
                    field = model._meta.get_field(name)
                    if field.many_to_many:
                        missing = field.remote_field.through._meta.db_table not in tables
                    else:
                        missing = field.column not in columns
                    if missing:
                        missing_fields.append((model, field))

        if options["check"]:
            if missing_fields:
                missing = ", ".join(f"{model.__name__}.{field.name}" for model, field in missing_fields)
                raise CommandError(f"Missing catalog schema on {label}: {missing}")
            self.stdout.write(self.style.SUCCESS(f"Catalog schema is ready on {label}."))
            return

        with connection.schema_editor() as editor:
            for model, field in missing_fields:
                editor.add_field(model, field)
                self.stdout.write(f"Added {model.__name__}.{field.name}")

        with transaction.atomic(using=alias):
            modules = ModuleMaster.objects.using(alias)
            features = ProductFeature.objects.using(alias)
            for module in modules.filter(Product_Id__isnull=True, Is_Deleted=False).iterator():
                products = set(module.Product_Edition_id.filter(
                    Is_Deleted=False, Product_Id__Is_Deleted=False,
                ).values_list("Product_Id_id", flat=True))
                if len(products) == 1:
                    modules.filter(pk=module.pk, Product_Id__isnull=True).update(Product_Id_id=products.pop())

            for feature in features.filter(
                Module_Id__isnull=True, Product_Id__isnull=False, Is_Deleted=False,
            ).iterator():
                matches = list(modules.filter(
                    ProductFeature_id=feature, Product_Id_id=feature.Product_Id_id, Is_Deleted=False,
                ).values_list("pk", flat=True)[:2])
                if len(matches) == 1:
                    features.filter(pk=feature.pk, Module_Id__isnull=True).update(Module_Id_id=matches[0])

        self.stdout.write(self.style.SUCCESS("Module and feature schema is ready."))
