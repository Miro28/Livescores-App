"""Reusable widget components: StatBar and MatchCard."""
import customtkinter as ctk

from theme import COLORS


class StatBar(ctk.CTkFrame):
    """A two-sided horizontal bar showing comparison between two team values."""

    def __init__(self, parent, label, left_val, right_val, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)

        try:
            l = float(left_val)
            r = float(right_val)
        except (TypeError, ValueError):
            l = r = 0
        total = l + r if (l + r) > 0 else 1
        l_pct = l / total
        r_pct = r / total

        # Top row: left value | label | right value
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x")
        ctk.CTkLabel(top, text=str(left_val), font=("Inter", 13, "bold"),
                     text_color=COLORS["text"], width=40, anchor="w").pack(side="left")
        ctk.CTkLabel(top, text=label, font=("Inter", 12),
                     text_color=COLORS["text_muted"]).pack(side="left", expand=True)
        ctk.CTkLabel(top, text=str(right_val), font=("Inter", 13, "bold"),
                     text_color=COLORS["text"], width=40, anchor="e").pack(side="right")

        # Bar
        bar_container = ctk.CTkFrame(self, fg_color=COLORS["bg_alt"], height=6, corner_radius=3)
        bar_container.pack(fill="x", pady=(4, 8))
        bar_container.pack_propagate(False)

        inner = ctk.CTkFrame(bar_container, fg_color="transparent")
        inner.pack(fill="both", expand=True)

        if l_pct > 0:
            left_bar = ctk.CTkFrame(inner, fg_color=COLORS["accent"], corner_radius=3)
            left_bar.place(relx=0, rely=0, relwidth=l_pct, relheight=1)
        if r_pct > 0:
            right_bar = ctk.CTkFrame(inner, fg_color=COLORS["blue"], corner_radius=3)
            right_bar.place(relx=l_pct, rely=0, relwidth=r_pct, relheight=1)


class MatchCard(ctk.CTkFrame):
    """A clickable card representing a single match."""

    def __init__(self, parent, event, on_click, **kwargs):
        super().__init__(parent, fg_color=COLORS["card"], corner_radius=10,
                         border_width=1, border_color=COLORS["border"], **kwargs)

        self.event = event
        self.on_click = on_click
        self._normal = COLORS["card"]
        self._hover = COLORS["card_hover"]

        home = event.get("T1", [{}])[0].get("Nm", "Home")
        away = event.get("T2", [{}])[0].get("Nm", "Away")
        score1 = event.get("Tr1", "-")
        score2 = event.get("Tr2", "-")
        status = event.get("Eps", "")
        is_live = (status not in ("FT", "NS", "AET", "Postp.", "Canc.", "Abnd.")
                   and status != ""
                   and not status.startswith("20"))

        # Status pill (top-left)
        status_row = ctk.CTkFrame(self, fg_color="transparent")
        status_row.pack(fill="x", padx=14, pady=(10, 0))

        if is_live:
            pill = ctk.CTkFrame(status_row, fg_color=COLORS["live"], corner_radius=4, height=20)
            pill.pack(side="left")
            ctk.CTkLabel(pill, text=f"  ● LIVE  {status}  ", font=("Inter", 10, "bold"),
                         text_color="#FFFFFF").pack(padx=2)
        else:
            pill_color = COLORS["bg_alt"]
            text_color = COLORS["text_muted"]
            if status == "FT":
                text_color = COLORS["text"]
            ctk.CTkLabel(status_row, text=status or "—", font=("Inter", 11, "bold"),
                         text_color=text_color, fg_color=pill_color, corner_radius=4,
                         padx=8, pady=2).pack(side="left")

        # Main row
        main = ctk.CTkFrame(self, fg_color="transparent")
        main.pack(fill="x", padx=14, pady=(8, 12))

        ctk.CTkLabel(main, text=home, font=("Inter", 15, "bold"),
                     text_color=COLORS["text"], anchor="w"
                     ).pack(side="left", expand=True, fill="x")

        score_text = f"{score1}  :  {score2}" if score1 != "" else "vs"
        ctk.CTkLabel(main, text=score_text, font=("Inter", 18, "bold"),
                     text_color=COLORS["accent"] if is_live else COLORS["text"],
                     width=90).pack(side="left", padx=12)

        ctk.CTkLabel(main, text=away, font=("Inter", 15, "bold"),
                     text_color=COLORS["text"], anchor="e"
                     ).pack(side="left", expand=True, fill="x")

        self._bind_recursive(self)

    def _bind_recursive(self, widget):
        widget.bind("<Button-1>", lambda e: self.on_click(self.event))
        widget.bind("<Enter>", self._on_enter)
        widget.bind("<Leave>", self._on_leave)
        for child in widget.winfo_children():
            self._bind_recursive(child)

    def _on_enter(self, _):
        self.configure(fg_color=self._hover, border_color=COLORS["accent"])

    def _on_leave(self, _):
        self.configure(fg_color=self._normal, border_color=COLORS["border"])
