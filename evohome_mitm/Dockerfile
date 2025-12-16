FROM python:3.11-slim

RUN pip install --no-cache-dir pyserial

COPY rootfs/ /

CMD ["python3", "/opt/evohome-mitm/mitm.py"]
