from django.db import migrations, models

from CRMSuperAdmin.models import (
    AddonCategory_I,
    AddonDiscountCoupon_I,
    AddonPriceHistory_I,
    AddonPriceTemplate_I,
    AddonPricing_I,
    AddonProductCompatibility_I,
    AddonTieredPricing_I,
)


IDENTIFIERS = (
    ('addoncategory', 'AddonCategory_Id', 'ACI', AddonCategory_I),
    ('addondiscountcoupon', 'AddonDiscountCoupon_Id', 'ADC', AddonDiscountCoupon_I),
    ('addonpricehistory', 'AddonPriceHistory_Id', 'APH', AddonPriceHistory_I),
    ('addonpricetemplate', 'AddonPriceTemplate_Id', 'APT', AddonPriceTemplate_I),
    ('addonpricing', 'AddonPricing_Id', 'API', AddonPricing_I),
    ('addonproductcompatibility', 'AddonProductCompatibility_Id', 'APC', AddonProductCompatibility_I),
    ('addontieredpricing', 'AddonTieredPricing_Id', 'ATPS', AddonTieredPricing_I),
)


def populate_identifiers(apps, schema_editor):
    alias = schema_editor.connection.alias
    for model_name, field_name, prefix, _ in IDENTIFIERS:
        model = apps.get_model('CRMSuperAdmin', model_name)
        rows = model.objects.using(alias).order_by('pk')
        for number, pk in enumerate(rows.values_list('pk', flat=True).iterator(), start=1):
            rows.filter(pk=pk).update(**{field_name: f'{prefix}{number:09d}'})


class Migration(migrations.Migration):
    dependencies = [
        ('CRMSuperAdmin', '0038_alter_accounthistory_updated_time_and_more'),
    ]

    operations = [
        migrations.AddField(model_name, field_name, models.CharField(max_length=50, null=True))
        for model_name, field_name, _, _ in IDENTIFIERS
    ] + [
        migrations.RunPython(populate_identifiers, migrations.RunPython.noop),
    ] + [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.AlterField(model_name, field_name, models.CharField(max_length=50, unique=True)),
            ],
            state_operations=[
                migrations.AlterField(
                    model_name, field_name, models.CharField(max_length=50, unique=True, default=default),
                ),
            ],
        )
        for model_name, field_name, _, default in IDENTIFIERS
    ]
