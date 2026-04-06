"""
features.py
"""

import numpy as np
from scipy.signal import find_peaks


def extract_ecg_features(signal, fs) -> dict:
    signal = np.asarray(signal, dtype=float)
    min_distance = int(fs * 0.3)
    height_threshold = 0.4 * np.max(signal)
    peaks, _ = find_peaks(signal, distance=min_distance, height=height_threshold)

    r_peak_count = int(len(peaks))
    features: dict[str, float | int] = {"r_peak_count": r_peak_count}

    if r_peak_count >= 2:
        intervals = np.diff(peaks) / fs
        mean_interval = np.mean(intervals)
        bpm = 60.0 / mean_interval if mean_interval > 0 else 0.0
        features["heart_rate_bpm"] = round(bpm, 1)
        features["mean_rr_interval_s"] = round(float(mean_interval), 4)
        features["std_rr_interval_s"] = round(float(np.std(intervals)), 4)
    else:
        features["heart_rate_bpm"] = 0.0
        features["mean_rr_interval_s"] = 0.0
        features["std_rr_interval_s"] = 0.0

    features["peak_to_peak_amplitude"] = round(float(np.max(signal) - np.min(signal)), 4)
    return features


def extract_temperature_features(signal, time) -> dict:

    signal = np.asarray(signal, dtype=float)
    time = np.asarray(time, dtype=float)
    coeffs = np.polyfit(time, signal, 1)
    return {
        "trend_slope": round(float(coeffs[0]), 6),
        "average": round(float(np.mean(signal)), 4),
        "variance": round(float(np.var(signal)), 6),
    }


def extract_respiration_features(signal, fs) -> dict:

    signal = np.asarray(signal, dtype=float)
    features = {"rms_amplitude": round(float(np.sqrt(np.mean(signal ** 2))), 4)}

    # Breathing rate from dominant FFT peak in 0.1–1.0 Hz
    n = signal.size
    freqs = np.fft.rfftfreq(n, d=1.0 / fs)
    magnitudes = np.abs(np.fft.rfft(signal - np.mean(signal))) / n

    mask = (freqs >= 0.1) & (freqs <= 1.0)
    if np.any(mask):
        band_freqs = freqs[mask]
        band_mags = magnitudes[mask]
        dom_freq = band_freqs[np.argmax(band_mags)]
        features["breathing_rate_bpm"] = round(float(dom_freq * 60.0), 1)
        features["mean_breath_interval_s"] = round(1.0 / float(dom_freq), 4)
    else:
        features["breathing_rate_bpm"] = 0.0
        features["mean_breath_interval_s"] = 0.0

    return features


def extract_motion_features(signal, fs) -> dict:

    signal = np.asarray(signal, dtype=float)
    return {
        "activity_intensity_rms": round(float(np.sqrt(np.mean(signal ** 2))), 4),
        "peak_acceleration": round(float(np.max(np.abs(signal))), 4),
        "mean_acceleration_ms2": round(float(np.nanmean(signal)), 4),
    }


def extract_features(signal, fs, signal_type, time=None):

    extractors = {
        "ECG": lambda s, f: extract_ecg_features(s, f),
        "Temperature": lambda s, f: extract_temperature_features(
            s, time if time is not None else np.arange(len(s)) / f
        ),
        "Respiration": lambda s, f: extract_respiration_features(s, f),
        "IMU / Motion": lambda s, f: extract_motion_features(s, f),
    }
    func = extractors.get(signal_type)
    if func is None:
        return {"note": "No specific features for this signal type."}
    return func(signal, fs)
