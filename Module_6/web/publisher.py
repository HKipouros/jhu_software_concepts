import os
import pika
import json
from datetime import datetime

EXCHANGE = "tasks"
QUEUE = "tasks_q"
ROUTING_KEY = "scrape_new_data"

def _open_channel():
    url = os.environ["RABBITMQ_URL"]
    params = pika.URLParameters(url)
    conn = pika.BlockingConnection(params)
    ch = conn.channel()

    # Durable exchange & queue; bind once per process (idempotent)
    ch.exchange_declare(exchange=EXCHANGE, exchange_type="direct", durable=True)
    ch.queue_declare(queue=QUEUE, durable=True)
    ch.queue_bind(exchange=EXCHANGE, queue=QUEUE, routing_key=ROUTING_KEY)
    return conn, ch

def publish_task(kind: str, payload: dict | None = None, headers: dict | None =
None):
    body = json.dumps(
        {"kind": kind, "ts": datetime.utcnow().isoformat(), "payload": payload or {}},
        separators=(",", ":")
        ).encode("utf-8")
    conn, ch = _open_channel()
    try:
        ch.basic_publish(
        exchange=EXCHANGE,
        routing_key=ROUTING_KEY,
        body=body,
        properties=pika.BasicProperties(delivery_mode=2, headers=headers or {}),
        mandatory=False,
        )

# If using confirms:
# if not ch.wait_for_confirms():
# raise RuntimeError("Publish not confirmed")
    finally:
        conn.close()