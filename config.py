"""
config.py
"""

SIGNAL_DEFAULTS = {
    "ECG":          {"lpf_cutoff": 40.0, "hpf_cutoff": 0.5,   "filter_order": 4},
    "Temperature":  {"lpf_cutoff": 0.1,  "hpf_cutoff": 0.005, "filter_order": 2},
    "Respiration":  {"lpf_cutoff": 1.0,  "hpf_cutoff": 0.05,  "filter_order": 3},
    "IMU / Motion": {"lpf_cutoff": 20.0, "hpf_cutoff": 0.1,   "filter_order": 4},
}
