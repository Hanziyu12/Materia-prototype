# Rewarming Curve Design (4 → 27 °C over 30 min, configurable)

This note defines 4 mathematical rewarming algorithms and how to convert **target temperature** into **instantaneous warming rate** for control design.

## 1) Common variables and normalization

Let:
- `T0` = start temperature (°C), e.g., 4
- `Tf` = end temperature (°C), e.g., 27
- `tau` = total time (min), e.g., 30
- `ΔT = Tf - T0`
- `u = t/tau`, where `t ∈ [0, tau]` and `u ∈ [0,1]`

Every curve is written as:

\[
T(t) = T_0 + \Delta T \cdot f(u)
\]

with `f(0)=0` and `f(1)=1`.

The instantaneous warming rate is:

\[
\dot T(t) = \frac{dT}{dt} = \frac{\Delta T}{\tau} f'(u)
\]

This is the exact quantity needed for control decisions.

---

## 2) Curve A — Sine (uncontrolled)

A simple monotonic sine ramp:

\[
f_A(u) = \sin\left(\frac{\pi}{2}u\right)
\]

So:

\[
T_A(t) = T_0 + \Delta T\sin\left(\frac{\pi}{2}\frac{t}{\tau}\right)
\]

\[
\dot T_A(t) = \frac{\Delta T}{\tau}\frac{\pi}{2}\cos\left(\frac{\pi}{2}\frac{t}{\tau}\right)
\]

Properties:
- fastest at the beginning;
- naturally slows near the endpoint;
- often exceeds slope constraints unless time is extended.

---

## 3) Curve B — Linear

\[
f_B(u) = u
\]

\[
T_B(t)=T_0+\Delta T\frac{t}{\tau}
\]

\[
\dot T_B(t)=\frac{\Delta T}{\tau}
\]

Properties:
- constant warming rate;
- easiest to implement;
- valid if average slope `ΔT/tau` stays under safety limit.

---

## 4) Curve C — Stretched sine (controlled)

Use time-warping with exponent `β > 1` to reduce early slope:

\[
f_C(u)=\sin\left(\frac{\pi}{2}u^{\beta}\right)
\]

\[
T_C(t)=T_0+\Delta T\sin\left(\frac{\pi}{2}\left(\frac{t}{\tau}\right)^{\beta}\right)
\]

\[
\dot T_C(t)=\frac{\Delta T}{\tau}\frac{\pi}{2}\beta\left(\frac{t}{\tau}\right)^{\beta-1}
\cos\left(\frac{\pi}{2}\left(\frac{t}{\tau}\right)^{\beta}\right)
\]

Properties:
- more “controlled” than basic sine;
- starts gently for `β>1`;
- can be tuned to keep \(\dot T\) under 1 °C/min.

---

## 5) Curve D — Normal exponential (below linear)

Use a standard exponential form with base `b>1`, normalized on `[0,1]`:

\[
f_D(u)=\frac{b^u-1}{b-1},\quad b>1
\]

\[
T_D(t)=T_0+\Delta T\frac{b^{t/\tau}-1}{b-1}
\]

\[
\dot T_D(t)=\frac{\Delta T}{\tau}\frac{\ln(b)\,b^{t/\tau}}{b-1}
\]

Properties:
- starts gently and accelerates later;
- mostly below the linear curve for `0<u<1`;
- `b` controls curvature (`b=1.5` is a mild exponential shape).

---

## 6) Safety constraint (max 1 °C/min)

Constraint:

\[
|\dot T(t)| \le G_{max}=1\;\text{°C/min}
\]

For each curve, estimate peak slope:

\[
\dot T_{peak}=\max_{t\in[0,\tau]} |\dot T(t)|
\]

If \(\dot T_{peak} > G_{max}\), increase total time:

\[
\tau_{new}=\tau\cdot\frac{\dot T_{peak}}{G_{max}}
\]

This gives a first-pass feasibility adjustment before experiments.

---

## 7) How to use these curves in code/control

At runtime (every control step):
1. Compute target `T_target(t)` from selected curve.
2. Compute target slope `r_target(t)=dT/dt` from derivative.
3. Compare actual measured organ slope `r_meas`.
4. Adjust actuator (bag/fluid temperature difference, flow, heater power) to move `r_meas → r_target`.

### Interpreting the “3 K contrast gradient” idea

A practical model is:

\[
r \approx K\,(T_{bag}-T_{organ})
\]

where:
- `r` is organ warming rate (°C/min),
- `K` is experimentally identified gain (°C/min per °C).

If operation policy is “do not exceed 1 °C/min”, then command:

\[
r_{cmd}=\min(r_{target},1)
\]

and infer needed contrast:

\[
\Delta T_{bag-organ,cmd}=\frac{r_{cmd}}{K}
\]

Then cap by a maximum allowed bag-organ delta (e.g., 3 K if that is your validated limit).

---

## 8) Assumptions used

- Organ behaves as a lumped thermal mass over short intervals.
- Warming dynamics are monotonic and smooth.
- Derivatives represent intended slope, not guaranteed slope (real system lags).
- Sensor noise is filtered enough to estimate `dT/dt`.

---

## 9) What to test next (to move toward implementation)

1. **Identify plant gain `K`** across temperatures and flow rates.
2. **Check linearity** of `r` vs `(T_bag - T_organ)` and detect saturation.
3. **Measure delay/time constant** from step changes in bag temperature.
4. **Validate slope limit** with real tissue variability (not only benchtop surrogate).
5. **Tune curve parameters**:
   - `β` for stretched sine,
   - `b` for exponential,
   to satisfy outcome vs safety trade-offs.
6. **Closed-loop simulation** with sensor noise + delay + actuator limits.
7. **Fail-safe checks**: hard clamp on commanded rate, bag temperature, and delta-T.

---

## 10) Reference implementation in this repo

See `rewarming_curves.py` for:
- all 4 curve functions,
- analytic derivatives,
- peak-rate checks,
- computed minimum duration to satisfy max gradient.

Run:

```bash
python3 rewarming_curves.py
```

