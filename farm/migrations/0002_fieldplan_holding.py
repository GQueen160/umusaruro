from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("farm", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="fieldplan",
            name="holding",
            field=models.JSONField(blank=True, null=True),
        ),
    ]
