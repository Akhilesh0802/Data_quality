"""
calculator.py
-------------
Pure business logic (no Tkinter). Works for any estimator defined in config.py.
"""

import csv
from decimal import ROUND_HALF_UP, Decimal
from dataclasses import dataclass
from typing import Dict, List, Optional

from config import ESTIMATORS, HOURS_PER_DAY


class EstimationError(ValueError):
    """Raised when an invalid selection is passed to the calculator."""


@dataclass(frozen=True)
class ScopeChoice:
    key: str
    label: str
    band: str
    multiplier: int
    direct: bool = False


@dataclass(frozen=True)
class LineItem:
    key: str
    particular: str
    level: str
    base_hours: float
    multiplier: int

    @property
    def final_hours(self) -> float:
        return self.base_hours * self.multiplier


@dataclass(frozen=True)
class EstimateResult:
    key: str
    title: str
    mode: Optional[str]
    scopes: List[ScopeChoice]
    items: List[LineItem]
    hours_per_day: int = HOURS_PER_DAY

    @property
    def total_hours(self) -> float:
        return sum(item.final_hours for item in self.items)

    @property
    def total_days(self) -> float:
        return self.total_hours / self.hours_per_day


def fmt(value: float) -> str:
    """1.0 -> '1', 0.625 -> '0.63' (normal half-up rounding)"""
    rounded = Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return f"{float(rounded):g}"


def get_estimator(est_key: str) -> dict:
    try:
        return ESTIMATORS[est_key]
    except KeyError as exc:
        raise EstimationError(f"Unknown estimator: {est_key!r}") from exc


def get_levels(est_key: str, item_key: str) -> List[str]:
    return list(get_estimator(est_key)["matrix"][item_key].get("levels", {}))


def is_direct(est_key: str, item_key: str) -> bool:
    """True when the item's hours come straight from a dropdown (no levels)."""
    return "hours_by_band" in get_estimator(est_key)["matrix"][item_key]


def get_bands(est_key: str, scope_key: str) -> List[str]:
    return list(get_estimator(est_key)["scopes"][scope_key]["bands"])


def calculate(est_key: str, bands: Dict[str, str], levels: Dict[str, str]) -> EstimateResult:
    cfg = get_estimator(est_key)

    scopes, multipliers = [], {}
    for s_key, s_cfg in cfg["scopes"].items():
        band = bands.get(s_key)
        if band not in s_cfg["bands"]:
            raise EstimationError(f"Please select a valid option for '{s_cfg['label']}'")
        multipliers[s_key] = s_cfg["bands"][band]
        scopes.append(ScopeChoice(s_key, s_cfg["label"], band, multipliers[s_key],
                                  s_cfg.get("direct", False)))

    items = []
    for i_key, i_cfg in cfg["matrix"].items():
        if "hours_by_band" in i_cfg:                       # direct lookup
            s_cfg = cfg["scopes"][i_cfg["scope"]]
            band = bands[i_cfg["scope"]]
            unit = s_cfg.get("unit_singular", s_cfg["unit"]) if band == "1" else s_cfg["unit"]
            items.append(LineItem(i_key, i_cfg["label"], f"{band} {unit}",
                                  i_cfg["hours_by_band"][band], 1))
            continue
        level = levels.get(i_key)
        if level not in i_cfg["levels"]:
            raise EstimationError(f"Please select a valid option for '{i_cfg['label']}'")
        items.append(LineItem(i_key, i_cfg["label"], level,
                              i_cfg["levels"][level], multipliers[i_cfg["scope"]]))

    return EstimateResult(est_key, cfg["title"], cfg.get("mode"), scopes, items)


def to_summary_text(result: EstimateResult) -> str:
    lines = [result.title, "=" * len(result.title)]
    if result.mode:
        lines.append(f"Mode of Delivery : {result.mode}")
    for s in result.scopes:
        lines.append(f"{s.label:<32}: {s.band}" + ("" if s.direct else f" (x{s.multiplier})"))
    lines.append("")
    for item in result.items:
        lines.append(f"{item.particular:<46} {item.level:<13} "
                     f"{fmt(item.base_hours):>3} x {item.multiplier} = {fmt(item.final_hours)} hrs")
    lines += ["",
              f"Total Time (in hours): {fmt(result.total_hours)}",
              f"Total Time (in days) : {fmt(result.total_days)}  (@ {result.hours_per_day} hrs/day)"]
    return "\n".join(lines)


def export_csv(result: EstimateResult, path: str) -> None:
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow([result.title])
        w.writerow([])
        w.writerow(["Particulars", "Select", "Multiplier Factor"])
        if result.mode:
            w.writerow(["Mode of Delivery", result.mode, ""])
        for s in result.scopes:
            w.writerow([s.label, s.band, "" if s.direct else s.multiplier])
        w.writerow([])
        w.writerow(["Particulars", "Select", "Base Effort (hrs)", "Multiplier", "Final Effort (hrs)"])
        for item in result.items:
            w.writerow([item.particular, item.level, fmt(item.base_hours),
                        item.multiplier, fmt(item.final_hours)])
        w.writerow([])
        w.writerow(["Total Time (in hours)", "", "", "", fmt(result.total_hours)])
        w.writerow(["Total Time (in days)", "", "", "", fmt(result.total_days)])
