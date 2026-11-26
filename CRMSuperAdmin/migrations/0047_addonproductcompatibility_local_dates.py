from django.db import migrations, models
from django.utils import timezone


class Migration(migrations.Migration):
    dependencies = [('CRMSuperAdmin', '0046_addonproductcompatibility_rule_details')]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.AlterField(
                    model_name='addonproductcompatibility',
                    name='Created_Date',
                    field=models.DateField(default=timezone.localdate),
                ),
                migrations.AlterField(
                    model_name='addonproductcompatibility',
                    name='Updated_Date',
                    field=models.DateField(default=timezone.localdate),
                ),
            ],
        ),
    ]
