-- PT100: RTD temperature sensor
CREATE TABLE IF NOT EXISTS pt100_readings (
    id SERIAL PRIMARY KEY,
    temperature NUMERIC(6, 2) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- DHT22: temperature + humidity sensor
CREATE TABLE IF NOT EXISTS dht22_readings (
    id SERIAL PRIMARY KEY,
    temperature NUMERIC(5, 2) NOT NULL,
    humidity NUMERIC(5, 2) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- GY906: IR non-contact temperature sensor
CREATE TABLE IF NOT EXISTS gy906_readings (
    id SERIAL PRIMARY KEY,
    object_temp NUMERIC(6, 2) NOT NULL,
    ambient_temp NUMERIC(6, 2) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for time-series queries
CREATE INDEX idx_pt100_created_at ON pt100_readings(created_at DESC);
CREATE INDEX idx_dht22_created_at ON dht22_readings(created_at DESC);
CREATE INDEX idx_gy906_created_at ON gy906_readings(created_at DESC);
