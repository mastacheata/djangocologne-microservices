import uuid

from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Letter",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("recipient", models.CharField(max_length=100)),
                ("house", models.CharField(max_length=100)),
                ("text", models.TextField()),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("queued", "In the mailbag"),
                            ("picked_up", "With a pony"),
                            ("delivered", "Delivered"),
                        ],
                        db_index=True,
                        default="queued",
                        max_length=20,
                    ),
                ),
                ("attempt", models.PositiveIntegerField(default=1)),
                ("pony", models.CharField(blank=True, max_length=100)),
                ("deadline", models.DateTimeField(blank=True, null=True)),
                ("deliveries", models.PositiveIntegerField(default=0)),
                ("posted_at", models.DateTimeField(auto_now_add=True)),
                ("delivered_at", models.DateTimeField(blank=True, null=True)),
            ],
            options={"ordering": ["-posted_at"]},
        ),
    ]
