from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('CRMSuperAdmin', '0044_addonmaster_compatibility_and_release'),
    ]

    operations = [
        migrations.AddField(
            model_name='addonmaster',
            name='License_Model',
            field=models.CharField(
                choices=[('Per Tenant', 'Per Tenant'), ('Per User', 'Per User'),
                         ('Usage Based', 'Usage Based'), ('Tiered Volume', 'Tiered Volume')],
                default='Per Tenant',
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='addonmaster',
            name='Trial_Available',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='addonmaster',
            name='Trial_Days',
            field=models.PositiveIntegerField(default=0),
        ),
    ]
