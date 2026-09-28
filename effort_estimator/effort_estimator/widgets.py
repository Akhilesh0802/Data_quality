"""
widgets.py
----------
Reusable modern widgets built on plain Tkinter (no external libraries):
Card, HoverButton, Dropdown, SegmentedControl, StatCard, BreakdownRow.
"""

import tkinter as tk

from calculator import fmt
from theme import (GREY_BORDER, GREY_DARK, GREY_TEXT, GREY_TRACK, PURPLE,
                   PURPLE_DARK, PURPLE_LIGHT, PURPLE_MID, PURPLE_SOFT, WHITE, font)


class Card(tk.Frame):
    """White card with thin grey border, title and purple accent underline."""

    def __init__(self, master, title=None):
        super().__init__(master, bg=GREY_BORDER, padx=1, pady=1)
        body = tk.Frame(self, bg=WHITE, padx=20, pady=12)
        body.pack(fill="both", expand=True)
        if title:
            tk.Label(body, text=title.upper(), font=font(9, "bold"),
                     fg=PURPLE, bg=WHITE).pack(anchor="w")
            tk.Frame(body, bg=PURPLE, height=3, width=32).pack(anchor="w", pady=(4, 8))
        self.content = tk.Frame(body, bg=WHITE)
        self.content.pack(fill="both", expand=True)


class HoverButton(tk.Label):
    """Flat button with hover / press colours (works the same on every OS)."""

    VARIANTS = {
        "primary":   (PURPLE, PURPLE_DARK, WHITE),
        "secondary": (PURPLE_LIGHT, PURPLE_SOFT, PURPLE),
    }

    def __init__(self, master, text, command, variant="primary"):
        self._bg, self._hover, fg = self.VARIANTS[variant]
        super().__init__(master, text=text, bg=self._bg, fg=fg, font=font(10, "bold"),
                         padx=18, pady=9, cursor="hand2")
        self._command = command
        self.bind("<Enter>", lambda _e: self.configure(bg=self._hover))
        self.bind("<Leave>", lambda _e: self.configure(bg=self._bg))
        self.bind("<ButtonPress-1>", lambda _e: self.configure(bg=PURPLE_DARK if variant == "primary" else PURPLE_SOFT))
        self.bind("<ButtonRelease-1>", self._release)

    def _release(self, event):
        self.configure(bg=self._hover)
        # fire only if mouse released over the button
        if 0 <= event.x <= self.winfo_width() and 0 <= event.y <= self.winfo_height():
            self._command()


class SegmentedControl(tk.Frame):
    """Pill-style option selector - all options visible, one click to choose."""

    def __init__(self, master, options, variable, command=None):
        super().__init__(master, bg=GREY_BORDER, padx=1, pady=1)
        self.variable = variable
        self.command = command
        self._buttons = {}
        for i, option in enumerate(options):
            btn = tk.Label(self, text=option, font=font(9, "bold"), pady=5, cursor="hand2")
            btn.grid(row=0, column=i, sticky="nsew", padx=(0 if i == 0 else 1, 0))
            self.columnconfigure(i, weight=1, uniform="seg")
            btn.bind("<Button-1>", lambda _e, o=option: self.select(o))
            btn.bind("<Enter>", lambda _e, o=option: self._hover(o, True))
            btn.bind("<Leave>", lambda _e, o=option: self._hover(o, False))
            self._buttons[option] = btn
        variable.trace_add("write", lambda *_: self._render())
        self._render()

    def select(self, option):
        if option != self.variable.get():
            self.variable.set(option)
            if self.command:
                self.command()

    def _render(self):
        current = self.variable.get()
        for option, btn in self._buttons.items():
            if option == current:
                btn.configure(bg=PURPLE, fg=WHITE)
            else:
                btn.configure(bg=WHITE, fg=GREY_TEXT)

    def _hover(self, option, entering):
        if option != self.variable.get():
            self._buttons[option].configure(bg=PURPLE_LIGHT if entering else WHITE,
                                            fg=PURPLE if entering else GREY_TEXT)


class StatCard(tk.Frame):
    """Big coloured number tile with count-up animation."""

    def __init__(self, master, caption, unit, bg):
        super().__init__(master, bg=bg, padx=22, pady=12)
        tk.Label(self, text=caption.upper(), font=font(9, "bold"),
                 fg="#D9CCEB" if bg == PURPLE else "#C9C9D2", bg=bg).pack(anchor="w")
        row = tk.Frame(self, bg=bg)
        row.pack(anchor="w", pady=(4, 0))
        self._value = tk.Label(row, text="0", font=font(26, "bold"), fg=WHITE, bg=bg)
        self._value.pack(side="left")
        tk.Label(row, text=unit, font=font(12), fg=WHITE, bg=bg).pack(side="left", anchor="s", pady=(0, 8), padx=(6, 0))
        self._sub = tk.Label(self, text="", font=font(9), fg="#D9CCEB" if bg == PURPLE else "#C9C9D2", bg=bg)
        self._sub.pack(anchor="w")
        self._current = 0.0
        self._job = None

    def set_subtitle(self, text):
        self._sub.configure(text=text)

    def animate_to(self, target, steps=14, delay=16):
        if self._job:
            self.after_cancel(self._job)
        start = self._current

        def step(i):
            value = start + (target - start) * (1 - (1 - i / steps) ** 3)  # ease-out
            self._value.configure(text=fmt(value))
            if i < steps:
                self._job = self.after(delay, step, i + 1)
            else:
                self._current = target
                self._value.configure(text=fmt(target))
                self._job = None

        step(1)


class BreakdownRow(tk.Frame):
    """One line of the breakdown: title, level pill, formula, hours and share bar."""

    def __init__(self, master, title):
        super().__init__(master, bg=WHITE)
        top = tk.Frame(self, bg=WHITE)
        top.pack(fill="x")
        tk.Label(top, text=title, font=font(10, "bold"), fg=GREY_DARK, bg=WHITE).pack(side="left")
        self._level = tk.Label(top, font=font(8, "bold"), fg=PURPLE, bg=PURPLE_LIGHT, padx=8, pady=1)
        self._level.pack(side="left", padx=(8, 0))
        self._hours = tk.Label(top, font=font(11, "bold"), fg=PURPLE, bg=WHITE)
        self._hours.pack(side="right")

        self._detail = tk.Label(self, font=font(9), fg=GREY_TEXT, bg=WHITE)
        self._detail.pack(anchor="w", pady=(1, 0))

        self._canvas = tk.Canvas(self, height=10, bg=WHITE, highlightthickness=0)
        self._canvas.pack(fill="x", pady=(3, 0))
        self._canvas.bind("<Configure>", lambda _e: self._draw())
        self._frac = 0.0
        self._job = None

    def set_values(self, level, detail, hours, share):
        self._level.configure(text=level)
        self._detail.configure(text=detail)
        self._hours.configure(text=f"{fmt(hours)} h")
        self._animate(share)

    def _animate(self, target, steps=14, delay=16):
        if self._job:
            self.after_cancel(self._job)
        start = self._frac

        def step(i):
            self._frac = start + (target - start) * (1 - (1 - i / steps) ** 3)
            self._draw()
            if i < steps:
                self._job = self.after(delay, step, i + 1)
            else:
                self._job = None

        step(1)

    def _draw(self):
        c = self._canvas
        w = c.winfo_width()
        c.delete("all")
        if w <= 10:
            return
        c.create_line(5, 5, w - 5, 5, width=8, capstyle="round", fill=GREY_TRACK)
        if self._frac > 0.001:
            c.create_line(5, 5, 5 + (w - 10) * self._frac, 5, width=8,
                          capstyle="round", fill=PURPLE)


class Dropdown(tk.Frame):
    """
    Custom dropdown (replaces ttk.Combobox).
    Selected value is always clearly visible, looks the same on every OS.
    """

    def __init__(self, master, options, variable, command=None, width=10):
        super().__init__(master, bg=GREY_BORDER, padx=1, pady=1, cursor="hand2")
        self.variable = variable
        self.command = command

        inner = tk.Frame(self, bg=WHITE)
        inner.pack(fill="both", expand=True)
        self._text = tk.Label(inner, textvariable=variable, font=font(10, "bold"), fg=GREY_DARK,
                              bg=WHITE, anchor="w", width=width, padx=10, pady=5)
        self._text.pack(side="left", fill="x", expand=True)
        self._arrow = tk.Label(inner, text="▾", font=font(12, "bold"), fg=PURPLE, bg=WHITE, padx=8)
        self._arrow.pack(side="right")

        self._menu = tk.Menu(self, tearoff=0, bg=WHITE, fg=GREY_DARK, font=font(10),
                             activebackground=PURPLE, activeforeground=WHITE,
                             bd=0, relief="flat")
        for option in options:
            self._menu.add_command(label=f"  {option}  ", command=lambda o=option: self._choose(o))

        for widget in (self, inner, self._text, self._arrow):
            widget.bind("<Button-1>", self._open)
            widget.bind("<Enter>", lambda _e: self.configure(bg=PURPLE_MID))
            widget.bind("<Leave>", lambda _e: self.configure(bg=GREY_BORDER))

    def _open(self, _event=None):
        x = self.winfo_rootx()
        y = self.winfo_rooty() + self.winfo_height()
        try:
            self._menu.tk_popup(x, y)
        finally:
            self._menu.grab_release()

    def _choose(self, option):
        self.variable.set(option)
        self.configure(bg=PURPLE)                          # quick flash to confirm
        self.after(250, lambda: self.configure(bg=GREY_BORDER))
        if self.command:
            self.command()


class DatePicker(tk.Frame):
    """
    Date field with a pop-up calendar (pure Tkinter, no extra library).
    `variable` holds the date as DD-MM-YYYY. Past dates are disabled.
    """

    FMT = "%d-%m-%Y"

    def __init__(self, master, variable, min_date=None, width=24):
        import datetime as _dt
        super().__init__(master, bg=GREY_BORDER, padx=1, pady=1, cursor="hand2")
        self._dt = _dt
        self.variable = variable
        self.min_date = min_date or _dt.date.today()
        self._popup = None

        inner = tk.Frame(self, bg=WHITE)
        inner.pack(fill="both", expand=True)
        self._display = tk.StringVar()
        self._text = tk.Label(inner, textvariable=self._display, font=font(10, "bold"),
                              fg=GREY_DARK, bg=WHITE, anchor="w", width=width, padx=10, pady=5)
        self._text.pack(side="left", fill="x", expand=True)
        self._icon = tk.Label(inner, text="📅", font=font(11), fg=PURPLE, bg=WHITE, padx=8)
        self._icon.pack(side="right")

        for w in (self, inner, self._text, self._icon):
            w.bind("<Button-1>", lambda _e: self.open())
            w.bind("<Enter>", lambda _e: self.configure(bg=PURPLE_MID))
            w.bind("<Leave>", lambda _e: self.configure(bg=GREY_BORDER))

        variable.trace_add("write", lambda *_: self._refresh_display())
        self._refresh_display()

    # -------------------------------------------------------------- value
    def get_date(self):
        try:
            return self._dt.datetime.strptime(self.variable.get(), self.FMT).date()
        except ValueError:
            return None

    def _refresh_display(self):
        d = self.get_date()
        self._display.set(d.strftime("%a, %d %b %Y") if d else "Select date")

    # -------------------------------------------------------------- popup
    # The calendar is drawn INSIDE the same window (place() overlay) instead of a
    # separate pop-up window - separate windows + modal grabs are unreliable on Windows.
    def open(self):
        if self._popup:
            self.close()
            return
        selected = self.get_date() or self.min_date
        self._view = selected.replace(day=1)

        top = self.winfo_toplevel()
        self._owner = top
        popup = tk.Frame(top, bg=GREY_BORDER, padx=1, pady=1)
        self._popup = popup
        self._body = tk.Frame(popup, bg=WHITE)
        self._body.pack(fill="both", expand=True)
        self._render()

        top.update_idletasks()
        pw, ph = popup.winfo_reqwidth(), popup.winfo_reqheight()
        fx = self.winfo_rootx() - top.winfo_rootx()
        fy = self.winfo_rooty() - top.winfo_rooty()
        W, H = top.winfo_width(), top.winfo_height()
        if fy + self.winfo_height() + 2 + ph <= H - 4:          # fits below the field
            x, y = fx, fy + self.winfo_height() + 2
        elif fx + self.winfo_width() + 8 + pw <= W - 4:        # else open to the right
            x, y = fx + self.winfo_width() + 8, fy
        else:                                                  # else above the field
            x, y = fx, fy - ph - 2
        # keep the calendar fully inside the window
        x = max(4, min(x, W - pw - 4))
        y = max(4, min(y, H - ph - 4))
        popup.place(x=x, y=y)
        popup.lift()

        if not getattr(self, "_outside_bound", False):
            top.bind("<Button-1>", self._click_outside, add="+")
            top.bind("<Escape>", self._escape, add="+")
            self._outside_bound = True

    def close(self):
        if self._popup:
            self._popup.destroy()
            self._popup = None

    def _is_inside(self, widget, parent):
        return parent is not None and str(widget).startswith(str(parent))

    def _click_outside(self, event):
        if not self._popup:
            return
        if self._is_inside(event.widget, self._popup) or self._is_inside(event.widget, self):
            return
        self.close()

    def _escape(self, _event):
        if self._popup:
            self.close()
            return "break"

    def _shift_month(self, delta):
        y, m = self._view.year, self._view.month + delta
        y, m = y + (m - 1) // 12, (m - 1) % 12 + 1
        self._view = self._view.replace(year=y, month=m)
        self._render()

    def _pick(self, day):
        self.variable.set(day.strftime(self.FMT))
        self.close()

    def _render(self):
        import calendar
        for w in self._body.winfo_children():
            w.destroy()
        today = self._dt.date.today()
        selected = self.get_date()
        view = self._view

        head = tk.Frame(self._body, bg=PURPLE, padx=6, pady=6)
        head.pack(fill="x")
        can_go_back = (view.year, view.month) > (self.min_date.year, self.min_date.month)
        prev_btn = tk.Label(head, text="‹", font=font(14, "bold"), bg=PURPLE,
                            fg=WHITE if can_go_back else PURPLE_MID, padx=8,
                            cursor="hand2" if can_go_back else "arrow")
        prev_btn.pack(side="left")
        if can_go_back:
            prev_btn.bind("<Button-1>", lambda _e: self._shift_month(-1))
        tk.Label(head, text=view.strftime("%B %Y"), font=font(11, "bold"),
                 bg=PURPLE, fg=WHITE).pack(side="left", expand=True)
        next_btn = tk.Label(head, text="›", font=font(14, "bold"), bg=PURPLE, fg=WHITE,
                            padx=8, cursor="hand2")
        next_btn.pack(side="right")
        next_btn.bind("<Button-1>", lambda _e: self._shift_month(1))

        grid = tk.Frame(self._body, bg=WHITE, padx=8, pady=6)
        grid.pack()
        for col, name in enumerate(("Mo", "Tu", "We", "Th", "Fr", "Sa", "Su")):
            tk.Label(grid, text=name, font=font(9, "bold"), width=4,
                     fg=PURPLE if col < 5 else GREY_TEXT, bg=WHITE).grid(row=0, column=col, pady=(0, 4))

        weeks = calendar.Calendar(firstweekday=0).monthdatescalendar(view.year, view.month)
        for r, week in enumerate(weeks, start=1):
            for c, day in enumerate(week):
                in_month = day.month == view.month
                disabled = day < self.min_date or not in_month
                is_sel = day == selected
                is_today = day == today
                if not in_month:
                    bg, fg = WHITE, WHITE
                elif is_sel:
                    bg, fg = PURPLE, WHITE
                elif is_today:
                    bg, fg = PURPLE_LIGHT, PURPLE
                else:
                    bg = WHITE
                    fg = "#C4C4CC" if disabled else (GREY_TEXT if c >= 5 else GREY_DARK)
                cell = tk.Label(grid, text=str(day.day) if in_month else "", width=4, pady=4,
                                font=font(9, "bold" if (is_sel or is_today) else "normal"),
                                bg=bg, fg=fg, cursor="arrow" if disabled else "hand2")
                cell.grid(row=r, column=c, padx=1, pady=1)
                if not disabled:
                    cell.bind("<Button-1>", lambda _e, d=day: self._pick(d))
                    if not is_sel:
                        cell.bind("<Enter>", lambda e: e.widget.configure(bg=PURPLE_SOFT))
                        cell.bind("<Leave>", lambda e, b=bg: e.widget.configure(bg=b))

        foot = tk.Frame(self._body, bg=WHITE, padx=8, pady=6)
        foot.pack(fill="x")
        t = tk.Label(foot, text="Today", font=font(9, "bold"), fg=PURPLE, bg=PURPLE_LIGHT,
                     padx=10, pady=2, cursor="hand2")
        t.pack(side="left")
        t.bind("<Button-1>", lambda _e: self._pick(today))
        x = tk.Label(foot, text="Close", font=font(9, "bold"), fg=GREY_TEXT, bg=WHITE,
                     padx=10, pady=2, cursor="hand2")
        x.pack(side="right")
        x.bind("<Button-1>", lambda _e: self.close())
