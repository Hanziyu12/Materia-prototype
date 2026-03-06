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


@dataclass(frozen=True)
class RewarmingParams:
    t_start: float
    t_end: float
    t_total: float
    max_gradient: float = 1.0  # °C/min safety limit

    @property
    def delta_t(self) -> float:
        return self.t_end - self.t_start


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


# 3) Controlled stretched-sine (ease-in/ease-out via time stretch).
# beta > 1 stretches time early to reduce initial slope.
def curve_sine_stretched_controlled(
    t: float,
    p: RewarmingParams,
    beta: float = 2.0,
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


# 4) Exponential approach to final temperature.
def curve_exponential(
    t: float,
    p: RewarmingParams,
    k: float = 3.0,
) -> tuple[float, float]:
    if k <= 0:
        raise ValueError("k must be > 0")

    u = _u(t, p.t_total)
    denom = 1.0 - math.exp(-k)
    temp = p.t_start + p.delta_t * (1.0 - math.exp(-k * u)) / denom
    rate = p.delta_t / p.t_total * (k * math.exp(-k * u)) / denom
    return temp, rate


def max_rate_over_interval(
    curve: Callable[..., tuple[float, float]],
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
    curve: Callable[..., tuple[float, float]],
    p: RewarmingParams,
    **kwargs,
) -> float:
    """Compute minimum total time that keeps |dT/dt| <= max_gradient.

    This scales the current t_total by the ratio of peak/current allowed gradient.
    """
    current_peak = max_rate_over_interval(curve, p, **kwargs)
    if current_peak <= p.max_gradient:
        return p.t_total
    scale = current_peak / p.max_gradient
    return p.t_total * scale


def demo() -> None:
    params = RewarmingParams(t_start=4.0, t_end=27.0, t_total=30.0, max_gradient=1.0)

    curves = [
        ("sine_uncontrolled", curve_sine_uncontrolled, {}),
        ("linear", curve_linear, {}),
        ("sine_stretched_controlled(beta=2)", curve_sine_stretched_controlled, {"beta": 2.0}),
        ("exponential(k=3)", curve_exponential, {"k": 3.0}),
    ]

    print(f"Parameters: {params}")
    for name, fn, kwargs in curves:
        peak = max_rate_over_interval(fn, params, **kwargs)
        min_total = minimum_duration_for_gradient(fn, params, **kwargs)
        t_mid = params.t_total / 2.0
        temp_mid, rate_mid = fn(t_mid, params, **kwargs) if kwargs else fn(t_mid, params)
        print(
            f"{name:34s} | peak_rate={peak:0.3f} °C/min | "
            f"midpoint=({temp_mid:0.3f} °C, {rate_mid:0.3f} °C/min) | "
            f"min_time_for_1C_per_min={min_total:0.2f} min"
        )


if __name__ == "__main__":
    demo()
