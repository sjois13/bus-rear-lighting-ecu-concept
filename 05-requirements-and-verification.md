# 05 Requirements and Verification

Requirements are **solution-free and testable**: they state what the ECU does at its connector, not which part does it, and they promise only what the diagnostics can actually deliver. Values marked ASSUMPTION stand in for the vehicle specification. Each row carries the attributes a DOORS module would hold.

## Component requirements (ECU)

| ID | Requirement | From | Safety-relevant | Verified by |
|---|---|---|---|---|
| ECU-01 | The ECU shall operate without functional deviation from 18 V to 32 V at the supply connector (ASSUMPTION) and survive the suppressed load-dump pulse of the vehicle supply specification without damage. | SYS-01 | — | VT-01 |
| ECU-02 | The ECU shall withstand reverse supply voltage per the vehicle supply specification without damage and without energizing any output. | SYS-01 | — | VT-01 |
| ECU-03 | The ECU shall switch each lamp output within 50 ms (ASSUMPTION) of a valid CAN request, and only the requested outputs shall energize. | SYS-02, SYS-03 | — | VT-02, VT-08 |
| ECU-04 | With an output ON, the ECU shall report an open lamp or open wire within 200 ms (ASSUMPTION) for any lamp meeting LMP-01, without false reports. The ECU is not required to detect partial failure inside a lamp (see LMP-04). | SYS-04 | Yes (stop, turn) | VT-03 |
| ECU-05 | With an output OFF, the ECU shall detect an output short to battery at wake-up and at least every 10 s while awake (ASSUMPTION). For lamps declared conductive under LMP-02, it shall also detect an open load in this state. The check shall cause no visible light from a lamp meeting LMP-03. | SYS-04 | — | VT-05, VT-03 |
| ECU-06 | On an output short to ground, the ECU shall limit the fault, switch the output off after at most 3 retries (ASSUMPTION), report the fault, and keep the fault energy within the limits of the vehicle harness specification. | SYS-04 | — | VT-04 |
| ECU-07 | The ECU shall report output state and a per-channel fault code (open load, short to GND, short to battery, overtemperature) over CAN. | SYS-03, SYS-04 | Yes (turn tell-tale) | VT-03–05, VT-08 |
| ECU-08 | The stop outputs shall follow the hardwired brake input within 20 ms (ASSUMPTION), independently of CAN, MCU operation and the logic supply, whenever the supply connector is within ECU-01 limits. | SYS-05 | Yes | VT-09 |
| ECU-09 | The ECU shall report a mismatch between the hardwired brake input and the CAN brake signal lasting longer than 500 ms (ASSUMPTION). | SYS-05 | Yes | VT-09 |
| ECU-10 | After 500 ms without valid CAN lighting messages (ASSUMPTION), the ECU shall switch tail outputs on, drive stop outputs only from the brake input, and switch turn outputs off. | SYS-05 | Yes | VT-08 |
| ECU-11 | No single fault inside the ECU, other than loss of supply or ground, shall disable both stop outputs or both turn outputs. | SYS-06 | Yes | Analysis (doc 04) + VT-10 |
| ECU-12 | All components shall stay within their rated limits with all six outputs at maximum lamp load, 32 V supply and 85 °C ambient (ASSUMPTION). | SYS-01 | — | VT-06 |
| ECU-13 | Sleep current shall not exceed 100 µA (ASSUMPTION) at 28 V with all outputs off. | SYS-07 | — | VT-07 |
| ECU-14 | The ECU shall wake from sleep on a CAN wake-up pattern or an active brake input and report its status over CAN within 200 ms (ASSUMPTION). | SYS-07 | — | VT-07 |

## Lamp-interface requirements (for the lamp specification / Lastenheft)

The diagnostics depend on how the lamp behaves electrically. These requirements belong in the lamp supplier's specification.

| ID | Requirement | Reason | Reference lamp |
|---|---|---|---|
| LMP-01 | Each lamp function shall draw at least 20 mA when energized, over 18–32 V and the full temperature range. | 1.33× the switch's 15 mA maximum open-load threshold | Meets it: 21.9 mA minimum |
| LMP-02 | The supplier shall state minimum and maximum current over voltage and temperature, the driver topology, and whether the lamp conducts when fed through 1.5 kΩ with the function off. | Sets the ECU's sense windows and whether OFF-state open-load detection applies | To be stated |
| LMP-03 | The lamp shall emit no visible light when fed from 32 V through 1.5 kΩ for up to 2 ms. | Allows the OFF-state diagnostic window | To be confirmed |
| LMP-04 | A multi-string lamp shall either change its current by an agreed minimum when one string fails, or report the failure itself. | The ECU's ± 50 % sense accuracy cannot see partial failure | To be agreed |

## Verification plan

| Test | Setup and stimulus | Record | Pass criterion |
|---|---|---|---|
| VT-01 Supply | Steady state 18 / 28 / 32 V; suppressed load dump per specification; reverse polarity | P_VBAT, logic rails, reset, outputs, raw waveforms | No damage; outputs as commanded; nothing energizes under reverse polarity |
| VT-02 Channel control | Each channel alone; then all six | CAN timestamp vs output edge, terminal voltage, current | Correct channel only; latency ≤ 50 ms |
| VT-03 Open load | Disconnect each lamp, output ON; repeat at 18 / 28 / 32 V with resistive, linear and constant-power reference lamps; OFF-state check on declared-conductive lamps | Sense, flag, CAN fault, detection time, lamp light output | Open reported ≤ 200 ms; **no false report with any reference lamp**; no visible glow |
| VT-04 Short to GND | Current-limited fixture, then the real harness and fuse | Peak / steady current, retries, latch, fuse I²t vs wire | Off after ≤ 3 retries; energy within harness limit; reported |
| VT-05 Short to battery | Back-feed each output while off | Output voltage, CAN report, other channels | Reported; no other channel affected |
| VT-06 Thermal | All six at maximum load, 32 V, 85 °C until stable | Device, PCB, connector temperatures | Within ratings with the agreed margin |
| VT-07 Sleep and wake | Sleep at 28 V; then wake by CAN, then by brake input | Sleep current per block; time to first status frame | ≤ 100 µA; status ≤ 200 ms after each wake source |
| VT-08 CAN | Valid, malformed and unsupported frames; bus interruption | Outputs, status frames, timing | Correct mapping; fallback per ECU-10; recovery on next valid message |
| VT-09 Brake path | Brake toggled: normal, CAN off, MCU held in reset, **ECU asleep with logic rails off**; brake input vs CAN mismatch | Stop output timing, mismatch report | Stop follows input ≤ 20 ms in every mode; mismatch reported |
| VT-10 Fault injection | Disable U1, then U2 (inputs held low / VS opened) | Which lamps remain | One stop, one turn and one tail lamp remain each time |

Short-circuit and supply tests capture raw waveforms; pass/fail alone does not show the protection energy.

## Traceability

| SYS | ECU | Lamp spec | Test |
|---|---|---|---|
| SYS-01 | ECU-01, -02, -12 | — | VT-01, VT-06 |
| SYS-02 | ECU-03 | — | VT-02 |
| SYS-03 | ECU-03, -07 | — | VT-02, VT-08 |
| SYS-04 | ECU-04, -05, -06, -07 | LMP-01–04 | VT-03, VT-04, VT-05 |
| SYS-05 | ECU-08, -09, -10 | — | VT-08, VT-09 |
| SYS-06 | ECU-11 | — | VT-10 |
| SYS-07 | ECU-13, -14 | — | VT-07 |

Every SYS requirement traces to at least one ECU requirement and one test, and every test traces back. Open gap, flagged deliberately: the watchdog has no requirement of its own until its timing is defined; VT-09 (MCU held in reset) covers its effect on the stop function.
