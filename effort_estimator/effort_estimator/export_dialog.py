"""
export_dialog.py
----------------
Modal form shown when "Share Estimate" is clicked:
  Engagement / Entity name, tentative delivery date, CI resources (search, max 3),
  key assumptions.  Returns the filled details (+ action "copy" / "excel")
  or None if cancelled.
"""

import math
import tkinter as tk
from tkinter import ttk
from datetime import date, datetime, timedelta

from calculator import fmt
from config import CI_RESOURCES, DEFAULT_ASSUMPTION, MAX_RESOURCES
from theme import (GREY_BG, GREY_BORDER, GREY_DARK, GREY_TEXT, PURPLE, PURPLE_SOFT,
                   PURPLE_LIGHT, WHITE, font)
from widgets import DatePicker, HoverButton

DATE_FORMATS = ("%d-%m-%Y", "%d/%m/%Y", "%d-%b-%Y", "%d %b %Y")


def add_working_days(start: date, days: int) -> date:
    current = start
    while days > 0:
        current += timedelta(days=1)
        if current.weekday() < 5:          # Mon-Fri
            days -= 1
    return current


def parse_date(text: str):
    for fmt_ in DATE_FORMATS:
        try:
            return datetime.strptime(text.strip(), fmt_).date()
        except ValueError:
            continue
    return None


class ExportDialog(tk.Toplevel):
    def __init__(self, master, tab_name: str, total_hours: float, total_days: float):
        super().__init__(master)
        self.result = None
        self.selected = []                                  # chosen resource names

        self.title("Share Estimate")
        self.configure(bg=GREY_BG)
        self.resizable(False, False)
        self.transient(master)

        suggested = add_working_days(date.today(), max(1, math.ceil(total_days)))
        self.name_var = tk.StringVar()
        self.date_var = tk.StringVar(value=suggested.strftime("%d-%m-%Y"))
        self.search_var = tk.StringVar()
        self.error_var = tk.StringVar()
        self.count_var = tk.StringVar()

        self._build(tab_name, total_hours, suggested)
        self._render_resources()

        self.bind("<Escape>", self._on_escape)
        self.bind("<Return>", self._on_return)
        self.update_idletasks()
        x = master.winfo_rootx() + (master.winfo_width() - self.winfo_width()) // 2
        y = master.winfo_rooty() + (master.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{max(x, 0)}+{max(y, 0)}")
        self.grab_set()
        self.name_entry.focus_set()

    # ------------------------------------------------------------ helpers
    def _entry(self, parent, var, width=34):
        return tk.Entry(parent, textvariable=var, font=font(10), width=width, relief="flat",
                        bg=WHITE, fg=GREY_DARK, insertbackground=PURPLE,
                        highlightthickness=1, highlightbackground=GREY_BORDER,
                        highlightcolor=PURPLE)

    def _field_label(self, parent, text, hint=None):
        tk.Label(parent, text=text, font=font(10, "bold"), fg=GREY_DARK,
                 bg=WHITE).pack(anchor="w", pady=(10, 2))
        if hint:
            tk.Label(parent, text=hint, font=font(8), fg=GREY_TEXT, bg=WHITE).pack(anchor="w")

    # ------------------------------------------------------------ layout
    def _build(self, tab_name, total_hours, suggested):
        header = tk.Frame(self, bg=PURPLE, padx=22, pady=14)
        header.pack(fill="x")
        tk.Label(header, text="SHARE ESTIMATE", font=font(9, "bold"),
                 fg="#D9CCEB", bg=PURPLE).pack(anchor="w")
        tk.Label(header, text=f"{tab_name}  ·  Estimated {fmt(total_hours)} hours",
                 font=font(14, "bold"), fg=WHITE, bg=PURPLE).pack(anchor="w")

        body = tk.Frame(self, bg=WHITE, padx=22, pady=8)
        body.pack(fill="both", expand=True)
        left = tk.Frame(body, bg=WHITE)
        left.grid(row=0, column=0, sticky="nw", padx=(0, 24))
        right = tk.Frame(body, bg=WHITE)
        right.grid(row=0, column=1, sticky="nw")

        # left column
        self._field_label(left, "Engagement / Entity Name *")
        self.name_entry = self._entry(left, self.name_var)
        self.name_entry.pack(anchor="w", ipady=5)

        self._field_label(left, "Tentative delivery date *",
                          f"Click to pick  ·  suggested from estimate: {suggested.strftime('%d-%b-%Y')}")
        self.date_picker = DatePicker(left, self.date_var, width=27)
        self.date_picker.pack(anchor="w", pady=(3, 0))

        self._field_label(left, "Key assumptions, data dependencies or risks")
        self.assump_text = tk.Text(left, font=font(10), width=34, height=6, wrap="word",
                                   relief="flat", bg=WHITE, fg=GREY_DARK,
                                   highlightthickness=1, highlightbackground=GREY_BORDER,
                                   highlightcolor=PURPLE, padx=6, pady=4)
        self.assump_text.insert("1.0", DEFAULT_ASSUMPTION)
        self.assump_text.pack(anchor="w")

        # right column: resources
        top = tk.Frame(right, bg=WHITE)
        top.pack(fill="x", pady=(10, 2))
        tk.Label(top, text="Assigned CI resource *", font=font(10, "bold"),
                 fg=GREY_DARK, bg=WHITE).pack(side="left")
        tk.Label(top, textvariable=self.count_var, font=font(9, "bold"),
                 fg=PURPLE, bg=PURPLE_LIGHT, padx=8).pack(side="right")

        search = self._entry(right, self.search_var, width=30)
        search.pack(fill="x", ipady=5, pady=(4, 6))

        self.chips = tk.Frame(right, bg=WHITE)
        self.chips.pack(fill="x")

        box = tk.Frame(right, bg=GREY_BORDER, padx=1, pady=1)
        box.pack(fill="x", pady=(6, 0))
        self._build_scroll_list(box)

        self._placeholder(search, "Search name...")
        self.search_var.trace_add("write", lambda *_: self._render_resources())

        # footer
        foot = tk.Frame(self, bg=GREY_BG, padx=22, pady=12)
        foot.pack(fill="x")
        tk.Label(foot, textvariable=self.error_var, font=font(9, "bold"),
                 fg="#B3261E", bg=GREY_BG).pack(side="left")
        HoverButton(foot, "Copy for Email", lambda: self._submit("copy"), "primary").pack(side="right")
        HoverButton(foot, "Download Excel", lambda: self._submit("excel"), "secondary").pack(side="right", padx=10)
        HoverButton(foot, "Cancel", self.destroy, "secondary").pack(side="right")

    def _build_scroll_list(self, box):
        """Scrollable resource list (scrollbar + mouse wheel)."""
        holder = tk.Frame(box, bg=WHITE)
        holder.pack(fill="both")
        self.list_canvas = tk.Canvas(holder, bg=WHITE, highlightthickness=0,
                                     width=270, height=200)
        self.list_canvas.pack(side="left", fill="both", expand=True)

        style = ttk.Style(self)
        style.configure("GT.Vertical.TScrollbar", troughcolor="#F2F2F5", background=PURPLE_SOFT,
                        bordercolor=WHITE, lightcolor=PURPLE_SOFT, darkcolor=PURPLE_SOFT,
                        arrowcolor=PURPLE, gripcount=0)
        style.map("GT.Vertical.TScrollbar", background=[("active", PURPLE), ("pressed", PURPLE)])
        bar = ttk.Scrollbar(holder, orient="vertical", command=self.list_canvas.yview,
                            style="GT.Vertical.TScrollbar")
        bar.pack(side="right", fill="y")
        self.list_canvas.configure(yscrollcommand=bar.set)

        self.list_frame = tk.Frame(self.list_canvas, bg=WHITE)
        self._list_window = self.list_canvas.create_window((0, 0), window=self.list_frame, anchor="nw")
        self.list_frame.bind("<Configure>", lambda _e: self.list_canvas.configure(
            scrollregion=self.list_canvas.bbox("all")))
        self.list_canvas.bind("<Configure>", lambda e: self.list_canvas.itemconfigure(
            self._list_window, width=e.width))

        # mouse wheel only while the pointer is over the list
        self.list_canvas.bind("<Enter>", lambda _e: self._wheel(True))
        self.list_canvas.bind("<Leave>", lambda _e: self._wheel(False))

    def _wheel(self, active):
        if active:
            self.bind_all("<MouseWheel>", self._on_wheel)                      # Windows / macOS
            self.bind_all("<Button-4>", lambda _e: self.list_canvas.yview_scroll(-1, "units"))
            self.bind_all("<Button-5>", lambda _e: self.list_canvas.yview_scroll(1, "units"))
        else:
            for seq in ("<MouseWheel>", "<Button-4>", "<Button-5>"):
                self.unbind_all(seq)

    def _on_wheel(self, event):
        step = -1 if event.delta > 0 else 1
        self.list_canvas.yview_scroll(step, "units")

    def destroy(self):
        self._wheel(False)
        super().destroy()

    def _placeholder(self, entry, text):
        """Grey hint text inside the search box."""
        def show(_e=None):
            if not self.search_var.get():
                entry.configure(fg=GREY_TEXT)
                entry.insert(0, text)
                self._ph_active = True

        def hide(_e=None):
            if getattr(self, "_ph_active", False):
                self._ph_active = False
                entry.delete(0, "end")
                entry.configure(fg=GREY_DARK)

        self._ph_text = text
        entry.bind("<FocusIn>", hide)
        entry.bind("<FocusOut>", show)
        show()

    def _query(self):
        q = self.search_var.get()
        if getattr(self, "_ph_active", False) or q == getattr(self, "_ph_text", ""):
            return ""
        return q.strip().lower()

    # --------------------------------------------------------- resources
    def _render_resources(self):
        for w in self.list_frame.winfo_children():
            w.destroy()
        if hasattr(self, "list_canvas"):
            self.list_canvas.yview_moveto(0)
        q = self._query()
        names = [n for n in CI_RESOURCES if q in n.lower()]
        full = len(self.selected) >= MAX_RESOURCES

        if not names:
            tk.Label(self.list_frame, text="No matching name", font=font(9),
                     fg=GREY_TEXT, bg=WHITE).pack(pady=12)
        for name in names:
            chosen = name in self.selected
            disabled = full and not chosen
            bg = PURPLE_LIGHT if chosen else WHITE
            fg = PURPLE if chosen else ("#B5B5BF" if disabled else GREY_DARK)
            row = tk.Label(self.list_frame, text=f"{'☑' if chosen else '☐'}   {name}",
                           font=font(10, "bold" if chosen else "normal"), bg=bg, fg=fg,
                           anchor="w", padx=10, pady=3,
                           cursor="arrow" if disabled else "hand2")
            row.pack(fill="x")
            if not disabled:
                row.bind("<Button-1>", lambda _e, n=name: self._toggle(n))
                if not chosen:
                    row.bind("<Enter>", lambda e: e.widget.configure(bg="#F6F3FA"))
                    row.bind("<Leave>", lambda e: e.widget.configure(bg=WHITE))

        # chips for selected names
        for w in self.chips.winfo_children():
            w.destroy()
        for name in self.selected:
            chip = tk.Label(self.chips, text=f"{name}  ✕", font=font(9, "bold"), fg=WHITE,
                            bg=PURPLE, padx=8, pady=2, cursor="hand2")
            chip.pack(side="left", padx=(0, 5), pady=2)
            chip.bind("<Button-1>", lambda _e, n=name: self._toggle(n))
        self.count_var.set(f"{len(self.selected)} / {MAX_RESOURCES}")

    def _toggle(self, name):
        if name in self.selected:
            self.selected.remove(name)
        elif len(self.selected) < MAX_RESOURCES:
            self.selected.append(name)
        self.error_var.set("")
        self._render_resources()

    # ------------------------------------------------------------ submit
    def _on_escape(self, _event):
        if getattr(self, "date_picker", None) and self.date_picker._popup:
            self.date_picker.close()
            return
        self.destroy()

    def _on_return(self, event):
        if not isinstance(event.widget, tk.Text):
            self._submit("copy")

    def _submit(self, action="copy"):
        name = self.name_var.get().strip()
        delivery = parse_date(self.date_var.get())
        if not name:
            self.error_var.set("Please enter the engagement / entity name")
            return
        if delivery is None:
            self.error_var.set("Please select the delivery date")
            return
        if not self.selected:
            self.error_var.set("Select at least one CI resource")
            return
        self.result = {
            "action": action,
            "entity_name": name,
            "delivery_date": delivery,
            "resources": list(self.selected),
            "assumptions": self.assump_text.get("1.0", "end").strip(),
        }
        self.destroy()


def ask_export_details(master, tab_name, total_hours, total_days):
    dialog = ExportDialog(master, tab_name, total_hours, total_days)
    master.wait_window(dialog)
    return dialog.result
