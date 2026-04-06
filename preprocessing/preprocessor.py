"""
preprocessor.py
"""

import numpy as np


def interpolate_nans(y: np.ndarray) -> np.ndarray:

    y = np.asarray(y, dtype=float).copy()
    idx = np.arange(y.size)
    good = np.isfinite(y)

    if not np.any(good):
        return np.zeros_like(y)
    if np.all(good):
        return y

    y[~good] = np.interp(idx[~good], idx[good], y[good])
    return y


def normalize(y: np.ndarray) -> np.ndarray:
    
    y = np.asarray(y, dtype=float)
    if len(y) == 0:
        raise ValueError("Signal cannot be empty")
    max_val = np.max(np.abs(y))
    if max_val == 0:
        return y.copy()
    return y / max_val


def remove_baseline(signal: np.ndarray, fs: float, cutoff: float) -> np.ndarray:

    from scipy.signal import butter, filtfilt
    nyq = 0.5 * fs
    if cutoff >= nyq:
        raise ValueError(f"Cutoff ({cutoff}) must be < Nyquist ({nyq}).")
    b, a = butter(2, cutoff / nyq, btype="high")
    return filtfilt(b, a, signal)


def estimate_fs(t: np.ndarray) -> float:
   
    dt = np.diff(np.asarray(t, dtype=float))
    dt = dt[np.isfinite(dt) & (dt > 0)]
    if dt.size == 0:
        raise ValueError("Time column must contain increasing, numeric values.")
    return 1.0 / float(np.median(dt))
