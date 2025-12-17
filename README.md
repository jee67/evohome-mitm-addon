# Evohome CH MITM Add-on

Home Assistant add-on die het **CH setpoint van Evohome begrenst**
via een RAMSES-II man-in-the-middle, zonder de Evohome-regeling zelf te wijzigen.

De add-on voorkomt onnodig hoge aanvoertemperaturen,
verbetert rendement en blijft volledig **fail-safe**.

---

## Wat doet deze add-on?

- Begrens het **CH setpoint (1F09)**
- Laat **idle (10 °C)** onaangeroerd
- Geen abrupte sprongen (soft-start)
- Volledig transparant: alle ketelmetingen blijven zichtbaar
- Bij stoppen neemt Evohome automatisch weer over

---

## Installatie

1. Home Assistant → **Instellingen → Add-ons → Add-on Store → Repositories**
2. Voeg toe: https://github.com/jee67/evohome-mitm-addon
3. Add-on Store → **⋮ → Reload**
4. Installeer **Evohome CH MITM**
5. Stel de configuratie in
6. Start de add-on

---

## Configuratie

- **controller_id**  
Voorbeeld: `01:033496`

- **otb_id**  
Voorbeeld: `10:061315`

- **max_ch_raw**  
Maximale CH-aanvoer (raw, halve graden)  
Voorbeeld: `100` = 50 °C

- **idle_ch_raw**  
Idle-setpoint  
Voorbeeld: `20` = 10 °C

---

## Rollback / Uitschakelen

- Stop de add-on
- Evohome werkt direct weer zoals voorheen
- Geen reset of herpairing nodig

---

## Opmerking

Deze add-on werkt met een vaste USB-binding
om conflicten met andere RF-dongles te voorkomen.
