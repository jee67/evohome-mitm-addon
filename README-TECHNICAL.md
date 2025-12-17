# Evohome CH MITM Add-on – Technical Documentation

## Doel

Deze add-on implementeert een **RAMSES-II man-in-the-middle (MITM)**
die uitsluitend het **CH setpoint (verb 1F09)** muteert
en verder **volledig transparant** is.

De Evohome controller blijft de primaire ruimteregelaar.

---

## Architectuur

Evohome Controller
│ (RF 868 MHz)
▼
R8810A ── bedraad ──► CiC ──► Ketel
▲
│
evofw3 USB stick + MITM

- R8810A blijft de enige gateway naar de CiC
- MITM beïnvloedt alleen RF-authority, geen bekabeling
- Geen herpairing vereist

---

## Protocolgedrag

- **Altijd exact één forward per ontvangen frame**
- Geen filtering of dropping
- Mutatie uitsluitend op:
  - `1F09` (Requested CH flow temperature)
- Alle `RP`, `I`, status- en meettelegrammen blijven intact

---

## Ramping / Rate limiting

Om hydraulische onrust te voorkomen:

- Stijging: max **+2.0 °C per 30 s**
- Daling: direct toegestaan
- Idle → warmtevraag verloopt geleidelijk

Dit voorkomt sprongen zoals 10 → 42 °C.

---

## MQTT override

- Topic: `evohome/mitm/max_ch_raw`
- Payload: integer (raw, 30–130)
- Timeout: configureerbaar
- Bij timeout → fallback naar statische `max_ch_raw`

---

## Fail-safe ontwerp

- Add-on stopt → volledige pass-through
- USB los → Evohome neemt over
- Exceptions → frame wordt alsnog doorgestuurd

> Correctie is toegestaan, filtering niet.

---

## Logging

- Logging via Supervisor stdout
- Bekijken via:
  ```bash
  ha addons logs 991b9a16_evohome_mitm
