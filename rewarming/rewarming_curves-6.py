"""Rewarming curve algorithms and comparison plot generation.

Updated model set (6 curves):
1) Hyperbolic / negative exponential (time-sensitive)
2) Natural positive exponential (time-sensitive)
3) Linear (time-sensitive)
4) Sigmoid (time-sensitive)
5) Kidney linear at 1.0 °C/min (not time-sensitive)
6) Horse sperm linear at 0.3 °C/min (not time-sensitive)
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable

try:
    import matplotlib.pyplot as plt
except ModuleNotFoundError:  # optional
    plt = None


@dataclass(frozen=True)
class CurveParams:
    temp_start: float = 4.0
    temp_end: float = 27.0
    time_total: float = 30.0

    @property
    def delta_t(self) -> float:
        return self.temp_end - self.temp_start


CurveFn = Callable[[float, CurveParams], tuple[float, float]]


def _clip(x: float, lo: float, hi: float) -> float:
    return max(lo, min(x, hi))


def _u(t: float, total: float) -> float:
    if total <= 0:
        raise ValueError("total time must be > 0")
    return _clip(t / total, 0.0, 1.0)


# 1) Hyperbolic / negative exponential (concave, fast early warming)
def curve_hyperbolic_negative_exponential(
    t: float,
    p: CurveParams,
    k_neg: float = 5.0,
) -> tuple[float, float]:
    if k_neg <= 0:
        raise ValueError("k_neg must be > 0")
    u = _u(t, p.time_total)
    denom = 1.0 - math.exp(-k_neg)
    y = (1.0 - math.exp(-k_neg * u)) / denom
    temp = p.temp_start + p.delta_t * y
    rate = p.delta_t / p.time_total * (k_neg * math.exp(-k_neg * u) / denom)
    return temp, rate


# 2) Natural positive exponential (convex, slow early warming)
def curve_natural_positive_exponential(
    t: float,
    p: CurveParams,
    k_pos: float = 5.0,
) -> tuple[float, float]:
    if k_pos <= 0:
        raise ValueError("k_pos must be > 0")
    u = _u(t, p.time_total)
    denom = math.exp(k_pos) - 1.0
    y = (math.exp(k_pos * u) - 1.0) / denom
    temp = p.temp_start + p.delta_t * y
    rate = p.delta_t / p.time_total * (k_pos * math.exp(k_pos * u) / denom)
    return temp, rate


# 3) Linear within fixed 30 min from 4 to 27

def curve_linear_time_sensitive(t: float, p: CurveParams) -> tuple[float, float]:
    u = _u(t, p.time_total)
    temp = p.temp_start + p.delta_t * u
    rate = p.delta_t / p.time_total
    return temp, rate


# 4) Sigmoid (normalized logistic)
def curve_sigmoid(
    t: float,
    p: CurveParams,
    alpha: float = 12.0,
) -> tuple[float, float]:
    if alpha <= 0:
        raise ValueError("alpha must be > 0")
    u = _u(t, p.time_total)

    def s(x: float) -> float:
        return 1.0 / (1.0 + math.exp(-alpha * (x - 0.5)))

    s0 = s(0.0)
    s1 = s(1.0)
    su = s(u)
    y = (su - s0) / (s1 - s0)
    temp = p.temp_start + p.delta_t * y

    ds_du = alpha * su * (1.0 - su)
    dy_du = ds_du / (s1 - s0)
    rate = p.delta_t / p.time_total * dy_du
    return temp, rate


# 5) Kidney linear with fixed maximum gradient 1.0 °C/min (not time-sensitive)
def curve_kidney_linear_max_1c_per_min(t: float, p: CurveParams) -> tuple[float, float]:
    rate = 1.0
    t_needed = p.delta_t / rate
    t_eff = _clip(t, 0.0, t_needed)
    temp = p.temp_start + rate * t_eff
    actual_rate = rate if t < t_needed else 0.0
    return temp, actual_rate


# 6) Horse sperm linear with fixed maximum gradient 0.3 °C/min (not time-sensitive)
def curve_horse_sperm_linear_max_03c_per_min(t: float, p: CurveParams) -> tuple[float, float]:
    rate = 0.3
    t_needed = p.delta_t / rate
    t_eff = _clip(t, 0.0, t_needed)
    temp = p.temp_start + rate * t_eff
    actual_rate = rate if t < t_needed else 0.0
    return temp, actual_rate


def equation_strings_numeric(p: CurveParams, k_neg: float = 5.0, k_pos: float = 5.0, alpha: float = 12.0) -> dict[str, str]:
    linear_rate = p.delta_t / p.time_total
    return {
        "1) Hyperbolic / negative exponential": (
            f"T(t)={p.temp_start:.3f}+{p.delta_t:.3f}*(1-exp(-{k_neg:.3f}*t/{p.time_total:.3f}))/(1-exp(-{k_neg:.3f}))"
        ),
        "2) Natural positive exponential": (
            f"T(t)={p.temp_start:.3f}+{p.delta_t:.3f}*(exp({k_pos:.3f}*t/{p.time_total:.3f})-1)/(exp({k_pos:.3f})-1)"
        ),
        "3) Linear (time-sensitive)": f"T(t)={p.temp_start:.3f}+{linear_rate:.3f}*t  (0<=t<={p.time_total:.1f})",
        "4) Sigmoid": (
            f"T(t)={p.temp_start:.3f}+{p.delta_t:.3f}*norm_sigmoid(t/{p.time_total:.3f}, alpha={alpha:.3f})"
        ),
        "5) Kidney linear (1.0 °C/min)": f"T(t)={p.temp_start:.3f}+1.000*t  (clamped at {p.temp_end:.3f})",
        "6) Horse sperm linear (0.3 °C/min)": f"T(t)={p.temp_start:.3f}+0.300*t  (clamped at {p.temp_end:.3f})",
    }


def sample_curve(curve: CurveFn, p: CurveParams, t_end: float, n: int = 400) -> tuple[list[float], list[float]]:
    times = [t_end * i / (n - 1) for i in range(n)]
    values = [curve(t, p)[0] for t in times]
    return times, values


def max_rate(curve: CurveFn, p: CurveParams, t_end: float, n: int = 4000) -> float:
    mr = 0.0
    for i in range(n):
        t = t_end * i / (n - 1)
        _, r = curve(t, p)
        mr = max(mr, abs(r))
    return mr


def plot_curves(output_path: str = "rewarming_curves.png") -> str:
    p = CurveParams(temp_start=4.0, temp_end=27.0, time_total=30.0)
    k_neg = 5.0
    k_pos = 5.0
    alpha = 12.0

    plot_time_cutoff = 30.0
    curves: list[tuple[str, CurveFn, float, str]] = [
        ("1) Hyperbolic / negative exponential", lambda t, pp: curve_hyperbolic_negative_exponential(t, pp, k_neg=k_neg), 30.0, "#d62728"),
        ("2) Natural positive exponential", lambda t, pp: curve_natural_positive_exponential(t, pp, k_pos=k_pos), 30.0, "#1f77b4"),
        ("3) Linear (time-sensitive)", curve_linear_time_sensitive, 30.0, "#2ca02c"),
        ("4) Sigmoid", lambda t, pp: curve_sigmoid(t, pp, alpha=alpha), 30.0, "#9467bd"),
        ("5) Kidney linear (1.0 °C/min)", curve_kidney_linear_max_1c_per_min, p.delta_t / 1.0, "#ff7f0e"),
        ("6) Horse sperm linear (0.3 °C/min)", curve_horse_sperm_linear_max_03c_per_min, p.delta_t / 0.3, "#8c564b"),
    ]

    equations = equation_strings_numeric(p, k_neg=k_neg, k_pos=k_pos, alpha=alpha)

    if plt is None:
        return plot_curves_svg_fallback(curves, equations, p, output_path.replace('.png', '.svg'))

    fig, ax = plt.subplots(figsize=(13, 7))
    for label, fn, t_end, color in curves:
        t, y = sample_curve(fn, p, t_end=t_end, n=500)
        peak = max_rate(fn, p, t_end=t_end)
        ax.plot(t, y, color=color, linewidth=2.2, label=f"{label} | peak={peak:.3f} °C/min")


    ax.set_title("Rewarming Curves Comparison")
    ax.set_xlabel("Time (min)")
    ax.set_ylabel("Temperature (°C)")
    ax.grid(True, alpha=0.3)
    ax.set_ylim(3.5, 27.5)
    ax.set_xlim(0, plot_time_cutoff)
    ax.legend(loc="upper left", fontsize=8)
    fig.tight_layout()
    fig.savefig(output_path, dpi=160)
    plt.close(fig)
    return output_path


def plot_curves_svg_fallback(
    curves: list[tuple[str, CurveFn, str]],
    p: CurveParams,
    output_path: str,
    plot_time_cutoff: float = 30.0,
) -> str:
    """Simple no-dependency SVG plot fallback."""
    width, height = 980, 760
    left, right, top, bottom = 80, 80, 40, 70
    plot_w = width - left - right
    plot_h = height - top - bottom

    x_max = plot_time_cutoff
    y_min, y_max = 3.5, 27.5

    def x_px(x: float) -> float:
        return left + (x / x_max) * plot_w

    def y_px(y: float) -> float:
        return top + (1.0 - (y - y_min) / (y_max - y_min)) * plot_h

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">',
        '<rect width="100%" height="100%" fill="white"/>',
        f'<text x="{left}" y="24" font-size="20" font-family="Arial">6 Rewarming Curves Comparison</text>',
        f'<line x1="{left}" y1="{top+plot_h}" x2="{left+plot_w}" y2="{top+plot_h}" stroke="black"/>',
        f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top+plot_h}" stroke="black"/>',
    ]

    # grid
    for i in range(0, 9):
        xv = x_max * i / 8
        xp = x_px(xv)
        parts.append(f'<line x1="{xp:.1f}" y1="{top}" x2="{xp:.1f}" y2="{top+plot_h}" stroke="#eee"/>')
        parts.append(f'<text x="{xp:.1f}" y="{top+plot_h+18}" font-size="11" text-anchor="middle">{xv:.1f}</text>')
    for i in range(0, 7):
        yv = y_min + (y_max - y_min) * i / 6
        yp = y_px(yv)
        parts.append(f'<line x1="{left}" y1="{yp:.1f}" x2="{left+plot_w}" y2="{yp:.1f}" stroke="#eee"/>')
        parts.append(f'<text x="{left-8}" y="{yp+4:.1f}" font-size="11" text-anchor="end">{yv:.1f}</text>')

    # curves
    legend_y = top + 20
    for label, fn, color in curves:
        t, y = sample_curve(fn, p, t_end=plot_time_cutoff, n=500)
        pts = " ".join([f"{x_px(tx):.2f},{y_px(ty):.2f}" for tx, ty in zip(t, y)])
        parts.append(f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="2.2"/>')

        peak = max_rate(fn, p, t_end=plot_time_cutoff)
        # legend in plot area (top-left)
        x0 = left + 12
        y0 = legend_y
        parts.append(f'<line x1="{x0}" y1="{y0}" x2="{x0+20}" y2="{y0}" stroke="{color}" stroke-width="3"/>')
        parts.append(
            f'<text x="{x0+26}" y="{y0+4}" font-size="11" font-family="Arial">{label} | peak={peak:.3f} °C/min</text>'
        )
        legend_y += 18

    parts.append(f'<text x="{left+plot_w/2:.1f}" y="{height-12}" font-size="12" text-anchor="middle">Time (min)</text>')
    parts.append(f'<text x="18" y="{top+plot_h/2:.1f}" font-size="12" transform="rotate(-90,18,{top+plot_h/2:.1f})" text-anchor="middle">Temperature (°C)</text>')
    parts.append('</svg>')

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(parts))
    return output_path


def demo() -> None:
    p = CurveParams(temp_start=4.0, temp_end=27.0, time_total=30.0)
    k_neg = 5.0
    k_pos = 5.0
    alpha = 12.0

    print(f"Assumptions (first 4 curves): start={p.temp_start}, end={p.temp_end}, total={p.time_total} min")
    print("Numeric equations:")
    for name, eq in equation_strings_numeric(p, k_neg=k_neg, k_pos=k_pos, alpha=alpha).items():
        print(f"  - {name}: {eq}")

    curve_items: list[tuple[str, CurveFn, float]] = [
        ("1) Hyperbolic / negative exponential", lambda t, pp: curve_hyperbolic_negative_exponential(t, pp, k_neg=k_neg), 30.0),
        ("2) Natural positive exponential", lambda t, pp: curve_natural_positive_exponential(t, pp, k_pos=k_pos), 30.0),
        ("3) Linear (time-sensitive)", curve_linear_time_sensitive, 30.0),
        ("4) Sigmoid", lambda t, pp: curve_sigmoid(t, pp, alpha=alpha), 30.0),
        ("5) Kidney linear (1.0 °C/min)", curve_kidney_linear_max_1c_per_min, p.delta_t / 1.0),
        ("6) Horse sperm linear (0.3 °C/min)", curve_horse_sperm_linear_max_03c_per_min, p.delta_t / 0.3),
    ]

    for name, fn, t_end in curve_items:
        mid_t = t_end / 2.0
        mid_temp, mid_rate = fn(mid_t, p)
        peak = max_rate(fn, p, t_end=t_end)
        print(
            f"{name:42s} | duration={t_end:6.2f} min | peak_rate={peak:0.3f} °C/min | "
            f"midpoint=({mid_temp:0.3f} °C, {mid_rate:0.3f} °C/min)"
        )


if __name__ == "__main__":
    demo()
    image = plot_curves("rewarming_curves.png")
    print(f"Saved plot: {image}")

