"""Rewarming curve algorithms for organ temperature control.

Each curve is parameterized by:
- t: time (minutes)
- t_total: total rewarming time (minutes)
- t_start: start temperature (°C)
- t_end: end temperature (°C)

All APIs return both instantaneous temperature and instantaneous rewarming
rate dT/dt in °C/min.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable

try:
    import matplotlib.pyplot as plt
except ModuleNotFoundError:  # optional dependency for plotting only
    plt = None


@dataclass(frozen=True)
class RewarmingParams:
    t_start: float
    t_end: float
    t_total: float
    max_gradient: float = 1.0  # °C/min safety limit

    @property
    def delta_t(self) -> float:
        return self.t_end - self.t_start


CurveFn = Callable[..., tuple[float, float]]


def _clip_time(t: float, t_total: float) -> float:
    return max(0.0, min(t, t_total))


def _u(t: float, t_total: float) -> float:
    if t_total <= 0:
        raise ValueError("t_total must be > 0")
    return _clip_time(t, t_total) / t_total


# 1) Uncontrolled sine: fast initial warming, then tapering.
def curve_sine_uncontrolled(t: float, p: RewarmingParams) -> tuple[float, float]:
    u = _u(t, p.t_total)
    theta = 0.5 * math.pi * u
    temp = p.t_start + p.delta_t * math.sin(theta)
    rate = p.delta_t / p.t_total * 0.5 * math.pi * math.cos(theta)
    return temp, rate


# 2) Linear ramp: constant warming rate.
def curve_linear(t: float, p: RewarmingParams) -> tuple[float, float]:
    u = _u(t, p.t_total)
    temp = p.t_start + p.delta_t * u
    rate = p.delta_t / p.t_total
    return temp, rate


# 3) Controlled stretched-sine (time-warped sine).
def curve_sine_stretched_controlled(
    t: float,
    p: RewarmingParams,
    beta: float = 1.5,
) -> tuple[float, float]:
    if beta <= 0:
        raise ValueError("beta must be > 0")

    u = _u(t, p.t_total)
    w = u**beta
    theta = 0.5 * math.pi * w

    temp = p.t_start + p.delta_t * math.sin(theta)

    # dT/dt = dT/du * du/dt with w = u^beta
    if u == 0 and beta < 1:
        rate = float("inf")
    else:
        rate = (
            p.delta_t
            / p.t_total
            * 0.5
            * math.pi
            * beta
            * (u ** (beta - 1))
            * math.cos(theta)
        )
    return temp, rate


# 4) Normal exponential rise (convex): mostly below linear for b > 1.
# Normalized to satisfy f(0)=0 and f(1)=1.
def curve_exponential(
    t: float,
    p: RewarmingParams,
    b: float = 1.5,
) -> tuple[float, float]:
    if b <= 1.0:
        raise ValueError("b must be > 1")

    u = _u(t, p.t_total)
    denom = b - 1.0
    temp = p.t_start + p.delta_t * (b**u - 1.0) / denom
    rate = p.delta_t / p.t_total * (math.log(b) * b**u / denom)
    return temp, rate


def curve_equation_strings(beta: float = 2.0, b: float = 1.5) -> dict[str, str]:
    """Return display equations for each curve with current parameter values."""
    return {
        "sine_uncontrolled": "T(t)=T0+ΔT*sin((π/2)*(t/τ))",
        "linear": "T(t)=T0+ΔT*(t/τ)",
        "sine_stretched_controlled": (
            f"T(t)=T0+ΔT*sin((π/2)*(t/τ)^{beta:g})"
        ),
        "exponential": f"T(t)=T0+ΔT*((({b:g})^(t/τ)-1)/({b:g}-1))",
    }


def numeric_curve_equation_strings(
    p: RewarmingParams,
    beta: float = 2.0,
    b: float = 1.5,
) -> dict[str, str]:
    """Return equations with numeric coefficients for the current parameters."""
    delta = p.delta_t
    tau = p.t_total
    linear_coeff = delta / tau
    sine_coeff = delta
    exp_coeff = delta / (b - 1.0)

    return {
        "Sine (uncontrolled)": (
            f"T(t)={p.t_start:.3f}+{sine_coeff:.3f}*sin({(math.pi/(2.0*tau)):.6f}*t)"
        ),
        "Linear": f"T(t)={p.t_start:.3f}+{linear_coeff:.3f}*t",
        "Stretched sine (controlled)": (
            f"T(t)={p.t_start:.3f}+{sine_coeff:.3f}*sin({math.pi/2.0:.6f}*(t/{tau:.3f})^{beta:g})"
        ),
        "Exponential": (
            f"T(t)={p.t_start:.3f}+{exp_coeff:.3f}*({b:g}^(t/{tau:.3f})-1)"
        ),
    }


def max_rate_over_interval(
    curve: CurveFn,
    p: RewarmingParams,
    n: int = 5000,
    **kwargs,
) -> float:
    max_rate = 0.0
    for i in range(n + 1):
        t = p.t_total * i / n
        _, rate = curve(t, p, **kwargs) if kwargs else curve(t, p)
        max_rate = max(max_rate, abs(rate))
    return max_rate


def minimum_duration_for_gradient(
    curve: CurveFn,
    p: RewarmingParams,
    **kwargs,
) -> float:
    """Compute minimum total time that keeps |dT/dt| <= max_gradient."""
    current_peak = max_rate_over_interval(curve, p, **kwargs)
    if current_peak <= p.max_gradient:
        return p.t_total
    scale = current_peak / p.max_gradient
    return p.t_total * scale


def _safety_adjusted_params(curve: CurveFn, p: RewarmingParams, **kwargs) -> RewarmingParams:
    adjusted_t_total = minimum_duration_for_gradient(curve, p, **kwargs)
    return RewarmingParams(
        t_start=p.t_start,
        t_end=p.t_end,
        t_total=adjusted_t_total,
        max_gradient=p.max_gradient,
    )


def demo() -> None:
    params = RewarmingParams(t_start=4.0, t_end=27.0, t_total=30.0, max_gradient=1.0)
    beta = 1.5
    b = 1.5

    curves = [
        ("sine_uncontrolled", curve_sine_uncontrolled, {}),
        ("linear", curve_linear, {}),
        ("sine_stretched_controlled", curve_sine_stretched_controlled, {"beta": beta}),
        ("exponential", curve_exponential, {"b": b}),
    ]

    print(f"Parameters: {params}")
    print("Current curve functions:")
    for name, equation in curve_equation_strings(beta=beta, b=b).items():
        print(f"  - {name}: {equation}")

    print("Current numeric functions:")
    for name, equation in numeric_curve_equation_strings(params, beta=beta, b=b).items():
        print(f"  - {name}: {equation}")

    for name, fn, kwargs in curves:
        adjusted = _safety_adjusted_params(fn, params, **kwargs)
        peak = max_rate_over_interval(fn, adjusted, **kwargs)
        t_mid = adjusted.t_total / 2.0
        temp_mid, rate_mid = fn(t_mid, adjusted, **kwargs) if kwargs else fn(t_mid, adjusted)
        print(
            f"{name:34s} | peak_rate={peak:0.3f} °C/min | "
            f"midpoint=({temp_mid:0.3f} °C, {rate_mid:0.3f} °C/min) | "
            f"safety_t_total={adjusted.t_total:0.2f} min"
        )

def plot_curves(
    p: RewarmingParams,
    output_path: str = "rewarming_curves.png",
    n_points: int = 301,
    beta: float = 1.5,
    b: float = 1.5,
    enforce_max_gradient: bool = True,
) -> str:
    """Plot the four rewarming curves and save as an image.

    If enforce_max_gradient=True, each curve uses a safety-adjusted duration so
    its peak rate is <= p.max_gradient.
    """
    if plt is None:
        raise RuntimeError(
            "matplotlib is not installed. Install it with `pip install matplotlib` "
            "to generate curve plots."
        )

    curve_specs: list[tuple[str, CurveFn, dict]] = [
        ("Sine (uncontrolled)", curve_sine_uncontrolled, {}),
        ("Linear", curve_linear, {}),
        (f"Stretched sine (controlled, beta={beta:g})", curve_sine_stretched_controlled, {"beta": beta}),
        (f"Exponential (b={b:g})", curve_exponential, {"b": b}),
    ]

    fig, ax = plt.subplots(figsize=(9, 5.5))
    for label, fn, kwargs in curve_specs:
        p_use = _safety_adjusted_params(fn, p, **kwargs) if enforce_max_gradient else p
        times = [p_use.t_total * i / (n_points - 1) for i in range(n_points)]
        values = [fn(t, p_use, **kwargs)[0] if kwargs else fn(t, p_use)[0] for t in times]
        peak = max_rate_over_interval(fn, p_use, **kwargs)
        ax.plot(times, values, linewidth=2, label=f"{label} (peak={peak:.2f})")

    title = "Organ Rewarming Curves"
    if enforce_max_gradient:
        title += f" (safety-adjusted to ≤{p.max_gradient:g} °C/min)"
    ax.set_title(title)
    ax.set_xlabel("Time (min)")
    ax.set_ylabel("Temperature (°C)")
    ax.grid(True, alpha=0.3)
    ax.legend()
    ax.set_ylim(min(p.t_start, p.t_end) - 0.5, max(p.t_start, p.t_end) + 0.5)
    fig.tight_layout()
    fig.savefig(output_path, dpi=150)
    plt.close(fig)
    return output_path


if __name__ == "__main__":
    demo()
    default_params = RewarmingParams(t_start=4.0, t_end=27.0, t_total=30.0, max_gradient=1.0)
    try:
        image = plot_curves(default_params)
        print(f"Saved plot: {image}")
    except RuntimeError as exc:
        print(f"Plot skipped: {exc}")

