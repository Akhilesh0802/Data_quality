"""
ui.py
-----
Main window with tabs (one per estimator in config.ESTIMATORS).
Each tab is fully independent. Grant Thornton Bharat LLP - purple & grey theme.
"""

import tkinter as tk
from tkinter import filedialog, messagebox

import calculator as calc
import email_share
import exporter
from export_dialog import ask_export_details
from config import APP_TITLE, COMPANY_NAME, ESTIMATORS, HOURS_PER_DAY
from theme import (GREY_BG, GREY_CHARCOAL, GREY_DARK, GREY_TEXT, PURPLE,
                   PURPLE_DARK, PURPLE_LIGHT, WHITE, font)
from widgets import (BreakdownRow, Card, Dropdown, HoverButton, SegmentedControl,
                     StatCard)

TAB_IDLE_FG = "#D9CCEB"


# ======================================================================
# One estimator page (used for every tab)
# ======================================================================
class EstimatorPage(tk.Frame):
    def __init__(self, master, est_key, toast):
        super().__init__(master, bg=GREY_BG, padx=28, pady=14)
        self.key = est_key
        self.cfg = ESTIMATORS[est_key]
        self._toast = toast
        self.result = None

        self.level_keys = [k for k in self.cfg["matrix"] if not calc.is_direct(est_key, k)]
        self.direct_keys = [k for k in self.cfg["matrix"] if calc.is_direct(est_key, k)]

        self.band_vars = {k: tk.StringVar(value=calc.get_bands(est_key, k)[0]) for k in self.cfg["scopes"]}
        self.pill_vars = {k: tk.StringVar() for k in self.cfg["scopes"]}
        self.level_vars = {k: tk.StringVar(value=calc.get_levels(est_key, k)[0]) for k in self.level_keys}
        self.hint_vars = {k: tk.StringVar() for k in self.level_keys}
        self.guide_rows = {}          # direct items: band -> (row_frame, labels)

        self._build()
        self.recalculate()

    # ------------------------------------------------------------ layout
    def _build(self):
        self.columnconfigure(0, weight=5, uniform="col")
        self.columnconfigure(1, weight=6, uniform="col")
        self.rowconfigure(0, weight=1)

        left = tk.Frame(self, bg=GREY_BG)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        right = tk.Frame(self, bg=GREY_BG)
        right.grid(row=0, column=1, sticky="nsew", padx=(12, 0))

        self._build_scope_card(left)
        if self.level_keys:
            self._build_complexity_card(left)
        else:                                   # guide only when there is room
            for d_key in self.direct_keys:
                self._build_guide_card(left, d_key)
        self._build_summary(right)

    def _build_scope_card(self, parent):
        card = Card(parent, "Scope")
        card.pack(fill="x")
        c = card.content
        c.columnconfigure(0, weight=1)
        row = 0
        if self.cfg.get("mode"):
            tk.Label(c, text="Mode of Delivery", font=font(10, "bold"),
                     fg=GREY_DARK, bg=WHITE).grid(row=row, column=0, sticky="w", pady=(0, 6))
            tk.Label(c, text=self.cfg["mode"], font=font(9, "bold"), fg=WHITE, bg=PURPLE,
                     padx=10, pady=3).grid(row=row, column=1, columnspan=2, sticky="e", pady=(0, 6))
            row += 1
        for s_key, s_cfg in self.cfg["scopes"].items():
            self._scope_row(c, row, s_key, s_cfg)
            row += 1

    def _scope_row(self, parent, row, s_key, s_cfg):
        text = tk.Frame(parent, bg=WHITE)
        text.grid(row=row, column=0, sticky="w", pady=4)
        tk.Label(text, text=s_cfg["label"], font=font(10, "bold"), fg=GREY_DARK, bg=WHITE).pack(anchor="w")
        tk.Label(text, text=s_cfg["subtitle"], font=font(9), fg=GREY_TEXT, bg=WHITE).pack(anchor="w")

        Dropdown(parent, calc.get_bands(self.key, s_key), self.band_vars[s_key],
                 command=self.recalculate, width=8).grid(row=row, column=1, padx=(12, 8), pady=6)

        tk.Label(parent, textvariable=self.pill_vars[s_key], font=font(9, "bold"), fg=PURPLE,
                 bg=PURPLE_LIGHT, padx=10, pady=3, width=5).grid(row=row, column=2, pady=6)

    def _build_complexity_card(self, parent):
        card = Card(parent, "Complexity")
        card.pack(fill="both", expand=True, pady=(12, 0))
        for i, i_key in enumerate(self.level_keys):
            i_cfg = self.cfg["matrix"][i_key]
            block = tk.Frame(card.content, bg=WHITE)
            block.pack(fill="x", pady=(0 if i == 0 else 8, 0))
            top = tk.Frame(block, bg=WHITE)
            top.pack(fill="x")
            tk.Label(top, text=i_cfg["label"], font=font(10, "bold"),
                     fg=GREY_DARK, bg=WHITE).pack(side="left")
            tk.Label(top, textvariable=self.hint_vars[i_key], font=font(9),
                     fg=GREY_TEXT, bg=WHITE).pack(side="right")
            SegmentedControl(block, calc.get_levels(self.key, i_key), self.level_vars[i_key],
                             command=self.recalculate).pack(fill="x", pady=(4, 0))

    def _build_guide_card(self, parent, d_key):
        """Reference table for direct-lookup items; click a row to select it."""
        i_cfg = self.cfg["matrix"][d_key]
        s_key = i_cfg["scope"]
        s_cfg = self.cfg["scopes"][s_key]
        card = Card(parent, "Effort Guide")
        card.pack(fill="both", expand=True, pady=(12, 0))
        tk.Label(card.content, text="Click a row to select", font=font(9),
                 fg=GREY_TEXT, bg=WHITE).pack(anchor="w", pady=(0, 6))

        for band, hours in i_cfg["hours_by_band"].items():
            unit = s_cfg.get("unit_singular", s_cfg["unit"]) if band == "1" else s_cfg["unit"]
            row = tk.Frame(card.content, bg=WHITE, cursor="hand2", padx=12, pady=7)
            row.pack(fill="x", pady=1)
            left = tk.Label(row, text=f"{band} {unit}", font=font(10, "bold"), bg=WHITE, fg=GREY_DARK)
            left.pack(side="left")
            right = tk.Label(row, text=f"{calc.fmt(hours)} hrs", font=font(10, "bold"), bg=WHITE, fg=PURPLE)
            right.pack(side="right")
            for w in (row, left, right):
                w.bind("<Button-1>", lambda _e, b=band, s=s_key: self._pick_band(s, b))
                w.bind("<Enter>", lambda _e, b=band: self._guide_hover(b, True))
                w.bind("<Leave>", lambda _e, b=band: self._guide_hover(b, False))
            self.guide_rows[band] = (row, left, right, s_key)

    def _pick_band(self, s_key, band):
        self.band_vars[s_key].set(band)
        self.recalculate()

    def _guide_hover(self, band, entering):
        row, left, right, s_key = self.guide_rows[band]
        if self.band_vars[s_key].get() == band:
            return
        bg = PURPLE_LIGHT if entering else WHITE
        for w in (row, left, right):
            w.configure(bg=bg)

    def _render_guide(self):
        for band, (row, left, right, s_key) in self.guide_rows.items():
            selected = self.band_vars[s_key].get() == band
            bg = PURPLE if selected else WHITE
            for w in (row, left, right):
                w.configure(bg=bg)
            left.configure(fg=WHITE if selected else GREY_DARK)
            right.configure(fg=WHITE if selected else PURPLE)

    def _build_summary(self, parent):
        stats = tk.Frame(parent, bg=GREY_BG)
        stats.pack(fill="x")
        stats.columnconfigure(0, weight=1, uniform="stat")
        stats.columnconfigure(1, weight=1, uniform="stat")
        self.hours_card = StatCard(stats, "Total Effort", "hours", PURPLE)
        self.hours_card.grid(row=0, column=0, sticky="nsew", padx=(0, 9))
        self.days_card = StatCard(stats, "Total Duration", "days", GREY_CHARCOAL)
        self.days_card.grid(row=0, column=1, sticky="nsew", padx=(9, 0))
        self.days_card.set_subtitle(f"@ {HOURS_PER_DAY} working hours / day")

        card = Card(parent, "Effort Breakdown")
        card.pack(fill="both", expand=True, pady=(12, 0))
        self.rows = {}
        for i, (i_key, i_cfg) in enumerate(self.cfg["matrix"].items()):
            row = BreakdownRow(card.content, i_cfg["label"])
            row.pack(fill="x", pady=(0 if i == 0 else 8, 0))
            self.rows[i_key] = row

        actions = tk.Frame(parent, bg=GREY_BG)
        actions.pack(fill="x", pady=(12, 0))
        HoverButton(actions, "Share Estimate", self.share_estimate, "primary").pack(side="right")
        HoverButton(actions, "Reset", self.reset, "secondary").pack(side="right", padx=10)

    # ----------------------------------------------------------- actions
    def recalculate(self):
        try:
            result = calc.calculate(self.key,
                                    {k: v.get() for k, v in self.band_vars.items()},
                                    {k: v.get() for k, v in self.level_vars.items()})
        except calc.EstimationError as exc:
            messagebox.showerror("Invalid selection", str(exc))
            return
        self.result = result
        items = {item.key: item for item in result.items}

        # scope pills: multiplier, or hours for direct-lookup scopes
        for s in result.scopes:
            if s.direct:
                hrs = sum(it.final_hours for k, it in items.items()
                          if k in self.direct_keys and self.cfg["matrix"][k]["scope"] == s.key)
                self.pill_vars[s.key].set(f"{calc.fmt(hrs)} h")
            else:
                self.pill_vars[s.key].set(f"× {s.multiplier}")

        total = result.total_hours
        for item in result.items:
            share = item.final_hours / total if total else 0
            if item.key in self.hint_vars:
                s_cfg = self.cfg["scopes"][self.cfg["matrix"][item.key]["scope"]]
                if s_cfg.get("direct"):
                    bands = list(s_cfg["bands"])
                    self.hint_vars[item.key].set(
                        f"{calc.fmt(item.base_hours)} hrs flat for {bands[0]}-{bands[-1]} {s_cfg['unit']}")
                else:
                    self.hint_vars[item.key].set(
                        f"{calc.fmt(item.base_hours)} hr per {s_cfg['base_qty']} {s_cfg['unit']}")
                detail = (f"{calc.fmt(item.base_hours)} h base  ×  {item.multiplier}   ·   "
                          f"{round(share * 100)}% of total")
            else:
                detail = f"Fixed effort for {item.level}   ·   {round(share * 100)}% of total"
            self.rows[item.key].set_values(item.level, detail, item.final_hours, share)

        self._render_guide()
        n = len(result.items)
        self.hours_card.set_subtitle(f"{n} activit{'y' if n == 1 else 'ies'} combined")
        self.hours_card.animate_to(result.total_hours)
        self.days_card.animate_to(result.total_days)

    def reset(self):
        for k, var in self.band_vars.items():
            var.set(calc.get_bands(self.key, k)[0])
        for k, var in self.level_vars.items():
            var.set(calc.get_levels(self.key, k)[0])
        self.recalculate()
        self._toast(f"{self.cfg['tab']} reset to defaults")

    def share_estimate(self):
        if not self.result:
            return
        details = ask_export_details(self.winfo_toplevel(), self.cfg["tab"],
                                     self.result.total_hours, self.result.total_days)
        if not details:
            return
        if details["action"] == "copy":
            self._copy_for_email(details)
        else:
            self._download_excel(details)

    def _copy_for_email(self, details):
        try:
            rich = email_share.copy_for_email(self.winfo_toplevel(), self.result, details)
        except Exception as exc:                       # clipboard problems
            messagebox.showerror("Copy failed", str(exc))
            return
        if rich:
            self._toast("✓ Table copied - open Outlook and press Ctrl+V")
        else:
            self._toast("✓ Copied as text - paste with Ctrl+V")

    def _download_excel(self, details):
        safe = "".join(ch for ch in details["entity_name"] if ch.isalnum() or ch in " -_").strip()
        path = filedialog.asksaveasfilename(
            title="Save Excel estimate", defaultextension=".xlsx",
            initialfile=f"{safe or 'estimate'}_{self.key}_estimate.xlsx",
            filetypes=[("Excel workbook", "*.xlsx")])
        if not path:
            return
        try:
            exporter.export_excel(self.result, details["entity_name"], details["delivery_date"],
                                  details["resources"], details["assumptions"], path)
        except exporter.ExportError as exc:
            messagebox.showerror("openpyxl not installed", str(exc))
            return
        except OSError as exc:
            messagebox.showerror("Export failed", f"{exc}\n\nIs the file open in Excel? Close it and retry.")
            return
        self._toast("✓ Excel exported")


# ======================================================================
# Application shell: header + tabs + pages + footer
# ======================================================================
class EstimatorApp(tk.Frame):
    def __init__(self, master: tk.Tk):
        super().__init__(master, bg=GREY_BG)
        self.master = master
        self.pages = {}
        self.current = None
        self._toast_job = None

        self._configure_window()
        self._build_header()
        self._build_footer()
        self._build_pages()
        self._bind_shortcuts()
        self.select_tab(next(iter(ESTIMATORS)))

    def _configure_window(self):
        self.master.title(f"{APP_TITLE} | {COMPANY_NAME}")
        self.master.geometry("1200x780")
        self.master.minsize(1100, 740)
        self.master.configure(bg=GREY_BG)
        self.pack(fill="both", expand=True)

    # ------------------------------------------------------------ header
    def _build_header(self):
        header = tk.Frame(self, bg=PURPLE, padx=28)
        header.pack(fill="x")

        top = tk.Frame(header, bg=PURPLE)
        top.pack(fill="x", pady=(14, 0))
        tk.Label(top, text=COMPANY_NAME.upper(), font=font(9, "bold"),
                 fg=TAB_IDLE_FG, bg=PURPLE).pack(anchor="w")
        tk.Label(top, text=APP_TITLE, font=font(20, "bold"), fg=WHITE, bg=PURPLE).pack(anchor="w")

        tabrow = tk.Frame(header, bg=PURPLE)
        tabrow.pack(fill="x", pady=(12, 0))
        tabbar = tk.Frame(tabrow, bg=PURPLE)
        tabbar.pack(side="left")
        self.note_var = tk.StringVar()
        tk.Label(tabrow, textvariable=self.note_var, font=font(9, "bold"),
                 fg=TAB_IDLE_FG, bg=PURPLE).pack(side="right", pady=(0, 6))

        self.tab_buttons = {}
        for key, cfg in ESTIMATORS.items():
            btn = tk.Label(tabbar, text=cfg["tab"], font=font(10, "bold"),
                           padx=22, pady=9, cursor="hand2")
            btn.pack(side="left", padx=(0, 4))
            btn.bind("<Button-1>", lambda _e, k=key: self.select_tab(k))
            btn.bind("<Enter>", lambda _e, k=key: self._tab_hover(k, True))
            btn.bind("<Leave>", lambda _e, k=key: self._tab_hover(k, False))
            self.tab_buttons[key] = btn

    def _render_tabs(self):
        for key, btn in self.tab_buttons.items():
            if key == self.current:
                btn.configure(bg=GREY_BG, fg=PURPLE)
            else:
                btn.configure(bg=PURPLE, fg=TAB_IDLE_FG)

    def _tab_hover(self, key, entering):
        if key != self.current:
            self.tab_buttons[key].configure(bg=PURPLE_DARK if entering else PURPLE,
                                            fg=WHITE if entering else TAB_IDLE_FG)

    # ------------------------------------------------------------- pages
    def _build_pages(self):
        container = tk.Frame(self, bg=GREY_BG)
        container.pack(fill="both", expand=True)
        container.rowconfigure(0, weight=1)
        container.columnconfigure(0, weight=1)
        for key in ESTIMATORS:
            page = EstimatorPage(container, key, self.show_toast)
            page.grid(row=0, column=0, sticky="nsew")
            self.pages[key] = page

    def select_tab(self, key):
        self.current = key
        self.pages[key].tkraise()
        note = ESTIMATORS[key].get("sample_note")
        self.note_var.set(f"ⓘ  {note}" if note else "")
        self._render_tabs()

    # ------------------------------------------------------------ footer
    def _build_footer(self):
        footer = tk.Frame(self, bg=GREY_BG, padx=28, pady=8)
        footer.pack(fill="x", side="bottom")
        tk.Label(footer, text=f"{COMPANY_NAME}  ·  Internal effort estimation tool   |   "
                              f"Ctrl+1/2 Switch tab   Ctrl+R Reset   Ctrl+S Share",
                 font=font(8), fg=GREY_TEXT, bg=GREY_BG).pack(side="left")
        self._toast = tk.Label(footer, text="", font=font(9, "bold"), fg=PURPLE,
                               bg=GREY_BG, padx=12, pady=4)
        self._toast.pack(side="right")

    def show_toast(self, message, ms=2500):
        if self._toast_job:
            self.after_cancel(self._toast_job)
        self._toast.configure(text=message, bg=PURPLE_LIGHT)
        self._toast_job = self.after(ms, lambda: self._toast.configure(text="", bg=GREY_BG))

    def _bind_shortcuts(self):
        for i, key in enumerate(ESTIMATORS, start=1):
            self.master.bind(f"<Control-Key-{i}>", lambda _e, k=key: self.select_tab(k))
        self.master.bind("<Control-r>", lambda _e: self.pages[self.current].reset())
        self.master.bind("<Control-s>", lambda _e: self.pages[self.current].share_estimate())
