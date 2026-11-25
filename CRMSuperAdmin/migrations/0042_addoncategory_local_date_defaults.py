from django.db import migrations, models
from django.utils import timezone


class Migration(migrations.Migration):
    dependencies = [
        ('CRMSuperAdmin', '0041_addonproductcompatibility_addon_name_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='addoncategory',
            name='Created_Date',
            field=models.DateField(default=timezone.localdate),
        ),
        migrations.AlterField(
            model_name='addoncategory',
            name='Updated_Date',
            field=models.DateField(default=timezone.localdate),
        ),
    ]
