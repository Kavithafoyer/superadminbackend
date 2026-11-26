from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('CRMSuperAdmin', '0045_sync_existing_schema_state')]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.AddField(model_name='addonproductcompatibility', name='Compatibility_Type', field=models.CharField(max_length=20, blank=True, default='', choices=[('compatible', 'Compatible'), ('incompatible', 'Not compatible'), ('dependency', 'Requires dependency')])),
                migrations.AddField(model_name='addonproductcompatibility', name='Dependencies', field=models.JSONField(default=list, blank=True)),
                migrations.AddField(model_name='addonproductcompatibility', name='Version_Constraint', field=models.BooleanField(default=False)),
                migrations.AddField(model_name='addonproductcompatibility', name='Minimum_Version', field=models.CharField(max_length=100, blank=True, default='')),
                migrations.AddField(model_name='addonproductcompatibility', name='Maximum_Version', field=models.CharField(max_length=100, blank=True, default='')),
                migrations.AddField(model_name='addonproductcompatibility', name='Rule_Description', field=models.TextField(blank=True, default='')),
            ],
        ),
    ]
