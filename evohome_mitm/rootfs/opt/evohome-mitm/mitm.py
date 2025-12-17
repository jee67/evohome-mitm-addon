#!/usr/bin/env python3
import os
import sys
import json
import time
import threading
import serial
import paho.mqtt.client as mqtt

from ramses_codec import (
    decode_ramses_line,
    encode_ramses_frame,
    is_relevant_ch_setpoint,
    get_ch_raw,
    set_ch_raw,
)

# ─────────────────────────────────────────────────────────────
# Config
# ─────────────────────────────────────────────────────────────

OPTIONS_FILE = "/data/options.json"
SERIAL_DEVICE = "/dev/serial/by-id/usb-FTDI_FT232R_USB_UART_A50285BI-if00-port0"
BAUDRATE = 115200

MQTT_TOPIC_MAX_CH = "evohome/mitm/max_ch_raw"

RAW_MIN = 30
RAW_MAX = 130

# Ramping
RAMP_STEP_RAW = 4          # +2.0 °C
RAMP_INTERVAL_SEC = 30     # per 30 s

# ─────────────────────────────────────────────────────────────
# Logging banner
# ─────────────────────────────────────────────────────────────

print("=== Evohome MITM gestart (2-richting, ramping actief) ===", flush=True)
print(sys.version, flush=True)

# ─────────────────────────────────────────────────────────────
# Config laden
# ─────────────────────────────────────────────────────────────

with open(OPTIONS_FILE, "r") as f:
    options = json.load(f)

controller_id = options.get("controller_id")
otb_id = options.get("otb_id")

idle_ch_raw = int(options.get("idle_ch_raw", 20))
max_ch_raw_static = int(options.get("max_ch_raw", 90))

mqtt_host = options.get("mqtt_host", "10.0.0.190")
mqtt_port = int(options.get("mqtt_port", 1883))
mqtt_timeout = int(options.get("mqtt_timeout_sec", 1800))

# ─────────────────────────────────────────────────────────────
# MQTT state
# ─────────────────────────────────────────────────────────────

mqtt_max_ch_raw = None
mqtt_last_update = 0

def effective_max_ch_raw():
    if mqtt_max_ch_raw is not None:
        if time.time() - mqtt_last_update <= mqtt_timeout:
            return mqtt_max_ch_raw
    return max_ch_raw_static

def on_mqtt_message(client, userdata, msg):
    global mqtt_max_ch_raw, mqtt_last_update
    try:
        v = int(msg.payload.decode().strip())
        if RAW_MIN <= v <= RAW_MAX:
            mqtt_max_ch_raw = v
            mqtt_last_update = time.time()
            print(f"MQTT override max_ch_raw={v}", flush=True)
    except Exception:
        pass

def mqtt_thread():
    client = mqtt.Client()
    client.on_message = on_mqtt_message
    try:
        client.connect(mqtt_host, mqtt_port, 60)
        client.subscribe(MQTT_TOPIC_MAX_CH)
        client.loop_forever()
    except Exception as e:
        print(f"MQTT niet beschikbaar: {e}", flush=True)

threading.Thread(target=mqtt_thread, daemon=True).start()

# ─────────────────────────────────────────────────────────────
# Ramping state
# ─────────────────────────────────────────────────────────────

last_sent_ch_raw = None
last_sent_ts = 0

def apply_ramping(target_raw):
    global last_sent_ch_raw, last_sent_ts
    now = time.time()

    if last_sent_ch_raw is None:
        last_sent_ch_raw = target_raw
        last_sent_ts = now
        return target_raw

    # idle of daling → direct
    if target_raw <= idle_ch_raw or target_raw <= last_sent_ch_raw:
        last_sent_ch_raw = target_raw
        last_sent_ts = now
        return target_raw

    elapsed = now - last_sent_ts
    steps = int(elapsed / RAMP_INTERVAL_SEC)
    if steps <= 0:
        return last_sent_ch_raw

    max_up = steps * RAMP_STEP_RAW
    new_raw = min(target_raw, last_sent_ch_raw + max_up)

    if new_raw != last_sent_ch_raw:
        last_sent_ch_raw = new_raw
        last_sent_ts = now

    return new_raw

# ─────────────────────────────────────────────────────────────
# Serial open
# ─────────────────────────────────────────────────────────────

ser = serial.Serial(SERIAL_DEVICE, BAUDRATE, timeout=0.1)
print(f"Serial open: {SERIAL_DEVICE}", flush=True)

# ─────────────────────────────────────────────────────────────
# Main loop — ALWAYS FORWARD
# ─────────────────────────────────────────────────────────────

while True:
    raw = b""
    try:
        raw = ser.readline()
        if not raw:
            continue

        frame = decode_ramses_line(raw)
        if frame is None:
            ser.write(raw)
            continue

        # Alleen 1F09 controller → OTB muteren
        if is_relevant_ch_setpoint(frame, controller_id, otb_id):
            ch_raw = get_ch_raw(frame)

            limit = effective_max_ch_raw()
            target = min(ch_raw, limit)
            ramped = apply_ramping(target)

            if ramped != ch_raw:
                frame = set_ch_raw(frame, ramped)
                raw = encode_ramses_frame(frame)
                print(
                    f"MUTATE CH {ch_raw/2:.1f} → {ramped/2:.1f} °C",
                    flush=True,
                )

        # 🔑 ALTJD exact één write
        ser.write(raw)

    except Exception as e:
        # absolute failsafe
        try:
            if raw:
                ser.write(raw)
        except Exception:
            pass
        print(f"EXCEPTION (pass-through): {e}", flush=True)
        time.sleep(0.05)
