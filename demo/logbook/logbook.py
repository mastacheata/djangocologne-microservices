"""The logbook subscribes to every topic on the bus. Nobody else had to change for it to exist."""

import logging
from datetime import datetime

import ponybus

logging.basicConfig(level=logging.INFO, format="%(message)s")
logging.getLogger("pika").setLevel(logging.WARNING)


def describe(routing_key, message):
    if "letter_id" not in message:
        return message.get("pony", "?")
    letter = f"{message['letter_id'][:6]} copy {message['attempt']}"
    if routing_key == ponybus.POSTED:
        return f"{letter} → {message['house']}"
    return f"{letter} · {message.get('pony', '?')}"


def main():
    connection, channel = ponybus.connect()
    print("Logbook open. Every message on the bus ends up here.", flush=True)
    for method, properties, body in channel.consume(ponybus.LOGBOOK):
        message = ponybus.decode(body)
        print(
            f"{datetime.now():%H:%M:%S}  {method.routing_key:<17} {describe(method.routing_key, message)}",
            flush=True,
        )
        channel.basic_ack(method.delivery_tag)


if __name__ == "__main__":
    main()
