# 24 V Bus Rear-Lighting ECU: Concept Study

**Author:** [Your name] · **Rev B**, October 2026 · Self-directed work sample

## What this is

A component-level concept for an ECU that switches and diagnoses six rear-lamp functions (tail, stop, turn; left and right) on a 24 V bus, commanded over CAN. It covers architecture, power and wake-up, the output stage down to a reference circuit with part values, the safety-relevant design decisions, and solution-free requirements traced to verification.

All numbers come from one calculation script (`calc/design_calcs.py`), so every claim can be re-run and checked.

## Key decisions

| # | Decision | Why |
|---|---|---|
| D1 | Output stage: **two quad smart high-side switches (Infineon BTT6200-4ESA)**, replacing the first candidate (BTT6030-2ERB) | The first candidate's open-load threshold (≤ 25 mA) sits on top of the tail-lamp current; the quad's (≤ 15 mA) leaves margin in every case (finding 1) |
| D2 | Channel allocation: no device carries both stop lamps, both turn lamps, both tail lamps, or all red functions of one side. Two spare channels | A single device failure never removes a whole function; the spares take reverse and rear fog without a new design |
| D3 | **Passive brake path:** the 24 V brake signal drives the stop-channel inputs through a zener-clamped diode-OR, and also wakes the ECU | Stop lamps work with CAN lost, the MCU in reset, or the logic rails off |
| D4 | CAN transceiver supplied from the battery rail in sleep; its INH output enables the logic supply on wake | The ECU can sleep at ~53 µA and still wake on CAN or the brake input |
| D5 | OFF-state open-load pull-ups **switched**, enabled only for a short diagnostic window | A permanent 1.5 kΩ pull-up drives ~12 mA into an LED tail lamp (visible glow) and 112 mA total in sleep |
| D6 | Lamp interface: minimum lamp current **≥ 20 mA** over 18–32 V, stated by the lamp supplier with the driver topology | The diagnostic only works if the lamp's current range is known; the reference lamp (21.9 mA minimum) meets it |

## Key findings

1. **The first switch candidate failed its own diagnostic check.** A 24 V bus runs at about 28 V with the alternator charging. There, a 0.7 W tail lamp with a constant-power LED driver draws 25.0 mA, exactly the BTT6030's maximum open-load threshold; a resistive lamp drops to 21.9 mA at 18 V. An intact lamp could be reported as open. The BTT6200-4ESA's 5–15 mA threshold gives +6.9 mA margin (1.46×) for every lamp model and voltage, so the part was changed (D1).
2. **The protection margin is thinner than the part ratings suggest.** The switches and the front-end controller are rated 65 V. The centrally suppressed 24 V load dump is 58 V or 65 V depending on edition and OEM, which leaves +7 V or **zero** headroom. The vehicle supply specification decides whether a local clamp stage is needed.
3. **The output stage is bias-limited, not load-limited.** Per quad device, lamp conduction loss is 43 mW, while the device's own supply current costs 288 mW at 32 V. The junction stays near 98 °C at 85 °C ambient.

## Contents

| Doc | Content |
|---|---|
| 01 System architecture | Scope, boundary, interfaces, operating cases, system requirements |
| 02 Power, wake and control | Input protection, logic supply, sleep and wake-up, CAN |
| 03 Output stage | Device selection, allocation, diagnostics, sense chain, reference circuit |
| 04 Safety-relevant design decisions | Brake path, CAN fallback, single-fault behaviour, residual risks |
| 05 Requirements and verification | ECU and lamp-interface requirements, test plan, traceability |

## Scope and honesty statement

This is a concept study, not a built product. Datasheet values come from the Infineon and TI documents cited. Values marked **ASSUMPTION** (voltage window, timeouts, sleep budget, logic loads, package thermal resistance) stand in for a vehicle specification I don't have. Vehicle-level safety goals and ASIL ratings belong to the OEM's HARA; doc 04 states only the working assumption the design follows.
