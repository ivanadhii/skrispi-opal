# IoT Sensor Dashboard

Real-time dashboard untuk monitoring data tiga sensor IoT melalui protokol MQTT. Data dari sensor dikirim ke broker EMQX, disimpan ke PostgreSQL, dan ditampilkan secara live di browser menggunakan WebSocket.

---

## Arsitektur Sistem

```
  [ Sensor / Simulator ]
          │
          │  MQTT Publish
          ▼
  ┌───────────────┐
  │  EMQX Broker  │  :1883 (MQTT)  :18083 (Dashboard)
  └───────┬───────┘
          │  Subscribe
          ▼
  ┌───────────────┐       ┌──────────────────┐
  │    Backend    │──────▶│   PostgreSQL DB   │
  │   (FastAPI)   │       │    :5432          │
  └───────┬───────┘       └──────────────────┘
          │  WebSocket / REST API
          ▼
  ┌───────────────┐
  │   Frontend    │  :80
  │  (HTML/CSS)   │
  └───────────────┘
```

**4 container Docker:**

| Container  | Image                | Port         | Fungsi                          |
|------------|----------------------|--------------|---------------------------------|
| `emqx`     | emqx:5.8             | 1883, 18083  | MQTT broker                     |
| `postgres` | postgres:16-alpine   | 5432         | Penyimpanan time-series data    |
| `backend`  | python:3.12 (custom) | 8000         | API + MQTT subscriber           |
| `frontend` | nginx:alpine (custom)| 80           | Dashboard HTML                  |

---

## Tech Stack

### Backend
| Library        | Versi   | Fungsi                                    |
|----------------|---------|-------------------------------------------|
| FastAPI        | 0.115.6 | REST API + WebSocket server               |
| Uvicorn        | 0.34.0  | ASGI server                               |
| paho-mqtt      | 2.1.0   | MQTT client untuk subscribe ke EMQX       |
| SQLAlchemy     | 2.0.36  | ORM untuk PostgreSQL                      |
| psycopg2       | 2.9.10  | PostgreSQL driver                         |
| python-dotenv  | 1.0.1   | Manajemen environment variable            |

### Frontend
| Library    | Versi  | Fungsi                        |
|------------|--------|-------------------------------|
| Chart.js   | 4.4.4  | Rendering grafik time-series  |
| Vanilla JS | —      | WebSocket client, DOM update  |
| Nginx      | alpine | Static file server            |

### Infrastruktur
- **EMQX 5.8** — MQTT broker enterprise-grade, support MQTT 5.0
- **PostgreSQL 16** — database relasional dengan index `DESC` untuk query time-series
- **Docker Compose** — orkestrasi semua container

---

## Sensor yang Didukung

### PT100 — RTD Temperature Sensor
- Tipe: Resistance Temperature Detector
- Output: Suhu (°C)
- MQTT Topic: `sensors/pt100`
- Payload:
  ```json
  { "temperature": 75.42 }
  ```

### DHT22 — Temperature & Humidity Sensor
- Tipe: Digital capacitive sensor
- Output: Suhu (°C) + Kelembaban relatif (%)
- MQTT Topic: `sensors/dht22`
- Payload:
  ```json
  { "temperature": 28.50, "humidity": 62.30 }
  ```

### GY-906 — IR Non-Contact Temperature (MLX90614)
- Tipe: Infrared thermometer
- Output: Suhu objek (°C) + Suhu ambient (°C)
- MQTT Topic: `sensors/gy906`
- Payload:
  ```json
  { "object_temp": 36.80, "ambient_temp": 25.10 }
  ```

---

## Struktur Project

```
skripsi-opal/
├── docker-compose.yml
│
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py          # FastAPI app, REST API, WebSocket
│   ├── mqtt_client.py   # MQTT subscriber + DB writer
│   ├── database.py      # SQLAlchemy engine & session
│   └── models.py        # ORM models (PT100, DHT22, GY906)
│
├── frontend/
│   ├── Dockerfile
│   ├── nginx.conf
│   └── index.html       # Dashboard (Chart.js + WebSocket)
│
├── db/
│   └── init.sql         # Schema PostgreSQL
│
└── tools/
    ├── testing.sh        # Kirim data dummy via mosquitto_pub
    └── simulate.py       # Simulator sensor (loop terus-menerus)
```

---

## Database Schema

```sql
-- PT100
CREATE TABLE pt100_readings (
    id          SERIAL PRIMARY KEY,
    temperature NUMERIC(6, 2) NOT NULL,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- DHT22
CREATE TABLE dht22_readings (
    id          SERIAL PRIMARY KEY,
    temperature NUMERIC(5, 2) NOT NULL,
    humidity    NUMERIC(5, 2) NOT NULL,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- GY-906
CREATE TABLE gy906_readings (
    id           SERIAL PRIMARY KEY,
    object_temp  NUMERIC(6, 2) NOT NULL,
    ambient_temp NUMERIC(6, 2) NOT NULL,
    created_at   TIMESTAMPTZ DEFAULT NOW()
);
```

Setiap tabel punya index `created_at DESC` untuk mempercepat query data terbaru.

---

## Cara Kerja (Data Flow)

1. **Sensor / simulator** publish pesan JSON ke EMQX via MQTT
2. **Backend** (thread terpisah) subscribe ke topik `sensors/pt100`, `sensors/dht22`, `sensors/gy906`
3. Setiap pesan masuk → data diparse → disimpan ke PostgreSQL via SQLAlchemy
4. Setelah insert berhasil → backend broadcast ke semua WebSocket client yang aktif
5. **Frontend** menerima data via WebSocket → update grafik Chart.js dan nilai stat secara real-time
6. Saat pertama load, frontend fetch 60 data terakhir dari REST API sebagai history chart

---

## REST API

Base URL: `http://localhost:8000`

| Method | Endpoint            | Deskripsi                          |
|--------|---------------------|------------------------------------|
| GET    | `/api/pt100/latest` | N data terbaru PT100 (`?limit=60`) |
| GET    | `/api/dht22/latest` | N data terbaru DHT22 (`?limit=60`) |
| GET    | `/api/gy906/latest` | N data terbaru GY906 (`?limit=60`) |
| GET    | `/health`           | Health check                       |
| WS     | `/ws`               | WebSocket endpoint (real-time)     |

Contoh response `GET /api/dht22/latest?limit=2`:
```json
[
  { "temperature": 27.50, "humidity": 61.20, "created_at": "2024-01-15T10:30:00+00:00" },
  { "temperature": 27.80, "humidity": 62.10, "created_at": "2024-01-15T10:30:05+00:00" }
]
```

WebSocket message format:
```json
{
  "sensor": "dht22",
  "data": {
    "temperature": 27.80,
    "humidity": 62.10,
    "created_at": "2024-01-15T10:30:05+00:00"
  }
}
```

---

## Cara Menjalankan

### Prasyarat
- [Docker](https://www.docker.com/) + Docker Compose
- `mosquitto-clients` (opsional, untuk testing manual)

### 1. Clone & Jalankan

```bash
git clone git@github.com:ivanadhii/skrispi-opal.git
cd skrispi-opal

docker compose up --build
```

Tunggu semua container healthy (sekitar 20–30 detik pertama kali).

### 2. Akses

| Layanan            | URL                        |
|--------------------|----------------------------|
| Dashboard          | http://localhost           |
| API Docs (Swagger) | http://localhost:8000/docs |
| EMQX Dashboard     | http://localhost:18083     |

> EMQX default login: `admin` / `public`

### 3. Stop

```bash
docker compose down

# Hapus semua data (reset DB)
docker compose down -v
```

---

## Testing & Simulasi

### Kirim Data Manual (1x burst)

Pastikan EMQX sudah running dan `mosquitto-clients` terinstall:

```bash
# macOS
brew install mosquitto

# Ubuntu/Debian
apt install mosquitto-clients
```

```bash
chmod +x tools/testing.sh
./tools/testing.sh
```

Script ini mengirim 5 data per sensor secara berurutan dengan nilai acak:
- PT100: 70–85 °C
- DHT22: 24–32 °C / 40–75 %
- GY-906: 35–39 °C (objek) / 23–27 °C (ambient)

### Simulasi Berkelanjutan (Loop)

```bash
python3 tools/simulate.py
```

Simulator mengirim data ke ketiga sensor setiap beberapa detik secara terus-menerus.

### Manual via mosquitto_pub

```bash
# PT100
mosquitto_pub -h localhost -p 1883 -t sensors/pt100 \
  -m '{"temperature": 78.5}'

# DHT22
mosquitto_pub -h localhost -p 1883 -t sensors/dht22 \
  -m '{"temperature": 29.1, "humidity": 65.0}'

# GY-906
mosquitto_pub -h localhost -p 1883 -t sensors/gy906 \
  -m '{"object_temp": 37.2, "ambient_temp": 25.8}'
```

---

## Environment Variables

Dikonfigurasi via `docker-compose.yml`:

| Variable       | Default                                              | Deskripsi            |
|----------------|------------------------------------------------------|----------------------|
| `DATABASE_URL` | `postgresql://iot_user:iot_password@postgres/iot_db` | Koneksi PostgreSQL   |
| `MQTT_BROKER`  | `emqx`                                               | Hostname MQTT broker |
| `MQTT_PORT`    | `1883`                                               | Port MQTT broker     |

---

## Troubleshooting

**Backend gagal konek ke EMQX saat startup**
Backend otomatis retry setiap 5 detik. Tunggu EMQX selesai booting (~15 detik).

**Data tidak muncul di dashboard**
1. Pastikan semua container running: `docker compose ps`
2. Cek log backend: `docker compose logs backend -f`
3. Pastikan topic yang dipublish sesuai: `sensors/pt100`, `sensors/dht22`, `sensors/gy906`

**Port 80 sudah dipakai**
Edit `docker-compose.yml` bagian frontend, ganti `"80:80"` ke port lain, misal `"8080:80"`.
