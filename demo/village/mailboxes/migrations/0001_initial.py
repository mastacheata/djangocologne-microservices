from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Delivery",
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
                ("letter_id", models.UUIDField(db_index=True)),
                ("attempt", models.PositiveIntegerField()),
                ("house", models.CharField(db_index=True, max_length=100)),
                ("recipient", models.CharField(max_length=100)),
                ("text", models.TextField()),
                ("pony", models.CharField(max_length=100)),
                ("delivered_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "ordering": ["-delivered_at"],
                "verbose_name_plural": "deliveries",
            },
        ),
    ]
