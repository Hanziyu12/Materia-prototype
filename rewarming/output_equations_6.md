>>> %Run rewarming_curves.py
Assumptions (first 4 curves): start=4.0, end=27.0, total=30.0 min
Numeric equations:
  - 1) Hyperbolic / negative exponential: T(t)=4.000+23.000*(1-exp(-5.000*t/30.000))/(1-exp(-5.000))
  - 2) Natural positive exponential: T(t)=4.000+23.000*(exp(5.000*t/30.000)-1)/(exp(5.000)-1)
  - 3) Linear (time-sensitive): T(t)=4.000+0.767*t  (0<=t<=30.0)
  - 4) Sigmoid: T(t)=4.000+23.000*norm_sigmoid(t/30.000, alpha=12.000)
  - 5) Kidney linear (1.0 °C/min): T(t)=4.000+1.000*t  (clamped at 27.000)
  - 6) Horse sperm linear (0.3 °C/min): T(t)=4.000+0.300*t  (clamped at 27.000)
1) Hyperbolic / negative exponential       | duration= 30.00 min | peak_rate=3.859 °C/min | midpoint=(25.255 °C, 0.317 °C/min)
2) Natural positive exponential            | duration= 30.00 min | peak_rate=3.859 °C/min | midpoint=(5.745 °C, 0.317 °C/min)
3) Linear (time-sensitive)                 | duration= 30.00 min | peak_rate=0.767 °C/min | midpoint=(15.500 °C, 0.767 °C/min)
4) Sigmoid                                 | duration= 30.00 min | peak_rate=2.311 °C/min | midpoint=(15.500 °C, 2.311 °C/min)
5) Kidney linear (1.0 °C/min)              | duration= 23.00 min | peak_rate=1.000 °C/min | midpoint=(15.500 °C, 1.000 °C/min)
6) Horse sperm linear (0.3 °C/min)         | duration= 76.67 min | peak_rate=0.300 °C/min | midpoint=(15.500 °C, 0.300 °C/min)
Saved plot: rewarming_curves.png

### 1. Hyperbolic / Negative Exponential

This curve starts fast and slows down as it approaches the target (decaying approach).
$$
.T(t) = 4 + 23 \cdot \frac{1 - e^{-5 \cdot \frac{t}{30}}}{1 - e^{-5}}
$$

$$
i.e. T(t) = 4 + 23 \cdot \frac{1 - e^{-k \cdot \frac{t}{30}}}{1 - e^{-k}}
$$



### 2. Natural Positive Exponential

This curve starts slowly and accelerates as it moves toward the target.
$$
\T(t) = 4 + 23 \cdot \frac{e^{5 \cdot \frac{t}{30}} - 1}{e^5 - 1}
$$

$$
i.e. T(t) = 4 + 23 \cdot \frac{1}{1 + e^{-\alpha (\frac{t}{30} - 0.5)}}
$$



### 3. Linear (Time-Sensitive)

A steady, constant increase designed to cover the 23°C span exactly in 30 minutes.
$$
\T(t) = 4 + 0.767t \quad \text{for } 0 \le t \le 30
$$

### 4. Sigmoid (S-Curve)

Starts slow, accelerates in the middle, and tapers off at the end. Note that $S(x)$ represents the normalized sigmoid function.
$$
\T(t) = 4 + 23 \cdot \sigma_{\text{norm}}\left(\frac{t}{30}, \alpha=12\right)
$$

### 5. Kidney Linear (Fixed Gradient)

A linear ramp at a fixed speed of **1.0°C/min**. It reaches the 27°C goal faster than the 30-minute window (at $t=23$).
$$
\T(t) = \min(4 + 1.0t, 27)
$$

### 6. Horse Sperm Linear (Fixed Gradient)

A slower linear ramp at **0.3°C/min**. This is much slower and would not reach 27°C within the 30-minute window.
$$
\T(t) = \min(4 + 0.3t, 27)
$$

------

### Comparison of Profiles

| **Equation Type** | **Initial Speed** | **Final Speed** | **Behavior**                   |
| ----------------- | ----------------- | --------------- | ------------------------------ |
| **Negative Exp**  | Fast              | Slow            | "Front-loaded" change          |
| **Positive Exp**  | Slow              | Fast            | "Back-loaded" change           |
| **Linear**        | Constant          | Constant        | Steady progress                |
| **Sigmoid**       | Slow              | Slow            | Smooth transition at both ends |

------

| **Curve Type**       | **Parameter to Change** | **To make it SHARPER** | **To make it FLATTER**  |
| -------------------- | ----------------------- | ---------------------- | ----------------------- |
| **Neg. Exponential** | k                       | Increase $k$           | Decrease $k$ (toward 0) |
| **Pos. Exponential** | k                       | Increase $k$           | Decrease $k$ (toward 0) |
| **Sigmoid**          | alpha                   | Increase $\alpha$      | Decrease $\alpha$       |
