"""The tiny bus helper every Pony Express service shares.

One topic exchange, three queues:

    letter.posted          -> mailbag             (ponies take letters from here)
    letter.picked_up       -> postoffice.receipts (the postmaster tracks letters and ponies)
    letter.delivered       -> postoffice.receipts
    pony.ready             -> postoffice.receipts (a pony is at the post office, waiting for work)
    pony.retired           -> postoffice.receipts (a pony leaves the herd for good)
    #                      -> logbook             (sees everything: logging for free)
"""

import json
import logging
import os
import time

import pika

EXCHANGE = "pony-express"

MAILBAG = "mailbag"
RECEIPTS = "postoffice.receipts"
LOGBOOK = "logbook"

POSTED = "letter.posted"
PICKED_UP = "letter.picked_up"
DELIVERED = "letter.delivered"
PONY_READY = "pony.ready"
PONY_RETIRED = "pony.retired"

log = logging.getLogger("ponybus")


class BusUnavailable(Exception):
    """The message bus can't be reached (down, restarting, or its hostname doesn't resolve)."""


def connect(retries=30, delay=2):
    """Open a connection to the bus, waiting for it to come up if needed."""
    params = pika.URLParameters(
        os.environ.get("AMQP_URL", "amqp://pony:express@localhost:5672/%2F")
    )
    for attempt in range(1, retries + 1):
        try:
            connection = pika.BlockingConnection(params)
            channel = connection.channel()
            declare_topology(channel)
            return connection, channel
        # A stopped container's hostname stops resolving, which surfaces as an OSError.
        except (pika.exceptions.AMQPConnectionError, OSError) as error:
            if attempt == retries:
                raise BusUnavailable(str(error)) from error
            log.warning(
                "Message bus not reachable (attempt %s/%s), retrying in %ss",
                attempt,
                retries,
                delay,
            )
            time.sleep(delay)


def declare_topology(channel):
    """Declare exchange, queues and bindings. Idempotent, so every service just calls it."""
    channel.exchange_declare(EXCHANGE, exchange_type="topic", durable=True)
    channel.queue_declare(MAILBAG, durable=True)
    channel.queue_bind(MAILBAG, EXCHANGE, routing_key=POSTED)
    channel.queue_declare(RECEIPTS, durable=True)
    channel.queue_bind(RECEIPTS, EXCHANGE, routing_key=PICKED_UP)
    channel.queue_bind(RECEIPTS, EXCHANGE, routing_key=DELIVERED)
    channel.queue_bind(RECEIPTS, EXCHANGE, routing_key="pony.*")
    # The logbook is nice to have, so cap it instead of letting it grow forever.
    channel.queue_declare(LOGBOOK, durable=True, arguments={"x-max-length": 10_000})
    channel.queue_bind(LOGBOOK, EXCHANGE, routing_key="#")


def publish(channel, routing_key, payload):
    channel.basic_publish(
        EXCHANGE,
        routing_key,
        json.dumps(payload).encode(),
        pika.BasicProperties(
            content_type="application/json", delivery_mode=pika.DeliveryMode.Persistent
        ),
    )


def decode(body):
    return json.loads(body)


def queue_depth(channel, queue):
    return channel.queue_declare(queue, passive=True).method.message_count
