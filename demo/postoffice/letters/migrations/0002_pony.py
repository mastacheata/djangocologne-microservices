import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("letters", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Pony",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=100, unique=True)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("available", "Available"),
                            ("on_the_road", "On the road"),
                            ("missing", "Gone missing"),
                        ],
                        default="available",
                        max_length=20,
                    ),
                ),
                ("letter", models.CharField(blank=True, max_length=6)),
                ("since", models.DateTimeField(default=django.utils.timezone.now)),
            ],
            options={"ordering": ["name"], "verbose_name_plural": "ponies"},
        ),
    ]
