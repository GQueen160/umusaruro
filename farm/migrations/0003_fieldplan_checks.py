from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("farm", "0002_fieldplan_holding"),
    ]

    operations = [
        migrations.AddField(
            model_name="fieldplan",
            name="checks",
            field=models.JSONField(blank=True, null=True),
        ),
    ]
