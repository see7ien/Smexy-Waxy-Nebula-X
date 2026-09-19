"""SHM cumulative-fatigue-damage estimation.

Physics: rainflow-count the raw stress time series into (range, count) pairs,
then fatigue = sum(count * range ** EXPONENT) -- a standard fatigue-damage
proxy. `LEARNED_C` converts that proxy into the actual damage units; it was
learned once, offline, as the average of actual_damage / fatigue across the
labeled training files (see final_predict.py, which does that derivation --
its raw SHM training data isn't bundled in this repo, so the already-learned
ratio is fixed here as a constant rather than re-derived at runtime).
"""

from __future__ import annotations

import pandas as pd
import rainflow

EXPONENT = 5.03
LEARNED_C = 3.836942106125183e-11


def calculate_fatigue(file) -> float:
    signal = pd.read_csv(file, header=None).iloc[:, 0].to_numpy()
    cycles = rainflow.count_cycles(signal)
    return sum(count * stress_range**EXPONENT for stress_range, count in cycles)


def predict_damage(file) -> float:
    return LEARNED_C * calculate_fatigue(file)
