from django.db import models


class Delivery(models.Model):
    """One letter dropped into one mailbox. The same letter can arrive more than once."""

    letter_id = models.UUIDField(db_index=True)
    attempt = models.PositiveIntegerField()
    house = models.CharField(max_length=100, db_index=True)
    recipient = models.CharField(max_length=100)
    text = models.TextField()
    pony = models.CharField(max_length=100)
    delivered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-delivered_at"]
        verbose_name_plural = "deliveries"

    def __str__(self):
        return f"{str(self.letter_id)[:6]} to {self.house} by {self.pony}"
