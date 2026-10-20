import logging
import random

import pika
from django.db import transaction
from django.db.models import Count, F, Q, Sum
from django.db.models.functions import Coalesce
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

import ponybus

from .models import Letter, Pony

log = logging.getLogger(__name__)

HOUSES = [
    "Buttercup Cottage",
    "The Old Stable",
    "Hayloft House",
    "Carrot Corner",
    "Meadow View",
    "Horseshoe Hall",
    "Saddle Row 3",
    "Clover Barn",
    "Paddock Place",
]
RECIPIENTS = [
    "Adrian",
    "Simon",
    "Jacob",
    "Ada",
    "Grace",
    "Guido",
    "Jeff",
    "Carlton",
    "Sarah",
]
TEXTS = [
    "Wish you were here!",
    "Your pull request was merged.",
    "Don't forget the meetup tonight.",
    "Thanks for the carrots.",
    "Have you tried turning it off and on again?",
    "The migrations are fine. Probably.",
    "See you at DjangoCon!",
    "Neigh-ver gonna give you up.",
]


def dashboard(request):
    return render(request, "letters/dashboard.html")


@require_POST
def post_letters(request):
    count = max(1, min(int(request.POST.get("count", 1)), 500))
    lose_first_copy = request.POST.get("lose_first_copy") == "1"
    letters = [
        Letter(
            recipient=random.choice(RECIPIENTS),
            house=random.choice(HOUSES),
            text=random.choice(TEXTS),
            lose_first_copy=lose_first_copy,
        )
        for _ in range(count)
    ]
    try:
        # If the bus is down, nothing gets posted: the transaction rolls back.
        with transaction.atomic():
            Letter.objects.bulk_create(letters)
            connection, channel = ponybus.connect(retries=1)
            try:
                for letter in letters:
                    ponybus.publish(channel, ponybus.POSTED, letter.as_message())
            finally:
                connection.close()
    except (ponybus.BusUnavailable, pika.exceptions.AMQPError):
        log.warning("Could not reach the message bus, nothing was posted")
        return JsonResponse(
            {"error": "The mailbag (message bus) is unreachable."}, status=503
        )
    return JsonResponse({"posted": count}, status=201)


def stats(request):
    by_status = dict(Letter.objects.values_list("status").annotate(n=Count("id")))
    totals = Letter.objects.aggregate(
        posted=Count("id"),
        reprints=Coalesce(Sum(F("attempt") - 1), 0),
        duplicates=Count("id", filter=Q(deliveries__gt=1)),
    )
    recent = [
        {
            "id": letter.short_id,
            "recipient": letter.recipient,
            "house": letter.house,
            "status": letter.status,
            "status_label": letter.get_status_display(),
            "copies": letter.attempt,
            "pony": letter.pony,
            "deliveries": letter.deliveries,
            "lose_first_copy": letter.lose_first_copy,
        }
        for letter in Letter.objects.all()[:14]
    ]
    ponies = [
        {
            "name": pony.name,
            "status": pony.status,
            "status_label": pony.get_status_display(),
            "letter": pony.letter,
        }
        for pony in Pony.objects.all()
    ]
    herd = {
        status: sum(pony["status"] == status for pony in ponies)
        for status in Pony.Status.values
    }
    return JsonResponse(
        {
            "mailbag": _mailbag_depth(),
            "queued": by_status.get(Letter.Status.QUEUED, 0),
            "picked_up": by_status.get(Letter.Status.PICKED_UP, 0),
            "delivered": by_status.get(Letter.Status.DELIVERED, 0),
            **totals,
            "recent": recent,
            "herd": herd,
            "ponies": ponies,
        }
    )


def health(request):
    return HttpResponse("ok")


def _mailbag_depth():
    """Ask the bus how many letters are waiting. None means the bus is unreachable."""
    try:
        connection, channel = ponybus.connect(retries=1)
    except ponybus.BusUnavailable:
        return None
    try:
        return ponybus.queue_depth(channel, ponybus.MAILBAG)
    finally:
        connection.close()
