"""Themed calendar popup that replaces tkcalendar."""
import calendar
from datetime import datetime

import customtkinter as ctk

from theme import COLORS


class CalendarPopup(ctk.CTkToplevel):
    """Custom calendar popup matching the dark theme."""

    def __init__(self, parent, current_date, on_pick):
        super().__init__(parent)
        self.title("Pick a date")
        self.geometry("320x340")
        self.configure(fg_color=COLORS["bg_alt"])
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.current = datetime(current_date.year, current_date.month, 1)
        self.selected = current_date
        self.on_pick = on_pick

        self._build()

    def _build(self):
        # Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=14, pady=(14, 8))

        ctk.CTkButton(header, text="‹", width=32, height=32,
                      font=("Inter", 16, "bold"),
                      fg_color=COLORS["card"], hover_color=COLORS["card_hover"],
                      text_color=COLORS["text"], corner_radius=8,
                      command=self._prev_month).pack(side="left")

        self.month_label = ctk.CTkLabel(header, text="",
                                        font=("Inter", 14, "bold"),
                                        text_color=COLORS["text"])
        self.month_label.pack(side="left", expand=True)

        ctk.CTkButton(header, text="›", width=32, height=32,
                      font=("Inter", 16, "bold"),
                      fg_color=COLORS["card"], hover_color=COLORS["card_hover"],
                      text_color=COLORS["text"], corner_radius=8,
                      command=self._next_month).pack(side="right")

        # Day headers
        days_row = ctk.CTkFrame(self, fg_color="transparent")
        days_row.pack(fill="x", padx=14)
        for d in ("Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"):
            ctk.CTkLabel(days_row, text=d, font=("Inter", 11, "bold"),
                         text_color=COLORS["text_muted"], width=38).pack(side="left")

        # Grid
        self.grid_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.grid_frame.pack(padx=14, pady=8)

        # Today button
        ctk.CTkButton(self, text="Today", height=32,
                      fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
                      font=("Inter", 12, "bold"),
                      command=self._goto_today).pack(fill="x", padx=14, pady=(4, 14))

        self._render_grid()

    def _render_grid(self):
        for w in self.grid_frame.winfo_children():
            w.destroy()

        self.month_label.configure(text=self.current.strftime("%B %Y"))

        cal = calendar.Calendar(firstweekday=0)
        weeks = cal.monthdayscalendar(self.current.year, self.current.month)
        today = datetime.now().date()

        for week in weeks:
            row = ctk.CTkFrame(self.grid_frame, fg_color="transparent")
            row.pack()
            for day in week:
                if day == 0:
                    ctk.CTkLabel(row, text="", width=38, height=32
                                 ).pack(side="left", padx=1, pady=1)
                else:
                    d = datetime(self.current.year, self.current.month, day).date()
                    is_today = d == today
                    is_sel = d == self.selected

                    if is_sel:
                        fg = COLORS["accent"]; tc = "#FFFFFF"
                    elif is_today:
                        fg = COLORS["card"]; tc = COLORS["accent"]
                    else:
                        fg = "transparent"; tc = COLORS["text"]

                    btn = ctk.CTkButton(
                        row, text=str(day), width=38, height=32,
                        font=("Inter", 12, "bold" if is_sel or is_today else "normal"),
                        fg_color=fg, hover_color=COLORS["card_hover"],
                        text_color=tc, corner_radius=8,
                        command=lambda dd=d: self._pick(dd),
                    )
                    btn.pack(side="left", padx=1, pady=1)

    def _prev_month(self):
        m = self.current.month - 1
        y = self.current.year
        if m < 1:
            m = 12
            y -= 1
        self.current = datetime(y, m, 1)
        self._render_grid()

    def _next_month(self):
        m = self.current.month + 1
        y = self.current.year
        if m > 12:
            m = 1
            y += 1
        self.current = datetime(y, m, 1)
        self._render_grid()

    def _goto_today(self):
        self._pick(datetime.now().date())

    def _pick(self, d):
        self.selected = d
        self.on_pick(d)
        self.destroy()
