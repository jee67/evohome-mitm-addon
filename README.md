# Evohome CH MITM Add-on - Evohome man-in-the-middle

Home Assistant add-on die als RAMSES-II man-in-the-middle fungeert om het CH setpoint (verb 1F09)
statisch te begrenzen. Idle-setpoint (10°C) blijft onaangeroerd. Fail-safe pass-through is ingebouwd.

## Installatie

1. Home Assistant → Instellingen → Add-ons → Add-on Store → Repositories
2. Voeg toe: https://github.com/<jouw-account>/<jouw-repo>
3. Add-on Store → ⋮ → Reload
4. Installeer **Evohome CH MITM**
5. Configureer controller_id / otb_id / max_ch_raw / idle_ch_raw
6. Start add-on

## Configuratie

- controller_id: bijv. `01:033496`
- otb_id: bijv. `10:061315`
- max_ch_raw: bijv. `100` (= 50.0°C)
- idle_ch_raw: bijv. `20` (= 10.0°C)

## Rollback / Noodprocedure

- Stop de add-on (Add-ons → Evohome CH MITM → Stop)
- Eventueel USB-stick herpluggen
- Daarna kan een andere integratie de stick weer gebruiken

## Opmerking

USB-binding is bewust vast om conflicten met andere dongles (zoals FanX/MySensors) te voorkomen.
