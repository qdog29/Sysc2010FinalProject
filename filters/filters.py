
import numpy as np
from scipy.signal import butter, filtfilt, firwin


# IIR filters (Butterworth + zero-phase filtfilt)

def apply_lowpass_iir(signal: np.ndarray, cutoff: float, fs: float,
                      order: int = 4) -> np.ndarray:
   
    nyq = 0.5 * fs
    b, a = butter(order, cutoff / nyq, btype="low")
    return filtfilt(b, a, signal)


def apply_highpass_iir(signal: np.ndarray, cutoff: float, fs: float,
                       order: int = 4) -> np.ndarray:
   
    nyq = 0.5 * fs
    b, a = butter(order, cutoff / nyq, btype="high")
    return filtfilt(b, a, signal)


def apply_bandpass_iir(signal: np.ndarray, low_cutoff: float,
                       high_cutoff: float, fs: float,
                       order: int = 4) -> np.ndarray:
    
    nyq = 0.5 * fs
    b, a = butter(order, [low_cutoff / nyq, high_cutoff / nyq], btype="band")
    return filtfilt(b, a, signal)

# FIR filters (firwin + lfilter)

def apply_lowpass_fir(signal: np.ndarray, cutoff: float, fs: float,
                      numtaps: int = 101) -> np.ndarray:
    
    coeffs = firwin(numtaps, cutoff, fs=fs, pass_zero=True)
    return filtfilt(coeffs, 1.0, signal)


def apply_highpass_fir(signal: np.ndarray, cutoff: float, fs: float,
                       numtaps: int = 101) -> np.ndarray:
 
    coeffs = firwin(numtaps, cutoff, fs=fs, pass_zero=False)
    return filtfilt(coeffs, 1.0, signal)


def apply_bandpass_fir(signal: np.ndarray, low_cutoff: float,
                       high_cutoff: float, fs: float,
                       numtaps: int = 101) -> np.ndarray:
   
    coeffs = firwin(numtaps, [low_cutoff, high_cutoff], fs=fs, pass_zero=False)
    return filtfilt(coeffs, 1.0, signal)

# Unified dispatcher used by the GUI

def apply_filter(signal: np.ndarray, fs: float, ftype: str, method: str,
                 cutoff_low: float | None = None, cutoff_high: float | None = None,
                 order: int = 4) -> np.ndarray:
    method = method.upper()
    ftype = ftype.upper()
    nyq = 0.5 * fs

    if cutoff_low is not None and cutoff_low >= nyq:
        raise ValueError(f"Cutoff Low ({cutoff_low} Hz) must be less than Nyquist ({nyq} Hz).")
    if cutoff_high is not None and cutoff_high >= nyq:
        raise ValueError(f"Cutoff High ({cutoff_high} Hz) must be less than Nyquist ({nyq} Hz).")

    if method == "IIR":
        if ftype == "LPF":
            assert cutoff_high is not None
            return apply_lowpass_iir(signal, cutoff_high, fs, order=order)
        elif ftype == "HPF":
            assert cutoff_low is not None
            return apply_highpass_iir(signal, cutoff_low, fs, order=order)
        elif ftype == "BPF":
            assert cutoff_low is not None and cutoff_high is not None
            return apply_bandpass_iir(signal, cutoff_low, cutoff_high, fs, order=order)
    elif method == "FIR":
        numtaps = order * 25 + 1  # reasonable FIR length from filter order
        max_taps = len(signal) // 3 - 1
        if max_taps < 3:
            raise ValueError(f"Signal too short ({len(signal)} samples) for FIR filtering.")
        if max_taps % 2 == 0:
            max_taps -= 1  # firwin needs odd numtaps for highpass/bandpass
        numtaps = min(numtaps, max_taps)
        if ftype == "LPF":
            assert cutoff_high is not None
            return apply_lowpass_fir(signal, cutoff_high, fs, numtaps=numtaps)
        elif ftype == "HPF":
            assert cutoff_low is not None
            return apply_highpass_fir(signal, cutoff_low, fs, numtaps=numtaps)
        elif ftype == "BPF":
            assert cutoff_low is not None and cutoff_high is not None
            return apply_bandpass_fir(signal, cutoff_low, cutoff_high, fs, numtaps=numtaps)

    raise ValueError(f"Unsupported filter: type={ftype}, method={method}")
