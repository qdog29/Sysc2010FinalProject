"""
app.py
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import numpy as np
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure

from gui.guiHelpers import (
    add_title, add_subtitle, add_hint, add_label,
    add_dropdown, add_checkbox, add_entry,
    add_button, add_separator, ToolTip,
)
from config import SIGNAL_DEFAULTS
from data_loader import load_csv_numeric
from testing import timed

try:
    from preprocessing import interpolate_nans, normalize, remove_baseline, estimate_fs
except ImportError:
    interpolate_nans = normalize = remove_baseline = estimate_fs = None
    print("preprocessing not available yet")

try:
    from filters import apply_filter
except ImportError:
    apply_filter = None
    print("filters not available yet")

try:
    from analysis import compute_stats, compute_fft, extract_features
    from analysis.fft import dominant_frequency
except ImportError:
    compute_stats = compute_fft = extract_features = dominant_frequency = None
    print("analysis not available yet")


# Main Window -------------------------------------------------------------------------------------------------------------------------------------------------
class App(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title("SYSC 2010 — Signal Analysis Application")
        self.geometry("1150x720")

        self.data = None
        self.processed = None
        self.processing_applied = False
        self.channel_map = {}

        self.container = ttk.Frame(self)
        self.container.pack(fill="both", expand=True, padx=10, pady=10)

        self.import_frame = ImportFrame(self.container, self)
        self.import_frame.grid(row=0, column=0, sticky="nsew")

        self.analysis_frame = AnalysisFrame(self.container, self)
        self.analysis_frame.grid(row=0, column=0, sticky="nsew")

        self.container.rowconfigure(0, weight=1)
        self.container.columnconfigure(0, weight=1)

        self.show_import()

    def run(self):
        self.mainloop()

    def show_import(self):
        self.import_frame.tkraise()

    def show_analysis(self):
        self.analysis_frame.tkraise()
        self.analysis_frame.refresh_views()

    def set_dataset(self, headers, data):
        self.data = data

        self.channel_map = {}
        channel_names = []
        for i in range(1, len(headers)):
            name = headers[i] if headers[i] else f"col{i}"
            self.channel_map[name] = i
            channel_names.append(name)

        self.analysis_frame.set_channels(channel_names)

        # Initialize processed from whichever column is now selected
        col_idx = self.channel_map.get(channel_names[0], 1) if channel_names else 1
        raw = data[:, col_idx].astype(float)
        if interpolate_nans is not None:
            self.processed = interpolate_nans(raw)
        else:
            self.processed = raw.copy()
            print("interpolate_nans not implemented yet")


# Import Frame -------------------------------------------------------------------------------------------------------------------------------------------------
class ImportFrame(ttk.Frame):

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app

        r = 0
        r = add_title(self, r, "SYSC 2010 — Signal Analysis Application")
        r = add_subtitle(self, r, "Load a CSV file to begin analysis")
        r = add_hint(self, r, "Supported formats: ECG, Temperature, Respiration, IMU / Motion CSV files")

        self.path_var = tk.StringVar()
        path_entry = ttk.Entry(self, textvariable=self.path_var, width=64)
        path_entry.grid(row=r, column=0, sticky="ew")
        ToolTip(path_entry, "Enter file path or use Browse to select a CSV file")
        browse_btn = ttk.Button(self, text="Browse…", command=self.on_browse)
        browse_btn.grid(row=r, column=1, padx=6)
        ToolTip(browse_btn, "Open file dialog to select a CSV file")
        load_btn = ttk.Button(self, text="Load", command=self.on_load)
        load_btn.grid(row=r, column=2)
        ToolTip(load_btn, "Load the selected CSV file for analysis")
        r += 1

        r = add_hint(self, r,
            "After loading, select the signal type (ECG, Temperature, etc.) "
            "to apply appropriate processing parameters.",
            pady=(12, 0),
        )

        self.columnconfigure(0, weight=1)

    def on_browse(self):
        path = filedialog.askopenfilename(
            title="Select CSV file",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        )
        if path:
            self.path_var.set(path)

    def on_load(self):
        path = self.path_var.get().strip()
        if not path:
            messagebox.showwarning("No file", "Please select a CSV file first.")
            return
        try:
            headers, data = load_csv_numeric(path)
            self.app.set_dataset(headers, data)
            self.app.show_analysis()
        except Exception as e:
            messagebox.showerror("Load failed", str(e))


# Analysis Frame -------------------------------------------------------------------------------------------------------------------------------------------------
class AnalysisFrame(ttk.Frame):

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app

        self.controls = ttk.Frame(self, width=230)
        self.controls.grid(row=0, column=0, sticky="nsw", padx=(0, 8))

        self.view = ttk.Frame(self)
        self.view.grid(row=0, column=1, sticky="nsew")

        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        self.build_controls()
        self.build_notebook()

    # Left-side controls panel -----------------------------------------------------------------
    def build_controls(self):
        c = self.controls
        r = 0

        r = add_label(c, r, "Controls", bold=True)

        self.signal_type, self.signal_type_menu, r = add_dropdown(
            c, r, "Signal Type", "ECG",
            list(SIGNAL_DEFAULTS.keys()),
            command=self.on_signal_type_changed,
        )
        ToolTip(self.signal_type_menu, "Select the type of sensor signal to set recommended parameters")

        self.channel, self.channel_menu, r = add_dropdown(
            c, r, "Signal Column", "col1", [],
            command=self.on_channel_changed,
        )
        ToolTip(self.channel_menu, "Select which data column to analyze")

        r = add_separator(c, r)
        r = add_label(c, r, "Preprocessing", bold=True)
        self.do_interp, r = add_checkbox(c, r, "Interpolate missing values", default=True)
        self.do_norm, r = add_checkbox(c, r, "Normalize (min-max)")
        self.do_baseline, r = add_checkbox(c, r, "Baseline correction")

        r = add_separator(c, r)
        r = add_label(c, r, "Filtering", bold=True)
        self.filter_type, ft_menu, r = add_dropdown(c, r, "Filter Type", "None", ["None", "LPF", "HPF", "BPF"])
        ToolTip(ft_menu, "LPF = Low-Pass, HPF = High-Pass, BPF = Band-Pass")
        self.filter_method, fm_menu, r = add_dropdown(c, r, "Method", "FIR", ["FIR", "IIR"])
        ToolTip(fm_menu, "FIR = Finite Impulse Response, IIR = Infinite Impulse Response")
        self.cut_low, r = add_entry(c, r, "Cutoff Low (Hz) — HPF / BPF", default="0.5")
        self.cut_high, r = add_entry(c, r, "Cutoff High (Hz) — LPF / BPF", default="40.0")
        self.filter_order, r = add_entry(c, r, "Filter Order", default="4")

        r = add_separator(c, r)
        r = add_button(c, r, "Apply Processing", command=self.on_apply, pady=(2, 0))
        r = add_button(c, r, "Reset to Raw", command=self.on_reset)
        r = add_button(c, r, "Reload File", command=self.on_reload)

        c.columnconfigure(0, weight=1)

    # Right-side notebook with tabs ------------------------------------------------------------
    def build_notebook(self):
        self.nb = ttk.Notebook(self.view)
        self.nb.pack(fill="both", expand=True)
        self.nb.bind("<<NotebookTabChanged>>", self._on_tab_changed)
        self._stale_tabs = {"fft": True, "stats": True}

        # Tab 1: Time domain
        self.time_tab = ttk.Frame(self.nb)
        self.nb.add(self.time_tab, text="  Time Domain  ")

        # View mode toggle bar
        view_bar = ttk.Frame(self.time_tab)
        view_bar.pack(fill="x", padx=4, pady=(4, 0))
        ttk.Label(view_bar, text="View:").pack(side="left", padx=(4, 6))
        self.time_view_mode = tk.StringVar(value="Overlay")
        for mode in ("Overlay", "Raw Only", "Processed Only", "Side by Side"):
            rb = ttk.Radiobutton(
                view_bar, text=mode, variable=self.time_view_mode,
                value=mode, command=self._redraw_time_plot,
            )
            rb.pack(side="left", padx=4)

        self.dual_yaxis = tk.BooleanVar(value=False)
        ttk.Checkbutton(view_bar, text="Dual Y-Axis", variable=self.dual_yaxis,
                         command=self._redraw_time_plot).pack(side="left", padx=(12, 4))

        self.show_markers = tk.BooleanVar(value=False)
        ttk.Checkbutton(view_bar, text="Show Points", variable=self.show_markers,
                         command=self._redraw_time_plot).pack(side="left", padx=(12, 4))

        self.time_fig = Figure(figsize=(7, 4), dpi=100)
        self.time_ax = self.time_fig.add_subplot(111)
        self.time_canvas = FigureCanvasTkAgg(self.time_fig, master=self.time_tab)
        self.time_canvas.get_tk_widget().pack(fill="both", expand=True)
        NavigationToolbar2Tk(self.time_canvas, self.time_tab)

        # Cursor readout label
        self.cursor_label = ttk.Label(self.time_tab, text="", anchor="w",
                                       font=("Courier", 10))
        self.cursor_label.pack(fill="x", padx=6, pady=(0, 2))

        # Store series data for hover lookup
        self._hover_t = None
        self._hover_raw = None
        self._hover_proc = None
        self._vline = None
        self.time_canvas.mpl_connect("motion_notify_event", self._on_time_hover)

        # Tab 2: FFT
        self.fft_tab = ttk.Frame(self.nb)
        self.nb.add(self.fft_tab, text="  FFT  ")
        self.fft_fig = Figure(figsize=(7, 4), dpi=100)
        self.fft_ax = self.fft_fig.add_subplot(111)
        self.fft_canvas = FigureCanvasTkAgg(self.fft_fig, master=self.fft_tab)
        self.fft_canvas.get_tk_widget().pack(fill="both", expand=True)
        NavigationToolbar2Tk(self.fft_canvas, self.fft_tab)

        # Tab 3: Statistics and features
        self.stats_tab = ttk.Frame(self.nb)
        self.nb.add(self.stats_tab, text="  Statistics & Features  ")
        self.stats_text = tk.Text(
            self.stats_tab, height=22, width=65,
            font=("Courier", 11), padx=10, pady=10,
        )
        self.stats_text.pack(fill="both", expand=True, padx=4, pady=4)

    # Callbacks --------------------------------------------------------------------------------
    def on_signal_type_changed(self, *_args):
        sig = self.signal_type.get()
        defaults = SIGNAL_DEFAULTS.get(sig)
        if defaults:
            self.cut_low.set(str(defaults["hpf_cutoff"]))
            self.cut_high.set(str(defaults["lpf_cutoff"]))
            self.filter_order.set(str(defaults["filter_order"]))

    def on_channel_changed(self, *_args):
        try:
            self.app.processing_applied = False
            _, y_raw = self.get_selected_series()
            if interpolate_nans is not None:
                self.app.processed = interpolate_nans(y_raw)
            else:
                self.app.processed = y_raw.copy()
            self.refresh_views()
        except Exception as e:
            messagebox.showerror("Channel switch failed", str(e))

    def on_apply(self):
        try:
            with timed(f"Total GUI update time"):
                t, y_raw = self.get_selected_series()
                y = y_raw.copy()
                sig_type = self.signal_type.get()

                if estimate_fs is not None:
                    fs = estimate_fs(t)
                else:
                    print("estimate_fs not implemented yet")
                    return

                if self.do_interp.get():
                    if interpolate_nans is not None:
                        y = interpolate_nans(y)
                    else:
                        print("interpolate_nans not implemented yet")
                elif np.any(~np.isfinite(y)):
                    raise ValueError("Signal has missing values. Enable interpolation or fix the CSV.")

                if self.do_baseline.get():
                    if remove_baseline is not None:
                        sig_defaults = SIGNAL_DEFAULTS.get(sig_type, {})
                        cutoff = sig_defaults.get("hpf_cutoff", 0.5)
                        y = remove_baseline(y, fs, cutoff)
                    else:
                        print("remove_baseline not implemented yet")

                
                ftype = self.filter_type.get()
                if ftype != "None":
                    if apply_filter is not None:
                        method = self.filter_method.get()
                        try:
                            cutoff_low = float(self.cut_low.get()) if self.cut_low.get().strip() else None
                        except ValueError:
                            raise ValueError(f"Cutoff Low must be a number, got '{self.cut_low.get()}'.")
                        try:
                            cutoff_high = float(self.cut_high.get()) if self.cut_high.get().strip() else None
                        except ValueError:
                            raise ValueError(f"Cutoff High must be a number, got '{self.cut_high.get()}'.")
                        try:
                            order = int(self.filter_order.get()) if self.filter_order.get().strip() else 4
                        except ValueError:
                            raise ValueError(f"Filter Order must be an integer, got '{self.filter_order.get()}'.")

                        # Validate that the correct cutoff field is provided for the filter type
                        if ftype == "LPF" and cutoff_high is None:
                            raise ValueError("LPF requires a Cutoff High value.")
                        if ftype == "HPF" and cutoff_low is None:
                            raise ValueError("HPF requires a Cutoff Low value.")
                        if ftype == "BPF" and (cutoff_low is None or cutoff_high is None):
                            raise ValueError("BPF requires both Cutoff Low and Cutoff High values.")
                        if ftype == "BPF" and cutoff_low >= cutoff_high:
                            raise ValueError(f"Cutoff Low ({cutoff_low}) must be less than Cutoff High ({cutoff_high}).")

                        nyq = fs / 2.0
                        if cutoff_low is not None and cutoff_low >= nyq:
                            raise ValueError(f"Cutoff Low ({cutoff_low} Hz) must be less than Nyquist ({nyq:.1f} Hz).")
                        if cutoff_high is not None and cutoff_high >= nyq:
                            raise ValueError(f"Cutoff High ({cutoff_high} Hz) must be less than Nyquist ({nyq:.1f} Hz).")

                        y = apply_filter(y, fs, ftype, method, cutoff_low, cutoff_high, order=order)
                    else:
                        print("apply_filter not implemented yet")


                if self.do_norm.get():
                    if normalize is not None:
                        y = normalize(y)
                    else:
                        print("normalize not implemented yet")

                self.app.processed = y
                self.app.processing_applied = True

                self.refresh_views()

        except Exception as e:
                messagebox.showerror("Processing failed", str(e))

    def on_reset(self):
        if self.app.data is None:
            return
        self.app.processing_applied = False
        _, y_raw = self.get_selected_series()
        if interpolate_nans is not None:
            self.app.processed = interpolate_nans(y_raw)
        else:
            self.app.processed = y_raw.copy()
        self.refresh_views()

    def on_reload(self):
        self.app.show_import()

    # Helpers ----------------------------------------------------------------------------------
    def set_channels(self, channel_names):
        menu = self.channel_menu["menu"]
        menu.delete(0, "end")
        if not channel_names:
            channel_names = ["col1"]
        self.channel.set(channel_names[0])
        for name in channel_names:
            menu.add_command(label=name, command=lambda v=name: self.channel.set(v))

    def get_selected_series(self):
        if self.app.data is None or self.app.data.size == 0:
            raise ValueError("No data loaded. Please load a CSV file first.")
        t = self.app.data[:, 0].astype(float)
        col_idx = self.app.channel_map.get(self.channel.get(), 1)
        if col_idx >= self.app.data.shape[1]:
            raise ValueError(f"Selected column index {col_idx} is out of range.")
        y = self.app.data[:, col_idx].astype(float)
        return t, y

    def refresh_views(self):
        try:
            self._refresh_views_inner()
        except Exception as e:
            messagebox.showerror("Display error", str(e))

    def _redraw_time_plot(self):
        """Redraw just the time-domain plot when the view mode changes."""
        if self.app.data is None:
            return
        try:
            t, y_raw = self.get_selected_series()
            y_proc = np.asarray(self.app.processed, dtype=float)
            self._draw_time_axes(t, y_raw, y_proc, self.signal_type.get())
        except Exception as e:
            messagebox.showerror("Display error", str(e))

    def _draw_time_axes(self, t, y_raw, y_proc, sig_type):
        """Render the time-domain figure based on the current view mode."""
        mode = self.time_view_mode.get()
        has_processing = self.app.processing_applied
        self.time_fig.clear()
        mkr = dict(marker="o", markersize=3) if self.show_markers.get() else {}

        # When normalize is enabled, scale only the processed signal
        if self.do_norm.get() and normalize is not None and has_processing:
            y_proc = normalize(y_proc)

        # If no processing applied yet, just show raw regardless of view mode
        if not has_processing:
            ax = self.time_fig.add_subplot(111)
            self.time_ax = ax
            ax.plot(t, y_raw, color="tab:blue", linewidth=0.8, label="Raw", **mkr)
            ax.legend(loc="upper right")
            ax.set_title(f"Time Domain — {sig_type}")
            ax.set_xlabel("Time (s)")
            ax.set_ylabel("Amplitude")
            ax.grid(True, alpha=0.3)
            self._hover_t = t
            self._hover_raw = y_raw
            self._hover_proc = None
            self._vline = None
            self.time_fig.tight_layout()
            self.time_canvas.draw()
            return

        if mode == "Side by Side":
            # Independent y-axes so each panel auto-scales to its own data
            ax1 = self.time_fig.add_subplot(1, 2, 1)
            ax2 = self.time_fig.add_subplot(1, 2, 2)
            ax1.plot(t, y_raw, color="tab:blue", linewidth=0.8, **mkr)
            ax1.set_title(f"Raw — {sig_type}")
            ax1.set_xlabel("Time (s)")
            ax1.set_ylabel("Amplitude")
            ax1.grid(True, alpha=0.3)
            ax2.plot(t, y_proc, color="tab:orange", linewidth=1.0, **mkr)
            ax2.set_title(f"Processed — {sig_type}")
            ax2.set_xlabel("Time (s)")
            ax2.set_ylabel("Amplitude")
            ax2.grid(True, alpha=0.3)
            self.time_ax = ax1  # keep reference for toolbar
        elif mode == "Overlay":
            ax = self.time_fig.add_subplot(111)
            self.time_ax = ax
            if self.dual_yaxis.get():
                ax.plot(t, y_raw, alpha=0.7, color="tab:blue", label="Raw", linewidth=0.8, **mkr)
                ax.set_ylabel("Raw", color="tab:blue")
                ax.tick_params(axis="y", labelcolor="tab:blue")
                ax2 = ax.twinx()
                ax2.plot(t, y_proc, alpha=0.85, color="tab:orange", label="Processed", linewidth=1.0, **mkr)
                ax2.set_ylabel("Processed", color="tab:orange")
                ax2.tick_params(axis="y", labelcolor="tab:orange")
                lines1, labels1 = ax.get_legend_handles_labels()
                lines2, labels2 = ax2.get_legend_handles_labels()
                ax.legend(lines1 + lines2, labels1 + labels2, loc="upper right")
            else:
                ax.plot(t, y_raw, alpha=0.55, color="tab:blue", label="Raw", linewidth=0.8, **mkr)
                ax.plot(t, y_proc, alpha=0.85, color="tab:orange", label="Processed", linewidth=1.0, **mkr)
                ax.set_ylabel("Amplitude")
                ax.legend(loc="upper right")
            ax.set_title(f"Time Domain — {sig_type}")
            ax.set_xlabel("Time (s)")
            ax.grid(True, alpha=0.3)
        elif mode == "Raw Only":
            ax = self.time_fig.add_subplot(111)
            self.time_ax = ax
            ax.plot(t, y_raw, color="tab:blue", linewidth=0.8, label="Raw", **mkr)
            ax.legend(loc="upper right")
            ax.set_title(f"Time Domain — {sig_type}")
            ax.set_xlabel("Time (s)")
            ax.set_ylabel("Amplitude")
            ax.grid(True, alpha=0.3)
        elif mode == "Processed Only":
            ax = self.time_fig.add_subplot(111)
            self.time_ax = ax
            ax.plot(t, y_proc, color="tab:orange", linewidth=1.0, label="Processed", **mkr)
            ax.legend(loc="upper right")
            ax.set_title(f"Time Domain — {sig_type}")
            ax.set_xlabel("Time (s)")
            ax.set_ylabel("Amplitude")
            ax.grid(True, alpha=0.3)

        # Store series for hover readout
        self._hover_t = t
        if mode in ("Raw Only", "Overlay", "Side by Side"):
            self._hover_raw = y_raw
        else:
            self._hover_raw = None
        if mode in ("Processed Only", "Overlay", "Side by Side"):
            self._hover_proc = y_proc
        else:
            self._hover_proc = None
        self._vline = None

        self.time_fig.tight_layout()
        self.time_canvas.draw()

    def _on_time_hover(self, event):
        """Show signal values at the cursor's x position."""
        if event.inaxes is None or self._hover_t is None:
            self.cursor_label.config(text="")
            return

        x = event.xdata
        t = self._hover_t
        parts = [f"t = {x:.4f}s"]

        if self._hover_raw is not None:
            idx = np.searchsorted(t, x, side="left")
            idx = np.clip(idx, 0, len(t) - 1)
            val = self._hover_raw[idx]
            parts.append(f"Raw = {val:.4f}" if np.isfinite(val) else "Raw = NaN")

        if self._hover_proc is not None:
            idx = np.searchsorted(t, x, side="left")
            idx = np.clip(idx, 0, len(t) - 1)
            val = self._hover_proc[idx]
            parts.append(f"Processed = {val:.4f}" if np.isfinite(val) else "Processed = NaN")

        self.cursor_label.config(text="    ".join(parts))

    def _on_tab_changed(self, _event=None):
        """Draw a tab's content on demand when the user switches to it."""
        if self.app.data is None:
            return
        tab_id = self.nb.index(self.nb.select())
        if tab_id == 1 and self._stale_tabs.get("fft"):
            self._draw_fft()
        elif tab_id == 2 and self._stale_tabs.get("stats"):
            self._draw_stats()

    def _refresh_views_inner(self):
        t, y_raw = self.get_selected_series()
        y_proc = np.asarray(self.app.processed, dtype=float)
        sig_type = self.signal_type.get()

        # Always draw the time-domain plot (visible by default)
        self._draw_time_axes(t, y_raw, y_proc, sig_type)

        # Mark other tabs as needing a redraw
        self._stale_tabs = {"fft": True, "stats": True}

        # If one of those tabs is currently active, draw it now
        tab_id = self.nb.index(self.nb.select())
        if tab_id == 1:
            self._draw_fft()
        elif tab_id == 2:
            self._draw_stats()

    def _draw_fft(self):
        t, y_raw = self.get_selected_series()
        y_proc = np.asarray(self.app.processed, dtype=float)
        sig_type = self.signal_type.get()

        fs = None
        if estimate_fs is not None:
            fs = estimate_fs(t)

        self.fft_ax.clear()
        if compute_fft is not None and dominant_frequency is not None and fs is not None:
            freqs_proc, mag_proc = compute_fft(y_proc, fs)
            dom_freq = dominant_frequency(freqs_proc, mag_proc)

            if self.app.processing_applied:
                freqs_raw, mag_raw = compute_fft(
                    interpolate_nans(y_raw) if interpolate_nans is not None else y_raw,
                    fs,
                )
                self.fft_ax.plot(freqs_raw, mag_raw, linewidth=0.8,
                                 color="#1f77b4", alpha=0.45, label="Raw")
                self.fft_ax.plot(freqs_proc, mag_proc, linewidth=0.9,
                                 color="#ff7f0e", label="Processed")
            else:
                self.fft_ax.plot(freqs_proc, mag_proc, linewidth=0.9)

            self.fft_ax.axvline(dom_freq, color="r", linestyle="--", alpha=0.6,
                                label=f"Dominant: {dom_freq:.2f} Hz")
            self.fft_ax.legend(loc="upper right")
        else:
            print("compute_fft not implemented yet")
        self.fft_ax.set_title(f"FFT Magnitude — {sig_type}")
        self.fft_ax.set_xlabel("Frequency (Hz)")
        self.fft_ax.set_ylabel("Magnitude")
        self.fft_ax.grid(True, alpha=0.3)
        self.fft_fig.tight_layout()
        self.fft_canvas.draw()
        self._stale_tabs["fft"] = False

    def _draw_stats(self):
        t, _ = self.get_selected_series()
        y_proc = np.asarray(self.app.processed, dtype=float)
        sig_type = self.signal_type.get()
        col_name = self.channel.get()

        fs = None
        if estimate_fs is not None:
            fs = estimate_fs(t)

        self.stats_text.delete("1.0", "end")
        self.stats_text.insert("end", f"  Signal Type   : {sig_type}\n")
        self.stats_text.insert("end", f"  Column        : {col_name}\n")
        self.stats_text.insert("end", f"  Samples       : {len(y_proc)}\n")

        if fs is not None:
            self.stats_text.insert("end", f"  Sampling Rate : {fs:.2f} Hz\n")

        duration = float(t[-1] - t[0]) if len(t) > 1 else 0.0
        self.stats_text.insert("end", f"  Duration      : {duration:.4f} s\n")

        self.stats_text.insert("end", "\n  ── Basic Statistics ─────────────────\n\n")
        if compute_stats is not None:
            stats = compute_stats(y_proc)
            for k, v in stats.items():
                self.stats_text.insert("end", f"    {k:>14} : {v:.6g}\n")
        else:
            self.stats_text.insert("end", "    compute_stats not implemented yet\n")
            print("compute_stats not implemented yet")

        self.stats_text.insert("end", f"\n  ── {sig_type} Features ──────────────\n\n")
        if extract_features is not None and fs is not None:
            features = extract_features(y_proc, fs, sig_type, time=t)
            for k, v in features.items():
                self.stats_text.insert("end", f"    {k:>24} : {v}\n")
        else:
            self.stats_text.insert("end", "    extract_features not implemented yet\n")
            print("extract_features not implemented yet")
        self._stale_tabs["stats"] = False

