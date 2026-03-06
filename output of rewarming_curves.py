>>> %Run rewarming_curves.py
Parameters: RewarmingParams(t_start=4.0, t_end=27.0, t_total=30.0, max_gradient=1.0)
Current curve functions:
  - sine_uncontrolled: T(t)=T0+ΔT*sin((π/2)*(t/τ))
  - linear: T(t)=T0+ΔT*(t/τ)
  - sine_stretched_controlled: T(t)=T0+ΔT*sin((π/2)*(t/τ)^1.5)
  - exponential: T(t)=T0+ΔT*(((1.5)^(t/τ)-1)/(1.5-1))
Current numeric functions:
  - Sine (uncontrolled): T(t)=4.000+23.000*sin(0.052360*t)
  - Linear: T(t)=4.000+0.767*t
  - Stretched sine (controlled): T(t)=4.000+23.000*sin(1.570796*(t/30.000)^1.5)
  - Exponential: T(t)=4.000+46.000*(1.5^(t/30.000)-1)
sine_uncontrolled                  | peak_rate=1.000 °C/min | midpoint=(20.263 °C, 0.707 °C/min) | safety_t_total=36.13 min
linear                             | peak_rate=0.767 °C/min | midpoint=(15.500 °C, 0.767 °C/min) | safety_t_total=30.00 min
sine_stretched_controlled          | peak_rate=1.000 °C/min | midpoint=(16.127 °C, 1.000 °C/min) | safety_t_total=32.56 min
exponential                        | peak_rate=0.933 °C/min | midpoint=(14.338 °C, 0.761 °C/min) | safety_t_total=30.00 min
