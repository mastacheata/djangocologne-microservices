from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("letters", "0002_pony"),
    ]

    operations = [
        migrations.AddField(
            model_name="letter",
            name="lose_first_copy",
            field=models.BooleanField(default=False),
        ),
    ]
