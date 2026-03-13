"""
Simulasi publisher MQTT untuk testing dashboard.
Jalankan: python tools/simulate.py
Butuh: pip install paho-mqtt
"""
import json
import random
import time
import paho.mqtt.client as mqtt

BROKER = "localhost"
PORT   = 1883

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.connect(BROKER, PORT)
client.loop_start()

print("Simulasi sensor dimulai. Ctrl+C untuk berhenti.\n")

pt100_base  = 75.0
dht22_temp  = 26.0
dht22_hum   = 55.0
gy906_obj   = 36.5
gy906_amb   = 25.0

try:
    while True:
        # PT100 — suhu industri (misal furnace)
        pt100_base += random.uniform(-0.5, 0.5)
        pt100_base = max(60.0, min(90.0, pt100_base))
        client.publish("sensors/pt100", json.dumps({"temperature": round(pt100_base, 2)}))

        # DHT22 — suhu & kelembaban ruangan
        dht22_temp += random.uniform(-0.3, 0.3)
        dht22_hum  += random.uniform(-1.0, 1.0)
        dht22_temp = max(20.0, min(35.0, dht22_temp))
        dht22_hum  = max(30.0, min(80.0, dht22_hum))
        client.publish("sensors/dht22", json.dumps({
            "temperature": round(dht22_temp, 2),
            "humidity":    round(dht22_hum,  2),
        }))

        # GY906 — suhu IR
        gy906_obj += random.uniform(-0.4, 0.4)
        gy906_amb += random.uniform(-0.1, 0.1)
        gy906_obj = max(34.0, min(40.0, gy906_obj))
        gy906_amb = max(22.0, min(28.0, gy906_amb))
        client.publish("sensors/gy906", json.dumps({
            "object_temp":  round(gy906_obj, 2),
            "ambient_temp": round(gy906_amb, 2),
        }))

        print(f"PT100: {pt100_base:.2f}°C | "
              f"DHT22: {dht22_temp:.2f}°C {dht22_hum:.1f}% | "
              f"GY906 obj:{gy906_obj:.2f}°C amb:{gy906_amb:.2f}°C")

        time.sleep(2)

except KeyboardInterrupt:
    print("\nSimulasi dihentikan.")
    client.loop_stop()
    client.disconnect()
