"""A magical pony: takes letters from the mailbag and carries them to the village.

Not every trip goes well. Some ponies get distracted and never come back, some stop
for a long snack. The post office doesn't care why: if there's no receipt in time,
it prints the letter again.
"""

import logging
import os
import random
import signal
import socket
import time

import pika
import requests

import ponybus

NAMES = [
    "Sparkle Hoof",
    "Thunder Mane",
    "Captain Oats",
    "Princess Pebble",
    "Sir Gallops",
    "Butterscotch",
    "Moonbeam",
    "Waffles",
    "Stardust",
    "Professor Neigh",
    "Django Unchained",
]

VILLAGE_URL = os.environ.get("VILLAGE_URL", "http://localhost:8002/api/deliveries/")
LOST_RATE = float(os.environ.get("LOST_RATE", 0.10))
LOST_SECONDS = float(os.environ.get("LOST_SECONDS", 20))
SLOW_RATE = float(os.environ.get("SLOW_RATE", 0.15))
SLOW_SECONDS = float(os.environ.get("SLOW_SECONDS", 12))
TRAVEL_MIN = float(os.environ.get("TRAVEL_MIN", 1))
TRAVEL_MAX = float(os.environ.get("TRAVEL_MAX", 3))

logging.basicConfig(level=logging.INFO, format="%(message)s")
logging.getLogger("pika").setLevel(logging.WARNING)
log = logging.getLogger("pony")


def deliver(pony, letter):
    """Carry one letter to its house. Returns True if it arrived."""
    trip = f"letter {letter['letter_id'][:6]} (copy {letter['attempt']}) for {letter['house']}"
    roll = random.random()
    # "drop" is the post office's demo switch: this copy is lost no matter what.
    if letter.get("drop") or roll < LOST_RATE:
        log.info("%s got distracted by a rainbow and lost %s.", pony, trip)
        time.sleep(LOST_SECONDS)
        log.info("%s found its way back to the post office.", pony)
        return False

    travel = random.uniform(TRAVEL_MIN, TRAVEL_MAX)
    if roll < LOST_RATE + SLOW_RATE:
        log.info("%s stopped for a long snack on the way with %s.", pony, trip)
        travel += SLOW_SECONDS
    time.sleep(travel)

    try:
        requests.post(
            VILLAGE_URL, json={**letter, "pony": pony}, timeout=5
        ).raise_for_status()
    except requests.RequestException:
        log.info("%s found nobody home in the village and dropped %s.", pony, trip)
        return False
    log.info("%s delivered %s.", pony, trip)
    return True


def main():
    # Seeded by the container's hostname, so a pony keeps its name when its container restarts.
    rng = random.Random(socket.gethostname())
    pony = f"{rng.choice(NAMES)} #{rng.randint(10, 99)}"
    # docker compose stop sends SIGTERM: leave through the finally block below and say goodbye.
    signal.signal(signal.SIGTERM, _retire)

    connection, channel = ponybus.connect()
    # One letter at a time per pony, so a bigger herd means more letters in flight.
    channel.basic_qos(prefetch_count=1)
    ponybus.publish(channel, ponybus.PONY_READY, {"pony": pony})
    log.info("%s is ready for duty.", pony)

    try:
        for method, properties, body in channel.consume(ponybus.MAILBAG):
            letter = ponybus.decode(body)
            # The letter is ours now. If we never come back, the post office prints it again.
            channel.basic_ack(method.delivery_tag)
            ponybus.publish(
                channel, ponybus.PICKED_UP, {**_receipt(letter), "pony": pony}
            )
            if deliver(pony, letter):
                ponybus.publish(
                    channel,
                    ponybus.DELIVERED,
                    {**_receipt(letter), "pony": pony, "house": letter["house"]},
                )
            ponybus.publish(channel, ponybus.PONY_READY, {"pony": pony})
    finally:
        try:
            ponybus.publish(channel, ponybus.PONY_RETIRED, {"pony": pony})
            connection.close()
            log.info("%s retired from the herd.", pony)
        except (pika.exceptions.AMQPError, OSError):
            # The bus is already gone, so there's nobody to say goodbye to.
            pass


def _receipt(letter):
    return {"letter_id": letter["letter_id"], "attempt": letter["attempt"]}


def _retire(signum, frame):
    raise SystemExit(0)


if __name__ == "__main__":
    main()
