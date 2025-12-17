FROM python:3.11-slim

RUN pip install --no-cache-dir pyserial paho-mqtt

COPY rootfs/ /

CMD ["python3", "-u", "/opt/evohome-mitm/mitm.py"]
