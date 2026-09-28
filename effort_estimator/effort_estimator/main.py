"""
main.py
-------
Entry point.  Run:  python main.py
"""

import tkinter as tk

from ui import EstimatorApp


def _enable_high_dpi():
    """Sharper fonts on Windows high-DPI screens (no-op elsewhere)."""
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass


def main():
    _enable_high_dpi()
    root = tk.Tk()
    EstimatorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
