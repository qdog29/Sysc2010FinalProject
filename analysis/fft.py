"""
fft.py
"""

import numpy as np


def compute_fft(signal, fs):

    signal = np.asarray(signal, dtype=float)
    if signal.size == 0:
        raise ValueError("Cannot compute FFT on an empty signal.")

    # Subtract mean to remove DC offset
    y = signal - np.mean(signal)
    n = y.size

    # rfft gives single-sided spectrum (positive frequencies only)
    freqs = np.fft.rfftfreq(n, d=1.0 / fs)
    magnitudes = np.abs(np.fft.rfft(y)) / n
    magnitudes[1:-1] *= 2
    return freqs, magnitudes


def dominant_frequency(freqs, magnitudes):

    if len(freqs) < 2:
        return 0.0
    idx = np.argmax(magnitudes[1:]) + 1
    return float(freqs[idx])
