# SYSC 2010 — Signal Analysis Application

A Python GUI application for preprocessing, filtering, visualizing, and extracting features from biomedical and sensor signals. Built for the SYSC 2010 Programming Project at Carleton University.

## Setup

```bash

git clone <your-repo-url>
cd sysc2010_final_project
python3 -m venv venv
source venv/bin/activate        # macOS / Linux
# venv\Scripts\activate         # Windows
pip install -r requirements.txt
python main.py

```

## Supported Signals

ECG, Temperature, Respiration, and IMU/Motion. CSV files must have a time column first, followed by signal data columns. Sampling rate is auto-detected from the time column.

## Features

- **Preprocessing:** interpolate missing values, baseline correction, normalize [-1, 1]
- **Filtering:** LPF, HPF, BPF with IIR (Butterworth) or FIR methods, configurable cutoffs and order
- **Visualization:** overlay, raw/processed only, side by side, dual Y-axis, show points, FFT comparison
- **Statistics:** mean, std, rms, peak-to-peak, min, max, median, signal duration
- **Feature extraction:** R-peaks and heart rate (ECG), trend slope (Temperature), breathing rate (Respiration), peak acceleration (IMU)

## File Structure


sysc2010_final_project/
├── main.py                  # Entry point
├── config.py                # Default filter parameters per signal type
├── requirements.txt         # Python dependencies
├── README.md
│
├── gui/
│   ├── app.py               # Main application window, ImportFrame, AnalysisFrame
│   └── guiHelpers.py        # Reusable GUI widget builders and tooltips
│
├── data_loader/
│   └── loader.py            # CSV loading, time parsing, data cleaning
│
├── preprocessing/
│   └── preprocessor.py      # Interpolation, normalization, baseline removal, fs estimation
│
├── filters/
│   └── filters.py           # IIR/FIR filter implementations and unified dispatcher
│
├── analysis/
│   ├── statistics.py        # Basic statistical computations
│   ├── features.py          # Signal-type-specific feature extraction
│   └── fft.py               # FFT computation and dominant frequency detection
│
└── testing/
    └── gui_refresh_timer.py  # Performance timing utility


## Known Limitations

- FIR filters require sufficient samples relative to filter order — use IIR for very short signals
- R-peak detection uses 40% max threshold with 0.3s minimum distance — may need tuning for unusual ECG
- Normalization without baseline correction compresses signals with large DC offsets

## Author

Name: Quinlan Taylor
Student Number: 101332711