# 🩺🩺 SANJEEVNI

### ESP32-Powered Wearable Wellness & Real-Time Physiological Monitoring Platform

**Sanjeevni** is an ESP32-based wearable health and wellness monitoring platform designed to continuously capture physiological and activity-related parameters through multiple sensors and make the collected data available for real-time analysis and visualization.

The system combines **embedded hardware, wearable sensing, a Python backend, and a modern frontend** into a unified health-monitoring platform.

> **Core Principle:** Sanjeevni is designed around **real sensor data only**.
> **No mock data. No fabricated readings. No simulated health parameters.**

---

## 📌 Table of Contents

* [Overview](#-overview)
* [Problem Statement](#-problem-statement)
* [Objectives](#-objectives)
* [Key Features](#-key-features)
* [System Architecture](#-system-architecture)
* [Hardware](#-hardware)
* [Sensors & Parameters](#-sensors--parameters)
* [Software Stack](#-software-stack)
* [Project Structure](#-project-structure)
* [Data Flow](#-data-flow)
* [Backend](#-backend)
* [Firmware](#-firmware)
* [Frontend](#-frontend)
* [Real-Time Monitoring](#-real-time-monitoring)
* [Data Integrity Policy](#-data-integrity-policy)
* [Installation & Setup](#-installation--setup)
* [Environment Variables](#-environment-variables)
* [Running the Project](#-running-the-project)
* [API Overview](#-api-overview)
* [Sensor Calibration](#-sensor-calibration)
* [Error Handling](#-error-handling)
* [Development Workflow](#-development-workflow)
* [Future Scope](#-future-scope)
* [Limitations](#-limitations)
* [Contributing](#-contributing)
* [License](#-license)
* [Disclaimer](#-disclaimer)

---

## 🔎 Overview

Sanjeevni is a **wearable physiological monitoring system** built around the ESP32 microcontroller.

The wearable collects physiological and motion data using sensors such as:

* ❤️ **MAX30102** — PPG-based heart-rate / SpO₂ sensing
* 🏃 **MPU6050** — accelerometer and gyroscope for motion/activity data
* 🌡️ **MAX30205** — body-temperature-oriented temperature sensing
* ✋ **GSR** — galvanic skin response through an analog input

The ESP32 acts as the edge device responsible for sensor acquisition and transmission.

The collected readings are sent to the **Python backend**, where they are processed, validated, stored, and exposed to the frontend application.

The frontend provides a user-facing interface for monitoring the incoming physiological data.

### High-Level Architecture

```text
┌──────────────────────────────────────────────┐
│                 WEARABLE DEVICE               │
│                                                │
│                    ESP32                      │
│                                                │
│   ┌─────────┐ ┌─────────┐ ┌─────────────┐     │
│   │MAX30102 │ │MPU6050  │ │ MAX30205    │     │
│   │  PPG    │ │ IMU     │ │ Temperature │     │
│   └────┬────┘ └────┬────┘ └──────┬──────┘     │
│        │           │             │            │
│        └───────────┴─────────────┘            │
│                     │                         │
│                  GSR ADC                      │
└─────────────────────┬──────────────────────────┘
                       │
                       │ Real Sensor Data
                       ▼
┌──────────────────────────────────────────────┐
│                PYTHON BACKEND                 │
│                                                │
│  Validation → Processing → API → Storage      │
└─────────────────────┬──────────────────────────┘
                       │
                       │ REST / Real-Time Data
                       ▼
┌──────────────────────────────────────────────┐
│                   FRONTEND                    │
│                                                │
│   Dashboard • Live Monitoring • Analytics     │
└──────────────────────────────────────────────┘
```

---

## 🎯 Problem Statement

Traditional health monitoring often depends on periodic measurements or dedicated medical equipment.

Sanjeevni explores a different approach:

> **Can a compact wearable continuously collect multiple physiological and activity-related parameters and make those readings available through a connected software platform?**

The project focuses on building the complete pipeline:

```text
Physical Sensor
      ↓
ESP32
      ↓
Data Acquisition
      ↓
Communication
      ↓
Python Backend
      ↓
Validation / Processing
      ↓
Frontend
      ↓
Real-Time Monitoring
```

---

## 🎯 Objectives

The primary objectives of Sanjeevni are:

1. Build a compact ESP32-based wearable.
2. Collect physiological parameters from real sensors.
3. Capture motion and activity information.
4. Establish reliable communication between wearable and backend.
5. Process and validate incoming sensor data.
6. Provide real-time monitoring through a frontend interface.
7. Maintain a strict **no-mock-data** architecture.
8. Create a modular platform that can be extended with additional sensors and analytics.

---

## ✨ Key Features

### 🩺 Multi-Parameter Monitoring

Sanjeevni is designed to collect multiple parameters from a single wearable platform.

Current sensor modules include:

| Sensor   | Parameter / Signal                                     | Interface  |
| -------- | -------------------------------------------------------- | ---------- |
| MAX30102 | PPG / Heart-rate related signal / SpO₂-related signal    | I²C        |
| MPU6050  | Accelerometer + Gyroscope                                 | I²C        |
| MAX30205 | Temperature                                                | I²C        |
| GSR      | Galvanic Skin Response                                     | Analog ADC |

### ⚡ Real-Time Data Pipeline

Sensor readings move through the system without artificially generated values:

```text
Sensor → ESP32 → Backend → Frontend
```

### 📊 Live Monitoring

The frontend presents incoming sensor measurements in a user-friendly dashboard, updating as new readings arrive from the backend.

### 🔐 Data Integrity

The project strictly prohibits:

* Randomly generated health values
* Hard-coded physiological readings
* Fake sensor responses
* Placeholder readings presented as real measurements
* Synthetic data silently entering production flows

### 🧩 Modular Architecture

Each layer is independently extensible:

```text
Hardware
   ↓
Firmware
   ↓
Communication
   ↓
Backend
   ↓
Frontend
```

New sensors, processing modules, APIs, and UI components can therefore be added without redesigning the entire system.

---

## 🏗 System Architecture

Sanjeevni follows a layered architecture, where each layer has a single, well-defined responsibility and communicates with adjacent layers through a stable interface.

| Layer         | Responsibility                                                  |
| ------------- | ----------------------------------------------------------------- |
| Hardware      | Physical sensing (PPG, IMU, temperature, GSR)                     |
| Firmware      | Sensor drivers, acquisition loop, transmission to backend          |
| Communication | Wi-Fi / serial transport of sensor payloads                        |
| Backend       | Validation, processing, storage, and API exposure                  |
| Frontend      | Visualization, live dashboards, historical analytics               |

This separation allows each layer to be developed, tested, and replaced independently — for example, swapping the communication transport or adding a new sensor module without touching the frontend.

---

## 🧰 Hardware

### ESP32

The ESP32 serves as the primary edge-computing and communication controller.

Responsibilities include:

* Sensor initialization
* Sensor polling
* Raw data acquisition
* Basic signal processing
* Device communication
* Data transmission to backend
* Connection management

### MAX30102

The MAX30102 is used as the wearable's optical sensing module.

It provides photoplethysmography (**PPG**) signals that can be processed for physiological measurements such as:

* Heart-rate estimation
* Blood-oxygen-related estimation

> Actual derived values depend on signal quality, sensor placement, calibration, algorithms, and environmental conditions.

### MPU6050

The MPU6050 combines:

* 3-axis accelerometer
* 3-axis gyroscope

It is used for:

* Motion detection
* Activity analysis
* Movement patterns
* Orientation-related information

### MAX30205

The MAX30205 is a high-accuracy temperature sensor designed for temperature measurement.

Within Sanjeevni, it is used for temperature monitoring.

> Sensor temperature should not automatically be interpreted as medically equivalent to a clinically measured core body temperature.

### GSR Sensor

The Galvanic Skin Response sensor measures changes associated with the electrical conductance/resistance of the skin.

The ESP32 reads the GSR signal through an analog input.

Potential applications include:

* Arousal-related analysis
* Stress-related signal exploration
* Activity/context correlation

> GSR readings should be treated as **physiological signals**, not direct psychological diagnoses.

---

## 📡 Sensors & Parameters

The Sanjeevni architecture is designed around a multi-modal sensing model.

```text
                   SANJEEVNI
                       │
       ┌───────────────┼────────────────┐
       │               │                │
       ▼               ▼                ▼
   Physiological     Motion          Skin Signal
      Signals        Signals
       │               │                │
       ▼               ▼                ▼
   MAX30102         MPU6050            GSR
       │               │                │
       ├───────────────┴────────────────┤
       │                                │
       ▼                                ▼
   Temperature                    Combined Dataset
       │
       ▼
   MAX30205
```

### Current Measurement Categories

**Cardiovascular-related**
* PPG waveform
* Heart-rate estimation
* SpO₂-related estimation

**Temperature**
* Temperature sensor reading

**Motion**
* Accelerometer X/Y/Z
* Gyroscope X/Y/Z

**Electrodermal**
* GSR ADC reading

---

## 💻 Software Stack

### Firmware
* ESP32
* Arduino / ESP32-compatible firmware
* C/C++
* I²C
* ADC
* Sensor-specific libraries

### Backend
* Python
* REST API
* Data validation
* Sensor-data processing
* Real-time communication as implemented by the backend

See [`backend/README.md`](backend/README.md) for backend-specific documentation.

### Frontend
* Modern JavaScript/TypeScript framework
* Real-time monitoring components
* Sensor dashboards
* Data visualization
* Device/status information

---

## 📁 Project Structure

A typical repository structure is:

```text
Sanjeevni/
│
├── backend/
│   ├── README.md
│   ├── app/
│   ├── requirements.txt
│   └── ...
│
├── frontend/
│   ├── src/
│   ├── package.json
│   └── ...
│
├── firmware/
│   ├── ESP32/
│   │   ├── MAX30102/
│   │   ├── MPU6050/
│   │   ├── MAX30205/
│   │   └── GSR/
│   │
│   └── ...
│
├── docs/
│   ├── architecture/
│   ├── hardware/
│   ├── research/
│   └── ...
│
├── README.md
├── .gitignore
└── LICENSE
```

> Directory names may evolve as the project develops. Keep this section synchronized with the actual repository structure.

---

## 🔄 Data Flow

The complete Sanjeevni data pipeline is:

```text
┌─────────────┐
│   Sensors   │
└──────┬──────┘
       │  Raw measurements
       ▼
┌─────────────┐
│    ESP32    │
└──────┬──────┘
       │  Device communication (Wi-Fi / Serial)
       ▼
┌─────────────┐
│   Backend   │
│  Validation │
│  Processing │
│   Storage   │
└──────┬──────┘
       │  REST / Real-time data
       ▼
┌─────────────┐
│  Frontend   │
│  Dashboard  │
└─────────────┘
```

**Step-by-step:**

1. **Sensors** capture raw physiological and motion signals.
2. **ESP32** polls each sensor over I²C/ADC and packages the readings.
3. **Communication layer** transmits the payload to the backend (e.g., over Wi-Fi via REST/WebSocket, or serial during development/debugging).
4. **Backend** validates incoming payloads, rejects malformed or out-of-range data, processes/derives higher-level metrics, and persists readings.
5. **Frontend** consumes the processed data via API/real-time channel and renders it on the dashboard.

---

## 🖥 Backend

The Python backend is responsible for:

* Receiving sensor payloads from the ESP32
* Validating payload structure and value ranges
* Processing/deriving physiological metrics where applicable
* Persisting readings to storage
* Exposing REST and/or real-time endpoints to the frontend

Detailed backend setup, endpoint definitions, and configuration are documented separately in [`backend/README.md`](backend/README.md).

---

## 🔌 Firmware

The firmware layer runs on the ESP32 and is responsible for:

* Initializing I²C and ADC peripherals
* Reading each sensor at an appropriate polling interval
* Packaging readings into a structured payload (e.g., JSON)
* Managing Wi-Fi/network connectivity
* Transmitting payloads to the backend
* Basic on-device error handling (sensor disconnects, retries)

Firmware source for each sensor module lives under `firmware/ESP32/<SENSOR_NAME>/`.

---

## 🎨 Frontend

The frontend provides the user-facing layer of Sanjeevni:

* Live dashboard for incoming sensor data
* Per-sensor visualizations (heart rate, SpO₂, temperature, motion, GSR)
* Device/connection status indicators
* Historical data views (where supported by the backend)

---

## 📈 Real-Time Monitoring

Sanjeevni is designed so that sensor readings are visible on the frontend shortly after acquisition, with the backend acting as the intermediary that validates and forwards data. The exact transport (polling, WebSocket, SSE, etc.) depends on the backend implementation — see `backend/README.md`.

---

## 🔐 Data Integrity Policy

Sanjeevni enforces a **strict no-mock-data policy** across every layer of the stack:

* ❌ No randomly generated health values
* ❌ No hard-coded physiological readings
* ❌ No fake sensor responses used as if real
* ❌ No placeholder readings presented as real measurements
* ❌ No synthetic data silently entering production flows

If a sensor is disconnected, faulty, or returns invalid data, the system should **surface an error or "no data" state** rather than substitute a fabricated value. This applies to firmware, backend, and frontend code alike, including during development and testing (use clearly labeled test fixtures, never silently-injected fake readings).

---

## ⚙️ Installation & Setup

### Prerequisites

* ESP32 development board
* MAX30102, MPU6050, MAX30205, and GSR sensor modules
* Arduino IDE or PlatformIO
* Python 3.10+
* Node.js (for frontend, if applicable)
* Git

### Clone the Repository

```bash
git clone https://github.com/<your-org>/Sanjeevni.git
cd Sanjeevni
```

---

## 🔑 Environment Variables

Backend and frontend configuration should be supplied via environment variables rather than hard-coded values. Typical variables include:

```env
# Backend
HOST=0.0.0.0
PORT=8000
DATABASE_URL=your_database_connection_string
LOG_LEVEL=INFO

# Device / Firmware
WIFI_SSID=your_wifi_ssid
WIFI_PASSWORD=your_wifi_password
BACKEND_ENDPOINT=http://<backend-host>:8000/api/sensor-data

# Frontend
VITE_API_BASE_URL=http://localhost:8000
```

> Exact variable names depend on the actual backend/frontend implementation — keep this section in sync with `.env.example` files in each module.

---

## ▶️ Running the Project

**1. Flash the firmware**

```bash
# Using Arduino IDE: open firmware/ESP32/<module>/<module>.ino and upload
# Using PlatformIO:
cd firmware/ESP32
pio run --target upload
```

**2. Start the backend**

```bash
cd backend
pip install -r requirements.txt
python app.py
```

**3. Start the frontend**

```bash
cd frontend
npm install
npm run dev
```

**4. Power on the wearable** and confirm it connects to Wi-Fi and begins transmitting to the backend endpoint.

---

## 📡 API Overview

A representative (illustrative) set of backend endpoints:

| Method | Endpoint                | Description                                |
| ------ | ------------------------ | ------------------------------------------- |
| POST   | `/api/sensor-data`       | Receive a sensor payload from the ESP32     |
| GET    | `/api/sensor-data/latest`| Fetch the most recent reading(s)            |
| GET    | `/api/sensor-data/history`| Fetch historical readings                  |
| GET    | `/api/device/status`     | Get device/connection status                |
| WS     | `/ws/live`                | Real-time streaming channel (if implemented)|

> See [`backend/README.md`](backend/README.md) for the authoritative, up-to-date API reference.

---

## 🎛 Sensor Calibration

Each sensor may require calibration or tuning before readings are reliable:

* **MAX30102** — finger/wrist placement, ambient light shielding, and algorithm tuning affect HR/SpO₂ accuracy.
* **MPU6050** — accelerometer/gyroscope offsets should be calibrated at rest to remove bias.
* **MAX30205** — verify against a reference thermometer under controlled conditions.
* **GSR** — baseline skin conductance varies by person and electrode placement; a per-user baseline is recommended.

Calibration routines and reference values should be documented under `docs/hardware/`.

---

## 🛠 Error Handling

Sanjeevni handles errors explicitly rather than masking them with fabricated data:

* **Sensor-level:** failed reads are flagged and reported, not replaced with defaults.
* **Firmware-level:** connection loss triggers retry logic and status reporting rather than silent failure.
* **Backend-level:** malformed or out-of-range payloads are rejected with clear validation errors.
* **Frontend-level:** missing or stale data is shown as "no data" / "disconnected," never as a plausible-looking fake value.

---

## 🔁 Development Workflow

1. Create a feature branch from `main`.
2. Make changes within the relevant layer (`firmware/`, `backend/`, `frontend/`, `docs/`).
3. Test against real hardware/sensor data wherever possible.
4. Update relevant documentation (this README and layer-specific READMEs).
5. Open a pull request describing the change and how it was validated.

---

## 🚀 Future Scope

* Additional physiological sensors (e.g., ECG, respiration)
* On-device signal processing and filtering
* Cloud-based long-term storage and analytics
* Mobile companion app
* Alerting/notification system for anomalous readings
* Battery and power-optimization improvements

---

## ⚠️ Limitations

* Derived physiological values (HR, SpO₂, etc.) depend heavily on sensor placement, contact quality, and environmental conditions.
* The system is a research/engineering platform, not a certified medical device.
* Real-time performance depends on network conditions between the wearable and backend.

---

## 🤝 Contributing

Contributions are welcome. Please:

1. Fork the repository.
2. Create a descriptive feature branch.
3. Follow the existing code style for each layer.
4. Ensure any sensor-related change is tested against real hardware.
5. Submit a pull request with a clear description of the change.

---

## 📄 License

This project is licensed under the terms specified in the [LICENSE](LICENSE) file.

---

## ⚕️ Disclaimer

Sanjeevni is an educational/engineering project and is **not a certified medical device**. Readings produced by this system should not be used for medical diagnosis, treatment decisions, or emergency response. Always consult a qualified healthcare professional for medical concerns.
