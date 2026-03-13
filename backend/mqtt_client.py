import json
import logging
import os
import time
import threading
import paho.mqtt.client as mqtt
from database import SessionLocal
from models import PT100Reading, DHT22Reading, GY906Reading

logger = logging.getLogger(__name__)

MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))

TOPICS = {
    "sensors/pt100": "pt100",
    "sensors/dht22": "dht22",
    "sensors/gy906": "gy906",
}

# Callback registry for WebSocket broadcast
_ws_callbacks: list = []


def register_ws_callback(cb):
    _ws_callbacks.append(cb)


def _broadcast(sensor: str, data: dict):
    for cb in list(_ws_callbacks):
        try:
            cb(sensor, data)
        except Exception:
            pass


def _save_pt100(payload: dict):
    db = SessionLocal()
    try:
        reading = PT100Reading(temperature=payload["temperature"])
        db.add(reading)
        db.commit()
        db.refresh(reading)
        _broadcast("pt100", {
            "temperature": float(reading.temperature),
            "created_at": reading.created_at.isoformat(),
        })
    except Exception as e:
        logger.error(f"PT100 DB error: {e}")
        db.rollback()
    finally:
        db.close()


def _save_dht22(payload: dict):
    db = SessionLocal()
    try:
        reading = DHT22Reading(
            temperature=payload["temperature"],
            humidity=payload["humidity"],
        )
        db.add(reading)
        db.commit()
        db.refresh(reading)
        _broadcast("dht22", {
            "temperature": float(reading.temperature),
            "humidity": float(reading.humidity),
            "created_at": reading.created_at.isoformat(),
        })
    except Exception as e:
        logger.error(f"DHT22 DB error: {e}")
        db.rollback()
    finally:
        db.close()


def _save_gy906(payload: dict):
    db = SessionLocal()
    try:
        reading = GY906Reading(
            object_temp=payload["object_temp"],
            ambient_temp=payload["ambient_temp"],
        )
        db.add(reading)
        db.commit()
        db.refresh(reading)
        _broadcast("gy906", {
            "object_temp": float(reading.object_temp),
            "ambient_temp": float(reading.ambient_temp),
            "created_at": reading.created_at.isoformat(),
        })
    except Exception as e:
        logger.error(f"GY906 DB error: {e}")
        db.rollback()
    finally:
        db.close()


_HANDLERS = {
    "pt100": _save_pt100,
    "dht22": _save_dht22,
    "gy906": _save_gy906,
}


def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        logger.info("MQTT connected")
        for topic in TOPICS:
            client.subscribe(topic)
            logger.info(f"Subscribed to {topic}")
    else:
        logger.error(f"MQTT connect failed: {reason_code}")


def on_message(client, userdata, msg):
    topic = msg.topic
    sensor = TOPICS.get(topic)
    if not sensor:
        return
    try:
        payload = json.loads(msg.payload.decode())
        logger.info(f"[{sensor}] {payload}")
        _HANDLERS[sensor](payload)
    except Exception as e:
        logger.error(f"Message error on {topic}: {e}")


def start_mqtt():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect = on_connect
    client.on_message = on_message

    while True:
        try:
            client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
            client.loop_forever()
        except Exception as e:
            logger.error(f"MQTT connection error: {e}. Retrying in 5s...")
            time.sleep(5)


def start_mqtt_thread():
    t = threading.Thread(target=start_mqtt, daemon=True)
    t.start()
    return t
