import uuid

from django.db import models
from django.utils import timezone


class Pony(models.Model):
    """What the post office knows about a pony: only what the receipts on the bus tell it."""

    class Status(models.TextChoices):
        AVAILABLE = "available", "Available"
        ON_THE_ROAD = "on_the_road", "On the road"
        MISSING = "missing", "Gone missing"

    name = models.CharField(max_length=100, unique=True)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.AVAILABLE
    )
    # Short id of the letter the pony is carrying, if any.
    letter = models.CharField(max_length=6, blank=True)
    since = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "ponies"

    def __str__(self):
        return f"{self.name} ({self.get_status_display()})"


class Letter(models.Model):
    class Status(models.TextChoices):
        QUEUED = "queued", "In the mailbag"
        PICKED_UP = "picked_up", "With a pony"
        DELIVERED = "delivered", "Delivered"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recipient = models.CharField(max_length=100)
    house = models.CharField(max_length=100)
    text = models.TextField()
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.QUEUED, db_index=True
    )
    # How many copies we've printed. Every reprint bumps it, so receipts can tell copies apart.
    attempt = models.PositiveIntegerField(default=1)
    pony = models.CharField(max_length=100, blank=True)
    # When the pony carrying the current copy has to be back with a receipt.
    deadline = models.DateTimeField(null=True, blank=True)
    # More than one means the house got duplicates. We don't mind.
    deliveries = models.PositiveIntegerField(default=0)
    # Demo switch: the pony carrying the first copy drops it, so only a reprint can arrive.
    lose_first_copy = models.BooleanField(default=False)
    posted_at = models.DateTimeField(auto_now_add=True)
    delivered_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-posted_at"]

    def __str__(self):
        return f"Letter {self.short_id} to {self.recipient}, {self.house}"

    @property
    def short_id(self):
        return str(self.id)[:6]

    def as_message(self):
        return {
            "letter_id": str(self.id),
            "attempt": self.attempt,
            "recipient": self.recipient,
            "house": self.house,
            "text": self.text,
            "drop": self.lose_first_copy and self.attempt == 1,
        }
