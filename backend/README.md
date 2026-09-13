# SANJEEVNI — Production-Grade Backend (Phase 2)

SANJEEVNI is a real-time wellness and stress monitoring platform powered by an ESP32 wearable device.
The backend serves as the **single source of truth** for telemetry, ingesting real physiological data via USB Serial (development transport), HTTP API, and Wi-Fi, persisting to **Supabase PostgreSQL** via SQLAlchemy & Alembic.

---

## Absolute No-Mock-Data Rule

The backend enforces an uncompromising data integrity policy:
- **No synthetic or random physiological values are ever generated.**
- Missing telemetry, disconnected devices, or missing ML models explicitly yield:
  - `NO_DATA`
  - `DEVICE_DISCONNECTED`
  - `INSUFFICIENT_DATA`
  - `SENSOR_ERROR`
  - `MODEL_UNAVAILABLE`

The mobile application and web frontend use these explicit states to show honest status messages (`"Waiting for sensor data..."`, `"Device disconnected"`, `"Collecting sensor buffer..."`) rather than fake stress percentages or simulated vitals.

---

## Phase 2 Implementation Status Matrix

| Component | Status | Details |
|:---|:---|:---|
| **Canonical Sensor Packet** | `VERIFIED` | Transport-agnostic schema (`sensor_timestamp`, `received_at`, `ir`, `red`, `accel`, `gyro`, `temperature`, `gsr`, `quality`, `transport`) |
| **USB Serial Reader** | `VERIFIED` | Portable `serial_reader.py` handling line buffers, partial lines, reconnects, and parsing real ESP32 CSV streams |
| **Unified Sensor Ingestion Service** | `VERIFIED` | Single authoritative service handling USB Serial, HTTP, and Wi-Fi |
| **Data Quality Grading** | `VERIFIED` | Physiological quality evaluation: `GOOD`, `FAIR`, `POOR`, `INVALID` |
| **Duplicate & Ordering Handling** | `VERIFIED` | Deduplication by `(device_id, sequence_number)` or `(device_id, sensor_timestamp)`; out-of-order tracking |
| **Device State & Counter Tracking** | `VERIFIED` | States (`REGISTERED`, `CONNECTING`, `CONNECTED`, `NO_DATA`, `STALE`, `DISCONNECTED`, `ERROR`) with telemetry counters |
| **Database Persistence (Supabase PostgreSQL)** | `VERIFIED` | SQLAlchemy & Alembic models with composite indexes on `(device_id, sensor_timestamp)` and `(device_id, received_at)` |
| **Wi-Fi Transport Protocol** | `VERIFIED` | Documented in [docs/WIFI_INTEGRATION.md](file:///d:/Desktop/Sanjeevani/backend/docs/WIFI_INTEGRATION.md) |
| **Automated Test Suite** | `VERIFIED` | 39 unit and integration tests passing in < 1 second |
| **Hardware Connection** | `PENDING` | Tested with recorded telemetry from `Yash.csv`; physical ESP32 board is not currently plugged into USB ports |

---

## ESP32 Telemetry Format & Field Mapping

The ESP32 firmware (`sensor_tracker_no_ble_sd.ino` and `sketch_jul31d.ino`) outputs the following 12 fields:

| Firmware Header | Canonical Schema Field | Model Field | Bounds / Valid Range | Physical Sensor |
|:---|:---|:---|:---|:---|
| `Timestamp` | `sensor_timestamp` / `timestamp` | `sensor_timestamp` | IST / UTC datetime | NTP / RTC synchronized time |
| `IR` | `ir` / `IR` | `ir` | 1 – 300,000 | MAX30102 PPG Infrared |
| `RED` | `red` / `RED` | `red` | 1 – 300,000 | MAX30102 PPG Red |
| `Accel_X` | `accel_x` / `Accel_X` | `accel_x` | -32,768 – 32,767 | MPU6050 Accelerometer X |
| `Accel_Y` | `accel_y` / `Accel_Y` | `accel_y` | -32,768 – 32,767 | MPU6050 Accelerometer Y |
| `Accel_Z` | `accel_z` / `Accel_Z` | `accel_z` | -32,768 – 32,767 | MPU6050 Accelerometer Z |
| `Gyro_X` | `gyro_x` / `Gyro_X` | `gyro_x` | -32,768 – 32,767 | MPU6050 Gyroscope X |
| `Gyro_Y` | `gyro_y` / `Gyro_Y` | `gyro_y` | -32,768 – 32,767 | MPU6050 Gyroscope Y |
| `Gyro_Z` | `gyro_z` / `Gyro_Z` | `gyro_z` | -32,768 – 32,767 | MPU6050 Gyroscope Z |
| `Temp_F` | `temperature` / `Temp_F` | `temp_f` | 60.0°F – 120.0°F | MAX30205 Skin Temperature |
| `GSR_Raw` | `gsr_raw` / `GSR_Raw` | `gsr_raw` | 0 – 4,095 | ESP32 12-bit ADC (GPIO 34) |
| `GSR_Voltage` | `gsr_voltage` / `GSR_Voltage` | `gsr_voltage` | 0.0V – 3.3V | Calculated GSR voltage |

---

## Setup and Ingestion Guide

### 1. Installation
```bash
cd backend
.venv\Scripts\Activate.ps1   # Windows PowerShell
pip install -r requirements.txt
```

### 2. Environment Configuration
Configure `.env`:
```env
# Supabase PostgreSQL connection URL
DATABASE_URL=postgresql+psycopg2://postgres:[YOUR-PASSWORD]@db.[YOUR-PROJECT-REF].supabase.co:5432/postgres

# Optional USB Serial Port
ESP32_SERIAL_PORT=COM3
ESP32_SERIAL_BAUDRATE=115200
ESP32_SERIAL_DEVICE_ID=ESP32_WEARABLE_DEV
```
*(Defaults to local SQLite `sanjeevani_dev.db` when PostgreSQL credentials are not provided).*

### 3. Apply Database Migrations
```bash
alembic upgrade head
```

### 4. Running the Backend
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
Interactive Swagger documentation is available at **http://localhost:8000/docs**.

### 5. Running the USB Serial Ingestion Reader
With your ESP32 plugged in via USB:
```bash
python -m app.transport.serial_reader
```
The reader continuously parses serial lines and passes canonical packets into the backend ingestion service.

---

## Running Automated Tests
```bash
pytest tests -v
```
All 39 unit and integration tests run in under 1 second.
