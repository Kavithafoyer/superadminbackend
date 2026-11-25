from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('CRMSuperAdmin', '0043_addonmaster_addon_category_addonpricing_addon_name_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='addonmaster',
            name='Minimum_Core_API_Version',
            field=models.CharField(blank=True, default='', max_length=100),
        ),
        migrations.AddField(
            model_name='addonmaster',
            name='Known_Incompatibilities',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AddField(
            model_name='addonmaster',
            name='Release_Version',
            field=models.CharField(blank=True, default='', max_length=100),
        ),
        migrations.AddField(
            model_name='addonmaster',
            name='Release_Status',
            field=models.CharField(blank=True, default='', max_length=100),
        ),
        migrations.AddField(
            model_name='addonmaster',
            name='Release_Notes',
            field=models.TextField(blank=True, default=''),
        ),
    ]
