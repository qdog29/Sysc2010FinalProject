"""
loader.py
"""

import pandas as pd
import numpy as np

_EPOCH_MS_MIN, _EPOCH_MS_MAX = 1_000_000_000_000, 9_999_999_999_999
_EPOCH_S_MIN, _EPOCH_S_MAX = 1_000_000_000, 9_999_999_999


def _parse_time(series):
    numeric = pd.to_numeric(series, errors="coerce")
    if numeric.notna().all():
        vals = numeric.to_numpy(dtype=np.float64)
        if np.all((vals >= _EPOCH_MS_MIN) & (vals <= _EPOCH_MS_MAX)):
            vals = vals / 1000.0
        elif np.all((vals >= _EPOCH_S_MIN) & (vals <= _EPOCH_S_MAX)):
            pass
        return vals - np.nanmin(vals)
    try:
        dt = pd.to_datetime(series, errors="raise")
        return (dt - dt.min()).dt.total_seconds().to_numpy(dtype=np.float64)
    except Exception:
        raise ValueError(f"Cannot parse time column. Sample: '{series.iloc[0]}'")


def load_csv_numeric(path):
    try:
        df = pd.read_csv(path, engine="c", low_memory=False)
    except pd.errors.EmptyDataError:
        raise ValueError(f"CSV file is empty: {path}")

    if df.empty:
        raise ValueError(f"CSV file has no data rows: {path}")

    first_val = str(df.columns[0]).strip()
    try:
        float(first_val)
        df = pd.read_csv(path, engine="c", low_memory=False, header=None)
        if df.shape[1] == 1:
            df.columns = ["value"]
        elif df.shape[1] == 2:
            df.columns = ["timestamp", "value"]
        else:
            df.columns = ["timestamp"] + [f"ch_{i}" for i in range(df.shape[1] - 1)]
    except ValueError:
        pass

    if df.shape[1] == 1:
        raise ValueError(
            "CSV has only one column. A timestamp column is required so that "
            "the sampling rate can be derived from the data."
        )

    first_col = df.columns[0]
    t = _parse_time(df[first_col])

    sensor_cols, sensor_arrays = [], []
    for col in df.columns[1:]:
        converted = pd.to_numeric(df[col], errors="coerce")
        if converted.notna().any():
            sensor_cols.append(col)
            sensor_arrays.append(converted.to_numpy(dtype=np.float64))

    if not sensor_cols:
        raise ValueError(f"No numeric sensor columns found in {path}")

    data = np.column_stack([t] + sensor_arrays)
    headers = [first_col] + sensor_cols

    valid = np.isfinite(data[:, 0])
    data = data[valid]
    if data.shape[0] == 0:
        raise ValueError("No valid data after cleaning.")

    data = data[np.argsort(data[:, 0], kind="mergesort")]
    _, idx = np.unique(data[:, 0], return_index=True)
    data = data[idx]

    return headers, data
