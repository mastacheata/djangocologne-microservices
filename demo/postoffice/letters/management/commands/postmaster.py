from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.models import F
from django.utils import timezone

import ponybus
from letters.models import Letter, Pony


class Command(BaseCommand):
    help = "Reads pony receipts from the bus, keeps track of the herd and reprints letters whose pony didn't come back in time."

    def handle(self, *args, **options):
        connection, self.channel = ponybus.connect()
        self.channel.basic_qos(prefetch_count=50)
        self.channel.basic_consume(ponybus.RECEIPTS, self.on_receipt)
        self.stdout.write(
            f"Postmaster on duty. Ponies have {settings.DELIVERY_TIMEOUT:g}s to come back."
        )
        try:
            while True:
                # Handle receipts for up to a second, then look for ponies that are overdue.
                connection.process_data_events(time_limit=1)
                self.reprint_overdue()
                self.forget_lost_ponies()
        except KeyboardInterrupt:
            connection.close()

    def on_receipt(self, channel, method, properties, body):
        receipt = ponybus.decode(body)
        if method.routing_key == ponybus.PICKED_UP:
            self.picked_up(receipt)
        elif method.routing_key == ponybus.DELIVERED:
            self.delivered(receipt)
        elif method.routing_key == ponybus.PONY_READY:
            self.set_pony(receipt["pony"], Pony.Status.AVAILABLE)
        elif method.routing_key == ponybus.PONY_RETIRED:
            Pony.objects.filter(name=receipt["pony"]).delete()
        channel.basic_ack(method.delivery_tag)

    def set_pony(self, name, status, letter=""):
        # Any sign of life (re)adopts a pony, including one we gave up on earlier.
        _, created = Pony.objects.update_or_create(
            name=name,
            defaults={"status": status, "letter": letter, "since": timezone.now()},
        )
        if created:
            self.stdout.write(f"{name} joined the herd.")

    def picked_up(self, receipt):
        self.set_pony(
            receipt["pony"], Pony.Status.ON_THE_ROAD, letter=receipt["letter_id"][:6]
        )
        # Only the current copy starts the clock. A late receipt for an old copy changes nothing.
        Letter.objects.filter(
            id=receipt["letter_id"],
            attempt=receipt["attempt"],
            status=Letter.Status.QUEUED,
        ).update(
            status=Letter.Status.PICKED_UP,
            pony=receipt["pony"],
            deadline=timezone.now() + timedelta(seconds=settings.DELIVERY_TIMEOUT),
        )

    def delivered(self, receipt):
        # Any copy counts, even one a slow pony brings in after we reprinted it.
        letters = Letter.objects.filter(id=receipt["letter_id"])
        letters.update(deliveries=F("deliveries") + 1)
        updated = letters.exclude(status=Letter.Status.DELIVERED).update(
            status=Letter.Status.DELIVERED,
            pony=receipt["pony"],
            delivered_at=timezone.now(),
            deadline=None,
        )
        if not updated:
            self.stdout.write(
                f"Letter {receipt['letter_id'][:6]} arrived again (copy {receipt['attempt']}). No harm done."
            )

    def reprint_overdue(self):
        overdue = Letter.objects.filter(
            status=Letter.Status.PICKED_UP, deadline__lt=timezone.now()
        )
        for letter in overdue:
            self.stdout.write(
                self.style.WARNING(
                    f"{letter.pony} isn't back with letter {letter.short_id}. Printing copy {letter.attempt + 1}."
                )
            )
            # Only if that pony is still out with this letter. It may have come back without it.
            Pony.objects.filter(
                name=letter.pony, status=Pony.Status.ON_THE_ROAD, letter=letter.short_id
            ).update(status=Pony.Status.MISSING, since=timezone.now())
            letter.attempt += 1
            letter.status = Letter.Status.QUEUED
            letter.pony = ""
            letter.deadline = None
            letter.save(update_fields=["attempt", "status", "pony", "deadline"])
            ponybus.publish(self.channel, ponybus.POSTED, letter.as_message())

    def forget_lost_ponies(self):
        # A pony that left without saying goodbye (killed, crashed) would stay "missing" forever.
        cutoff = timezone.now() - timedelta(seconds=settings.PONY_FORGET_AFTER)
        lost = Pony.objects.filter(status=Pony.Status.MISSING, since__lt=cutoff)
        for pony in lost:
            self.stdout.write(
                self.style.WARNING(
                    f"{pony.name} has been missing for over {settings.PONY_FORGET_AFTER:g}s. Struck off the list."
                )
            )
        lost.delete()
