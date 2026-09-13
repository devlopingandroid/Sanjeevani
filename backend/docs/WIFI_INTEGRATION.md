# ESP32 Wi-Fi Ingestion Protocol Specification

This document details the architectural contract for connecting the ESP32 wearable directly to the FastAPI backend over Wi-Fi (Phase 2 preparation).

---

## 1. Overview
The backend provides a unified ingestion service that handles both development USB Serial and production Wi-Fi telemetry identically:

```
ESP32 Wearable (Wi-Fi)
       ↓  HTTP POST
/api/v1/sensors/ingest
       ↓
Canonical Validation & Normalization
       ↓
Supabase PostgreSQL
```

---

## 2. Ingestion Endpoint

- **Method**: `POST`
- **Path**: `/api/v1/sensors/ingest`
- **Headers**:
  ```http
  Content-Type: application/json
  X-Device-Id: ESP32_MAC_ADDRESS
  ```

---

## 3. JSON Payload Contract

The ESP32 firmware constructs and transmits JSON packets matching the canonical sensor schema:

```json
{
  "device_id": "ESP32_A1B2C3D4E5F6",
  "timestamp": "13-09-2026 15:30:00.125",
  "sequence_number": 1042,
  "IR": 27156,
  "RED": 18003,
  "Accel_X": 1056,
  "Accel_Y": 1152,
  "Accel_Z": 16428,
  "Gyro_X": -136,
  "Gyro_Y": 221,
  "Gyro_Z": 110,
  "Temp_F": 91.58,
  "GSR_Raw": 1911,
  "GSR_Voltage": 1.540,
  "transport": "WIFI"
}
```

### Supported Field Name Aliases:
- `timestamp` or `sensor_timestamp`
- `IR` or `ir`
- `RED` or `red`
- `Accel_X` or `accel_x`
- `Temp_F` or `temperature`
- `GSR_Raw` or `gsr_raw`
- `GSR_Voltage` or `gsr_voltage`

---

## 4. Batch Ingestion (Optimized for Wi-Fi Power Saving)

To optimize ESP32 battery life and radio power consumption, samples can be buffered locally in ESP32 RAM (e.g., 25 samples = 1 second) and dispatched in a single batch:

- **Path**: `/api/v1/sensors/ingest-batch`
- **Payload**:
  ```json
  {
    "device_id": "ESP32_A1B2C3D4E5F6",
    "packets": [
      {
        "timestamp": "13-09-2026 15:30:00.040",
        "sequence_number": 1001,
        "IR": 27150,
        "RED": 18000,
        "Accel_X": 1050,
        "Accel_Y": 1150,
        "Accel_Z": 16420,
        "Gyro_X": -130,
        "Gyro_Y": 220,
        "Gyro_Z": 110,
        "Temp_F": 91.55,
        "GSR_Raw": 1910,
        "GSR_Voltage": 1.539,
        "transport": "WIFI"
      }
    ]
  }
  ```

---

## 5. Network Failure & Reconnect Policy

1. **Connection Loss**:
   - When Wi-Fi drops, the ESP32 must **never generate synthetic data**.
   - Samples are buffered in circular RAM buffer (up to buffer capacity).
   - If buffer is full, old samples may be dropped or stored on local SD card (as implemented in `sketch_jul31d.ino`).
2. **Exponential Backoff**:
   - Retry intervals: 1s, 2s, 4s, up to 30s.
3. **Resumed Transmission**:
   - Upon reconnect, buffered packets are sent with their original `sensor_timestamp` preserved.
   - The backend validates the preserved timestamps and detects out-of-order/duplicate packets safely without discarding valid telemetry.
