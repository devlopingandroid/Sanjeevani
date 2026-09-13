"""ESP32 USB Serial Ingestion Reader (Development Transport).

Continuously streams and parses the actual CSV output from the ESP32 wearable firmware:
Timestamp,IR,RED,Accel_X,Accel_Y,Accel_Z,Gyro_X,Gyro_Y,Gyro_Z,Temp_F,GSR_Raw,GSR_Voltage

Feeds directly into the unified SensorService.
"""
import time
import sys
import os
from typing import Optional, Generator, Dict, Any
from datetime import datetime, timezone
import serial
import serial.tools.list_ports

from app.core.config import settings
from app.core.logging import logger
from app.schemas.sensor import (
    CanonicalSensorPacket,
    SensorTransport,
    SensorQuality,
)
from app.services.sensor_service import SensorService
from app.services.device_service import DeviceService
from app.db.database import SessionLocal
from app.models.device import DeviceStatus


def parse_esp32_csv_line(line: str, device_id: str) -> Optional[CanonicalSensorPacket]:
    """Parses a single raw line emitted by the ESP32 firmware over USB Serial.

    Expected format:
    Timestamp,IR,RED,Accel_X,Accel_Y,Accel_Z,Gyro_X,Gyro_Y,Gyro_Z,Temp_F,GSR_Raw,GSR_Voltage
    """
    cleaned = line.strip()
    if not cleaned:
        return None

    # Skip header line if emitted upon ESP32 reboot
    if cleaned.startswith("Timestamp") or "IR" in cleaned:
        return None

    parts = [p.strip() for p in cleaned.split(",")]
    if len(parts) != 12:
        logger.debug(f"[INVALID_PACKET] Expected 12 CSV fields from ESP32, got {len(parts)}: '{cleaned}'")
        return None

    try:
        packet = CanonicalSensorPacket(
            device_id=device_id,
            timestamp=parts[0],
            IR=int(parts[1]),
            RED=int(parts[2]),
            Accel_X=int(parts[3]),
            Accel_Y=int(parts[4]),
            Accel_Z=int(parts[5]),
            Gyro_X=int(parts[6]),
            Gyro_Y=int(parts[7]),
            Gyro_Z=int(parts[8]),
            Temp_F=float(parts[9]),
            GSR_Raw=int(parts[10]),
            GSR_Voltage=float(parts[11]),
            transport=SensorTransport.SERIAL,
        )
        return packet
    except Exception as exc:
        logger.debug(f"[INVALID_PACKET] Parse/validation error on '{cleaned}': {exc}")
        return None


class ESP32SerialReader:
    """Portable, resilient serial reader with auto-reconnect and line buffering."""

    def __init__(
        self,
        port: Optional[str] = None,
        baudrate: Optional[int] = None,
        device_id: Optional[str] = None,
        auto_reconnect: bool = True,
        reconnect_delay: float = 2.0,
    ):
        self.port = port or settings.ESP32_SERIAL_PORT
        self.baudrate = baudrate or settings.ESP32_SERIAL_BAUDRATE
        self.device_id = device_id or settings.ESP32_SERIAL_DEVICE_ID
        self.auto_reconnect = auto_reconnect
        self.reconnect_delay = reconnect_delay

        self._running: bool = False
        self._serial_conn: Optional[serial.Serial] = None
        self._line_buffer: str = ""

    @staticmethod
    def auto_detect_port() -> Optional[str]:
        """Scans for available serial ports matching known ESP32 USB/UART descriptors."""
        ports = list(serial.tools.list_ports.comports())
        for p in ports:
            desc = (p.description or "").lower()
            name = (p.name or "").lower()
            # Common ESP32 USB-UART bridges: CP210x, CH340, FTDI, USB Serial
            if any(k in desc or k in name for k in ["cp210", "ch340", "ftdi", "uart", "usb serial"]):
                return p.device
        # Fallback to first available port if only one exists
        if len(ports) == 1:
            return ports[0].device
        return None

    def connect(self) -> bool:
        """Establishes connection to the serial port."""
        target_port = self.port or self.auto_detect_port()
        if not target_port:
            logger.warning("No ESP32 serial port specified or detected.")
            return False

        try:
            self._serial_conn = serial.Serial(
                port=target_port,
                baudrate=self.baudrate,
                timeout=1.0,
            )
            logger.info(f"[DEVICE_CONNECTED] Opened ESP32 serial port {target_port} at {self.baudrate} baud.")
            # Update device state in database
            db = SessionLocal()
            try:
                DeviceService.update_heartbeat(db, self.device_id, transport="SERIAL", is_valid=True)
            finally:
                db.close()
            return True
        except serial.SerialException as exc:
            logger.warning(f"Could not open serial port {target_port}: {exc}")
            self._serial_conn = None
            return False

    def close(self):
        """Safely closes the serial connection."""
        if self._serial_conn and self._serial_conn.is_open:
            try:
                self._serial_conn.close()
            except Exception:
                pass
        self._serial_conn = None
        logger.info(f"[DEVICE_DISCONNECTED] Closed serial connection for {self.device_id}")

    def read_lines(self) -> Generator[str, None, None]:
        """Reads incoming serial stream and yields complete lines, handling partial buffers."""
        if not self._serial_conn or not self._serial_conn.is_open:
            return

        try:
            raw_bytes = self._serial_conn.read(self._serial_conn.in_waiting or 1)
            if not raw_bytes:
                return

            text = raw_bytes.decode("utf-8", errors="replace")
            self._line_buffer += text

            while "\n" in self._line_buffer:
                line, self._line_buffer = self._line_buffer.split("\n", 1)
                cleaned = line.strip("\r")
                if cleaned:
                    yield cleaned
        except (serial.SerialException, OSError) as exc:
            logger.warning(f"Serial read error: {exc}")
            self.close()

    def process_incoming_line(self, line: str):
        """Parses a line and invokes the canonical SensorService."""
        packet = parse_esp32_csv_line(line, self.device_id)
        if not packet:
            return

        db = SessionLocal()
        try:
            response = SensorService.ingest_canonical_packet(db, packet)
            if response.accepted:
                logger.debug(f"[PACKET_ACCEPTED] {packet.device_id} (Quality: {packet.quality.value})")
            elif response.is_duplicate:
                logger.debug(f"[DUPLICATE_PACKET] {packet.device_id}")
        except Exception as exc:
            logger.error(f"Error persisting serial packet: {exc}")
        finally:
            db.close()

    def run(self):
        """Continuous ingestion loop with reconnection handling."""
        self._running = True
        logger.info(f"Starting ESP32 Serial Ingestion Reader for '{self.device_id}'...")

        while self._running:
            if not self._serial_conn or not self._serial_conn.is_open:
                connected = self.connect()
                if not connected:
                    if not self.auto_reconnect:
                        break
                    time.sleep(self.reconnect_delay)
                    continue

            # Read available lines
            for line in self.read_lines():
                self.process_incoming_line(line)

            # Small yield to prevent CPU spinning if buffer empty
            time.sleep(0.005)

    def stop(self):
        self._running = False
        self.close()


if __name__ == "__main__":
    reader = ESP32SerialReader()
    try:
        reader.run()
    except KeyboardInterrupt:
        reader.stop()
        print("\nSerial reader stopped by user.")
