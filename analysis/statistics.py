"""
statistics.py
"""

import numpy as np


def compute_mean(signal) -> float:
    y = np.asarray(signal, dtype=float)
    return float(np.nanmean(y))


def compute_std(signal) -> float:
    y = np.asarray(signal, dtype=float)
    return float(np.nanstd(y))


def compute_rms(signal) -> float:
    y = np.asarray(signal, dtype=float)
    return float(np.sqrt(np.nanmean(y ** 2)))


def compute_peak_to_peak(signal) -> float:
    y = np.asarray(signal, dtype=float)
    return float(np.nanmax(y) - np.nanmin(y))


def compute_stats(signal):
    y = np.asarray(signal, dtype=float)
    if y.size == 0:
        raise ValueError("Cannot compute statistics on an empty signal.")
    finite = y[np.isfinite(y)]
    if finite.size == 0:
        raise ValueError("Signal contains no finite values (all NaN or Inf).")
    return {
        "mean": compute_mean(y),
        "median": float(np.nanmedian(y)),
        "std": compute_std(y),
        "rms": compute_rms(y),
        "peak_to_peak": compute_peak_to_peak(y),
        "min": float(np.nanmin(y)),
        "max": float(np.nanmax(y)),
    }
