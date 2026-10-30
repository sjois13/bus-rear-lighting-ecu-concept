"""
Design calculations: 24 V rear-lighting ECU (concept study, Rev B)

Every number quoted in the portfolio documents comes from this script.
Run:  python3 design_calcs.py

Datasheet values: Infineon BTT6030-2ERA/-2ERB and BTT6200-4ESA datasheets
(verify against the current English revisions before relying on them).
Values marked ASSUMPTION are budget allocations or placeholders for the
vehicle specification and must be replaced.
"""

# --------------------------------------------------------------------------
# 1. Supply operating points (24 V vehicle system)
# --------------------------------------------------------------------------
V_MIN = 18.0      # ASSUMPTION: low end of normal operation (cranking excluded)
V_NOM = 28.0      # ISO 16750-2 UA for 24 V systems (alternator running)
V_MAX = 32.0      # ASSUMPTION: upper end of normal operation
V_LABEL = 24.0    # nameplate voltage, used by the lamp catalogue
V_POINTS = (V_MIN, V_NOM, V_MAX)

# --------------------------------------------------------------------------
# 2. Lamp loads (HELLA catalogue example, rated at 24 V)
# --------------------------------------------------------------------------
LAMPS = {"tail": 0.7, "stop": 5.0, "turn": 3.0}   # W per lamp at 24 V
MODELS = ("resistive", "linear", "const_p")

def lamp_current(p_rated, v, model):
    """resistive: I ~ V | linear: I constant | const_p: I = P / V"""
    i24 = p_rated / V_LABEL
    return {"resistive": i24 * v / V_LABEL, "linear": i24, "const_p": p_rated / v}[model]

def i_min(lamp):
    return min(lamp_current(LAMPS[lamp], v, m) for v in V_POINTS for m in MODELS)

def i_max(lamp):
    return max(lamp_current(LAMPS[lamp], v, m) for v in V_POINTS for m in MODELS)

# --------------------------------------------------------------------------
# 3. Candidate output devices (datasheet values)
# --------------------------------------------------------------------------
BTT6030 = dict(name="BTT6030-2ERB (2 ch)", il_ol=(4e-3, 25e-3), i_lim_min=40.0)
BTT6200 = dict(name="BTT6200-4ESA (4 ch)", il_ol=(5e-3, 15e-3), i_lim_min=9.0,
               rds_on_150=0.400,            # ohm, max at Tj = 150 C
               ignd_max=9e-3, ignd_typ=6e-3,  # A, all channels ON, VS = 36 V
               is_off_max=0.5e-6,           # A standby, Tj <= 85 C
               kilis=330,                   # typ (spec point 10 mA)
               kilis_acc_low=0.50,          # +-50 % at 10 mA
               kilis_acc_hi=0.11)           # +-11 % at 0.5 A
RTH_JA_ASSUMED = 40.0   # K/W ASSUMPTION for the quad package on a 4-layer board
N_DEV = 2

# --------------------------------------------------------------------------
# 4. Design choices
# --------------------------------------------------------------------------
R_IS = 1.2e3
ADC_VREF, ADC_BITS = 3.3, 12
I_LAMP_MAX_VARIANT = 0.5     # A, largest lamp variant a channel must measure
LMP01_I_MIN = 20e-3          # lamp-interface requirement

def hr(t):
    print("\n" + t + "\n" + "-" * len(t))

# ---- A. Loads ----------------------------------------------------------------
hr("A. Lamp currents (mA) by lamp model")
print(f"{'lamp':5} {'model':10}" + "".join(f"{v:>8.0f} V" for v in V_POINTS))
for lamp, p in LAMPS.items():
    for m in MODELS:
        print(f"{lamp:5} {m:10}" + "".join(f"{lamp_current(p, v, m)*1e3:9.1f}" for v in V_POINTS))
for lamp in LAMPS:
    print(f"{lamp}: min {i_min(lamp)*1e3:.1f} mA, max {i_max(lamp)*1e3:.1f} mA over all models and voltages")
p_total = 2 * sum(LAMPS.values())
print(f"All six ON (tail+stop+hazard): {p_total:.1f} W = {p_total/V_LABEL:.3f} A at 24 V")

# ---- B. Tail lamp vs open-load threshold, both candidates ---------------------
hr("B. Tail lamp vs ON-state open-load threshold (max)")
for dev in (BTT6030, BTT6200):
    th = dev["il_ol"][1]
    imin = i_min("tail")
    print(f"{dev['name']}: threshold max {th*1e3:.0f} mA, tail min {imin*1e3:.1f} mA "
          f"-> margin {(imin-th)*1e3:+.1f} mA, ratio {imin/th:.2f}x")
    worst = [(lamp_current(0.7, v, m), m, v) for v in V_POINTS for m in MODELS
             if lamp_current(0.7, v, m) <= th]
    print("   cases at/below threshold: " + (", ".join(f"{m} @ {v:.0f} V ({i*1e3:.1f} mA)" for i, m, v in worst) or "none"))
print(f"LMP-01 limit {LMP01_I_MIN*1e3:.0f} mA = {LMP01_I_MIN/BTT6200['il_ol'][1]:.2f}x BTT6200 max threshold; "
      f"reference tail min {i_min('tail')*1e3:.1f} mA meets it: {i_min('tail') >= LMP01_I_MIN}")

# ---- C. Short-circuit limit vs lamp current ----------------------------------
hr("C. Current limit vs largest lamp current")
for dev in (BTT6030, BTT6200):
    print(f"{dev['name']}: I_lim min {dev['i_lim_min']:.0f} A = {dev['i_lim_min']/i_max('stop'):.0f}x worst stop current")

# ---- D. Sense chain (BTT6200) --------------------------------------------------
hr(f"D. Current sense, BTT6200, R_IS = {R_IS/1e3:.1f} k")
d = BTT6200
lsb = ADC_VREF / 2**ADC_BITS
iis_max = I_LAMP_MAX_VARIANT / (d["kilis"] * (1 - d["kilis_acc_hi"]))
print(f"ADC LSB {lsb*1e3:.3f} mV")
print(f"0.5 A variant, kILIS -11 %: IIS {iis_max*1e3:.2f} mA -> VIS {iis_max*R_IS:.2f} V (< 3.3 V); "
      f"R_IS max for 3.0 V: {3.0/iis_max/1e3:.2f} k")
for lamp in LAMPS:
    for label, i in (("min", i_min(lamp)), ("max", i_max(lamp))):
        typ = i / d["kilis"] * R_IS
        lo = i / (d["kilis"] * (1 + d["kilis_acc_low"])) * R_IS
        hi = i / (d["kilis"] * (1 - d["kilis_acc_low"])) * R_IS
        print(f"  {lamp:4} {label} {i*1e3:6.1f} mA: VIS {lo*1e3:6.0f} / {typ*1e3:6.0f} / {hi*1e3:6.0f} mV "
              f"({typ/lsb:5.0f} LSB typ)")
print(f"Sense RC with 100 pF: tau {R_IS*100e-12*1e9:.0f} ns")
v_sat = V_NOM - 1.0
print(f"Fault saturation (IS ~ VS - 1 V = {v_sat:.0f} V) through 10 k into clamp: {(v_sat-3.6)/10e3*1e3:.1f} mA per device, "
      f"{N_DEV*(v_sat-3.6)/10e3*1e3:.1f} mA total into 3.3 V rail")

# ---- E. Thermal ------------------------------------------------------------------
hr("E. Losses per quad device (U1: STOP_L, TURN_R, TAIL_R)")
cond = sum(i_max(l)**2 * d["rds_on_150"] for l in ("stop", "turn", "tail"))
bias = d["ignd_max"] * V_MAX
per = cond + bias
print(f"Conduction (worst currents, 400 mOhm @150 C): {cond*1e3:.1f} mW")
print(f"Bias I_GND x VS (9 mA x 32 V): {bias*1e3:.0f} mW")
print(f"Total {per*1e3:.0f} mW -> dTj {per*RTH_JA_ASSUMED:.1f} K at {RTH_JA_ASSUMED:.0f} K/W (ASSUMPTION) "
      f"-> Tj {85+per*RTH_JA_ASSUMED:.0f} C at 85 C ambient")
print(f"Both devices bias typ {N_DEV*d['ignd_typ']*V_NOM*1e3:.0f} mW @28 V")

# ---- F. OFF-state pull-up vs LED glow -----------------------------------------
hr("F. OFF-state open-load pull-up (1.5 k) into a tail lamp")
r_lamp = V_LABEL**2 / LAMPS["tail"]
for v in (V_NOM, V_MAX):
    i = v / (1.5e3 + r_lamp)
    print(f"VS {v:.0f} V: {i*1e3:.1f} mA ({i/lamp_current(0.7, v, 'resistive')*100:.0f} % of ON current)")
print(f"Six permanent pull-ups at 28 V: {6*V_NOM/1.5e3*1e3:.0f} mA")

# ---- G. Logic supply ---------------------------------------------------------------
hr("G. Logic supply budget (ASSUMPTION allocations)")
i33 = 40e-3 + 2e-3 + 1e-3
i5 = 70e-3 + i33
pin = 5.0 * i5 / 0.80
print(f"3.3 V {i33*1e3:.0f} mA, LDO loss {(5-3.3)*i33*1e3:.0f} mW; 5 V {i5*1e3:.0f} mA = {5*i5:.2f} W")
print(f"Buck input {pin:.2f} W: {pin/V_NOM*1e3:.0f} mA @28 V, {pin/V_MIN*1e3:.0f} mA @18 V; LM5164 1 A margin {1/i5:.1f}x")

# ---- H. Sleep current -----------------------------------------------------------------
hr("H. Sleep budget (100 uA allocation, ASSUMPTION)")
sleep = {"2x quad switch standby (max, <=85 C)": N_DEV * d["is_off_max"],
         "CAN transceiver sleep on VSUP (allocation)": 20e-6,
         "Front-end controller Iq (allocation)": 15e-6,
         "Buck disabled via INH (allocation)": 5e-6,
         "Brake input network, brake released (allocation)": 2e-6,
         "Dividers / leakage (allocation)": 10e-6}
for k, v in sleep.items():
    print(f"  {k:50} {v*1e6:5.1f} uA")
print(f"  {'TOTAL':50} {sum(sleep.values())*1e6:5.1f} uA")

# ---- I. Passive brake path ------------------------------------------------------------
hr("I. Passive brake path (no logic supply needed)")
R_B, V_Z, V_F = 22e3, 5.1, 0.3
for v in (V_MIN, V_MAX):
    iz = (v - V_Z) / R_B
    print(f"Brake {v:.0f} V: zener current {iz*1e3:.2f} mA, R_B loss {(v-V_Z)**2/R_B*1e3:.0f} mW, "
          f"IN-side level ~{V_Z - V_F:.1f} V")
print(f"MCU branch: 3.3 V - {V_F} V = {3.3-V_F:.1f} V at the IN network (check vs VIN(H) max)")

# ---- J. Load dump headroom -------------------------------------------------------------
hr("J. Load-dump headroom to 65 V parts")
for name, us in (("Test B, 58 V", 58.0), ("Test B, 65 V", 65.0), ("Test A min, 151 V", 151.0)):
    print(f"{name:18}: headroom {65-us:+4.0f} V")
