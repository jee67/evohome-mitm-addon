import os
import sys
import json
import time
import serial

from ramses_codec import (
    decode_ramses_line,
    encode_ramses_frame,
    is_relevant_ch_setpoint,
    get_ch_raw,
    set_ch_raw,
)

OPTIONS_FILE = "/data/options.json"
SERIAL_DEVICE = "/dev/serial/by-id/usb-FTDI_FT232R_USB_UART_A50285BI-if00-port0"
BAUDRATE = 115200  # pas aan indien jouw evofw3 anders staat

DEFAULT_CONTROLLER_ID = "01:033496"
DEFAULT_OTB_ID = "10:061315"


def valid_ramses_id(addr: str) -> bool:
    # Formaat: "01:033496" (2 digits, ':', 6 digits)
    return (
        isinstance(addr, str)
        and len(addr) == 9
        and addr[2] == ":"
        and addr[:2].isdigit()
        and addr[3:].isdigit()
    )


def fatal(msg: str) -> None:
    print(f"FATAL: {msg}")
    sys.exit(1)


# ─────────────────────────────────────────────────────────────
# Config laden
# ─────────────────────────────────────────────────────────────
try:
    with open(OPTIONS_FILE, "r") as f:
        options = json.load(f)
except Exception as e:
    fatal(f"kan options.json niet lezen: {e}")

controller_id = (options.get("controller_id") or DEFAULT_CONTROLLER_ID).strip()
otb_id = (options.get("otb_id") or DEFAULT_OTB_ID).strip()

try:
    max_ch_raw = int(options.get("max_ch_raw", 100))
    idle_ch_raw = int(options.get("idle_ch_raw", 20))
except Exception:
    fatal("max_ch_raw/idle_ch_raw zijn geen geldige integers")

if not valid_ramses_id(controller_id):
    fatal(f"ongeldig controller_id: {controller_id}")

if not valid_ramses_id(otb_id):
    fatal(f"ongeldig otb_id: {otb_id}")

if not os.path.exists(SERIAL_DEVICE):
    fatal(f"serial device bestaat niet: {SERIAL_DEVICE}")

# ─────────────────────────────────────────────────────────────
# Serial openen
# ─────────────────────────────────────────────────────────────
try:
    ser = serial.Serial(SERIAL_DEVICE, baudrate=BAUDRATE, timeout=0.1)
except Exception as e:
    fatal(f"kan serial device niet openen: {e}")

print("Evohome CH MITM gestart")
print(f"Device        : {SERIAL_DEVICE}")
print(f"Controller ID : {controller_id}")
print(f"OTB ID        : {otb_id}")
print(f"MAX_CH_RAW    : {max_ch_raw} ({max_ch_raw/2:.1f}°C)")
print(f"IDLE_CH_RAW   : {idle_ch_raw} ({idle_ch_raw/2:.1f}°C)")

# ─────────────────────────────────────────────────────────────
# Main loop (fail-safe)
# ─────────────────────────────────────────────────────────────
while True:
    raw = b""
    try:
        raw = ser.readline()
        if not raw:
            continue

        frame = decode_ramses_line(raw)
        if frame is None:
            # Onbekend formaat → pass-through
            ser.write(raw)
            continue

        if is_relevant_ch_setpoint(frame, controller_id, otb_id):
            ch_raw = get_ch_raw(frame)

            # Idle → altijd transparant
            if ch_raw <= idle_ch_raw:
                ser.write(raw)
                continue

            # Statische bovengrens
            if ch_raw > max_ch_raw:
                frame = set_ch_raw(frame, max_ch_raw)
                raw = encode_ramses_frame(frame)

        ser.write(raw)

    except Exception:
        # Fail-safe: probeer wat je had door te zetten
        try:
            if raw:
                ser.write(raw)
        except Exception:
            pass
        time.sleep(0.1)
