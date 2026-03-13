#!/bin/bash

BROKER="localhost"
PORT="1883"

# Cek mosquitto_pub tersedia
if ! command -v mosquitto_pub &> /dev/null; then
  echo "ERROR: mosquitto_pub tidak ditemukan."
  echo "Install dulu: brew install mosquitto  atau  apt install mosquitto-clients"
  exit 1
fi

pub() {
  mosquitto_pub -h "$BROKER" -p "$PORT" -t "$1" -m "$2"
}

echo "============================================"
echo "  IoT Sensor MQTT Testing"
echo "  Broker: $BROKER:$PORT"
echo "============================================"

# ── PT100 ─────────────────────────────────────
echo ""
echo "[PT100] Mengirim 5 data suhu..."
for i in 1 2 3 4 5; do
  TEMP=$(awk -v min=70 -v max=85 'BEGIN{srand(); printf "%.2f", min+rand()*(max-min)}')
  echo "  → sensors/pt100  temperature=$TEMP°C"
  pub "sensors/pt100" "{\"temperature\": $TEMP}"
  sleep 1
done

# ── DHT22 ─────────────────────────────────────
echo ""
echo "[DHT22] Mengirim 5 data suhu + kelembaban..."
for i in 1 2 3 4 5; do
  TEMP=$(awk -v min=24 -v max=32 'BEGIN{srand('$RANDOM'); printf "%.2f", min+rand()*(max-min)}')
  HUM=$(awk  -v min=40 -v max=75 'BEGIN{srand('$RANDOM'); printf "%.2f", min+rand()*(max-min)}')
  echo "  → sensors/dht22  temperature=$TEMP°C  humidity=$HUM%"
  pub "sensors/dht22" "{\"temperature\": $TEMP, \"humidity\": $HUM}"
  sleep 1
done

# ── GY906 ─────────────────────────────────────
echo ""
echo "[GY906] Mengirim 5 data suhu IR..."
for i in 1 2 3 4 5; do
  OBJ=$(awk -v min=35 -v max=39 'BEGIN{srand('$RANDOM'); printf "%.2f", min+rand()*(max-min)}')
  AMB=$(awk -v min=23 -v max=27 'BEGIN{srand('$RANDOM'); printf "%.2f", min+rand()*(max-min)}')
  echo "  → sensors/gy906  object_temp=$OBJ°C  ambient_temp=$AMB°C"
  pub "sensors/gy906" "{\"object_temp\": $OBJ, \"ambient_temp\": $AMB}"
  sleep 1
done

echo ""
echo "============================================"
echo "  Selesai! Cek dashboard di http://localhost"
echo "============================================"
