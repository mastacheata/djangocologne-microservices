# Pony Express 🐴✉️

A herd of small services delivering mail by magical pony. Demo for the talk *From Pony to Herd: Microservices with Django*.

Letters pile up at the post office and go into a mailbag (a queue on the message bus). Ponies take them one at a time and
carry them to the village. Some ponies get lost, some are slow. If a pony isn't back with a receipt in time, the
postmaster prints the letter again and puts the copy back into the mailbag. Duplicates are fine, as long as every letter
eventually arrives (*at-least-once delivery*).

```
            letter.posted                         HTTP POST
 postoffice ─────────────► [ mailbag ] ─► pony ×N ─────────► village
 (Django)                                   │                (Django)
     ▲                                      │ letter.picked_up · letter.delivered
     │        [ postoffice.receipts ] ◄─────┘ pony.ready · pony.retired
 postmaster ◄──────┘
 (tracks the herd, reprints overdue letters)

 logbook ◄── [ logbook ] ◄── # (every message on the bus)
```

| Service | What it is | Owns |
|---|---|---|
| `postoffice` | Django. Post letters, watch them travel. <http://localhost:8001> | `postoffice.sqlite3` |
| `postmaster` | Same Django project, `manage.py postmaster`. Reads receipts, reprints overdue letters. | shares the post office DB |
| `pony` | Plain Python worker. Scale it. | nothing |
| `village` | Django. The mailboxes, with duplicates. <http://localhost:8002> | `village.sqlite3` |
| `logbook` | Plain Python. Subscribes to `#` and prints everything. | nothing |
| `rabbitmq` | The bus. Management UI: <http://localhost:15672> (`pony` / `express`) | the queues |

`shared/ponybus.py` is the only shared code: the exchange, queue names and a few helpers on top of `pika`.

## Run it

```sh
docker compose up --build -d
```

Open the post office, the village and the RabbitMQ *Queues* tab side by side.

> **431 Request Header Fields Too Large** in the RabbitMQ UI? That's your browser sending every cookie it has for
> `localhost`. `rabbitmq/advanced.config` raises the header limit; alternatively open <http://127.0.0.1:15672>.

Reset everything between rehearsals:

```sh
docker compose down -v && docker compose up -d
```

## Knobs

Set in `docker-compose.yml`:

| Variable | Service | Default | Meaning |
|---|---|---|---|
| `DELIVERY_TIMEOUT` | postoffice, postmaster | `8` | Seconds a pony has to come back before the letter is reprinted |
| `PONY_FORGET_AFTER` | postmaster | `60` | Seconds a pony can be missing before it's struck off the list (it's re-adopted if it shows up again) |
| `LOST_RATE` | pony | `0.10` | Share of trips where the pony loses the letter and wanders off |
| `LOST_SECONDS` | pony | `20` | How long a lost pony needs to find its way back |
| `SLOW_RATE` | pony | `0.15` | Share of trips with a long snack break |
| `SLOW_SECONDS` | pony | `12` | Length of the snack break (longer than the timeout, so it causes a reprint) |
| `TRAVEL_MIN` / `TRAVEL_MAX` | pony | `1` / `3` | Normal travel time in seconds |

## Demo script

1. **Happy path.** Post 10 letters. Letters go *In the mailbag → With a pony → Delivered*. A few get reprinted, and some
   houses in the village get a duplicate. That's fine. The herd box shows each pony as *available*, *on the road* or
   *gone missing* (its letter is overdue). Missing ponies turn up again a little later.
   **Lost on purpose:** *Post a letter the pony will lose*. The first copy is always dropped: the pony goes
   missing, the postmaster prints copy 2 after the timeout, and only copy 2 arrives in the village.
2. **Logging for free.** `docker compose logs -f logbook`. Nobody else had to change for the logbook to exist.
3. **A burst.** Post 100. The mailbag in RabbitMQ grows, because three ponies can't keep up.
   Grow the herd: `docker compose up -d --scale pony=10`. New ponies report for duty in the herd box and the queue
   drains. Scaling back down retires ponies: they say goodbye on the bus before they leave.
4. **The village is closed.** `docker compose stop village`, post 10. Ponies find nobody home, the postmaster keeps
   reprinting. `docker compose start village`: everything arrives, nothing is lost.
5. **No ponies at all.** `docker compose stop pony`, post 10. The letters just wait in the mailbag.
   `docker compose start pony` and they go out.
6. **The postmaster takes a break.** `docker compose stop postmaster`. Ponies keep delivering, the receipts queue grows
   in RabbitMQ. `docker compose start postmaster`: it catches up with every receipt.
7. **The bus is down.** `docker compose stop rabbitmq`, then try to post: the post office refuses, because there's no
   mailbag to put letters in. Nothing that was already in the mailbag is lost: the queues are durable.
   `docker compose start rabbitmq`: the workers crash, restart and reconnect on their own (`restart: unless-stopped`).
