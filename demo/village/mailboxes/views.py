import json

from django.db.models import Count
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models import Delivery


def village(request):
    return render(request, "mailboxes/village.html")


@csrf_exempt
@require_POST
def receive(request):
    """A pony drops a letter into a mailbox. We accept every copy; duplicates are fine."""
    data = json.loads(request.body)
    delivery = Delivery.objects.create(
        letter_id=data["letter_id"],
        attempt=data["attempt"],
        house=data["house"],
        recipient=data["recipient"],
        text=data["text"],
        pony=data["pony"],
    )
    return JsonResponse({"id": delivery.pk}, status=201)


def summary(request):
    houses = [
        {**house, "duplicates": house["deliveries"] - house["letters"]}
        for house in Delivery.objects.values("house")
        .annotate(deliveries=Count("id"), letters=Count("letter_id", distinct=True))
        .order_by("house")
    ]
    recent = [
        {
            "id": str(delivery.letter_id)[:6],
            "house": delivery.house,
            "recipient": delivery.recipient,
            "text": delivery.text,
            "pony": delivery.pony,
            "copy": delivery.attempt,
            "repeat": Delivery.objects.filter(
                letter_id=delivery.letter_id, delivered_at__lt=delivery.delivered_at
            ).exists(),
        }
        for delivery in Delivery.objects.all()[:12]
    ]
    deliveries = Delivery.objects.count()
    letters = Delivery.objects.values("letter_id").distinct().count()
    return JsonResponse(
        {
            "deliveries": deliveries,
            "letters": letters,
            "duplicates": deliveries - letters,
            "houses": houses,
            "recent": recent,
        }
    )
