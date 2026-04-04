"""
guihelpers.py
"""

import tkinter as tk
from tkinter import ttk


class ToolTip:

    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip_window = None
        widget.bind("<Enter>", self._show)
        widget.bind("<Leave>", self._hide)

    def _show(self, _event=None):
        if self.tip_window:
            return
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 4
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(
            tw, text=self.text, justify="left",
            background="#ffffe0", relief="solid", borderwidth=1,
            font=("", 10),
        )
        label.pack(ipadx=4, ipady=2)

    def _hide(self, _event=None):
        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None


def add_label(parent, row: int, text: str, bold: bool = False, pady: tuple = (0, 0)) -> int:
    font = ("", 11, "bold") if bold else None
    ttk.Label(parent, text=text, font=font).grid(row=row, column=0, sticky="w", pady=pady)
    return row + 1


def add_title(parent, row: int, text: str, size: int = 16) -> int:
    ttk.Label(parent, text=text, font=("", size, "bold")).grid(row=row, column=0, columnspan=3, sticky="w", pady=(0, 4))
    return row + 1


def add_subtitle(parent, row: int, text: str, size: int = 12) -> int:
    ttk.Label(parent, text=text, font=("", size)).grid(row=row, column=0, columnspan=3, sticky="w", pady=(0, 12))
    return row + 1


def add_hint(parent, row: int, text: str, pady: tuple = (2, 0)) -> int:
    ttk.Label(parent, text=text, foreground="gray").grid(row=row, column=0, columnspan=3, sticky="w", pady=pady)
    return row + 1


def add_dropdown(parent, row: int, label: str, default: str, options: list[str],
                 command=None) -> tuple[tk.StringVar, ttk.OptionMenu, int]:
    ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", pady=(8, 0))
    row += 1
    var = tk.StringVar(value=default)
    menu = ttk.OptionMenu(parent, var, default, *options, command=command)
    menu.grid(row=row, column=0, sticky="ew")
    return var, menu, row + 1


def add_checkbox(parent, row: int, text: str, default: bool = False) -> tuple[tk.BooleanVar, int]:
    var = tk.BooleanVar(value=default)
    ttk.Checkbutton(parent, text=text, variable=var).grid(row=row, column=0, sticky="w")
    return var, row + 1


def add_entry(parent, row: int, label: str, default: str = "", width: int = 14) -> tuple[tk.StringVar, int]:
    ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", pady=(6, 0))
    row += 1
    var = tk.StringVar(value=default)
    ttk.Entry(parent, textvariable=var, width=width).grid(row=row, column=0, sticky="ew")
    return var, row + 1


def add_button(parent, row: int, text: str, command=None, pady: tuple = (4, 0)) -> int:
    ttk.Button(parent, text=text, command=command).grid(row=row, column=0, sticky="ew", pady=pady)
    return row + 1


def add_separator(parent, row: int, pady: int = 8) -> int:
    ttk.Separator(parent, orient="horizontal").grid(row=row, column=0, sticky="ew", pady=pady)
    return row + 1
