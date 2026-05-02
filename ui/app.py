"""Main application window."""
from datetime import datetime, timedelta
from tkinter import StringVar

import customtkinter as ctk

from theme import COLORS
from config import AUTO_REFRESH_MS
from api import (
    cache,
    fetch_live_matches,
    fetch_matches_by_date,
    fetch_statistics,
    fetch_lineups,
    run_async,
)
from .components import StatBar, MatchCard
from .calendar_popup import CalendarPopup


class VDMScoreApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("green")

        self.title("VDM Score")
        self.geometry("1280x820")
        self.minsize(1100, 700)
        self.configure(fg_color=COLORS["bg"])

        self.current_view = "live"        # "live" | "date" | "details"
        self.current_date = datetime.now().date()
        self.search_text = ""
        self.auto_refresh = False
        self.refresh_after_id = None
        self.last_matches_data = None     # latest dataset for filtering

        self._build_layout()
        self._show_live_matches()

    # ----- Layout -----
    def _build_layout(self):
        # Top bar
        topbar = ctk.CTkFrame(self, fg_color=COLORS["bg_alt"], height=64, corner_radius=0)
        topbar.pack(fill="x", side="top")
        topbar.pack_propagate(False)

        logo = ctk.CTkFrame(topbar, fg_color="transparent")
        logo.pack(side="left", padx=24)
        ctk.CTkLabel(logo, text="●", font=("Inter", 20, "bold"),
                     text_color=COLORS["accent"]).pack(side="left")
        ctk.CTkLabel(logo, text="VDM Score",
                     font=("Inter", 20, "bold"),
                     text_color=COLORS["text"]).pack(side="left", padx=(8, 0))

        # Search bar
        search_wrap = ctk.CTkFrame(topbar, fg_color=COLORS["card"], corner_radius=10, height=36)
        search_wrap.pack(side="left", padx=24, pady=14)
        ctk.CTkLabel(search_wrap, text="🔍", text_color=COLORS["text_muted"],
                     font=("Inter", 13)).pack(side="left", padx=(10, 4))
        self.search_var = StringVar()
        self.search_var.trace_add("write", self._on_search)
        ctk.CTkEntry(search_wrap, textvariable=self.search_var,
                     placeholder_text="Search teams or leagues...",
                     width=320, height=32, border_width=0,
                     fg_color=COLORS["card"], text_color=COLORS["text"],
                     placeholder_text_color=COLORS["text_muted"],
                     font=("Inter", 12)).pack(side="left", padx=(0, 10))

        # Right-side controls
        right = ctk.CTkFrame(topbar, fg_color="transparent")
        right.pack(side="right", padx=20)

        self.refresh_btn = ctk.CTkButton(right, text="↻  Refresh", width=110, height=36,
                                         fg_color=COLORS["card"], hover_color=COLORS["card_hover"],
                                         text_color=COLORS["text"],
                                         font=("Inter", 12, "bold"), corner_radius=8,
                                         command=self._refresh)
        self.refresh_btn.pack(side="right", padx=4)

        self.auto_btn = ctk.CTkButton(right, text="⏱  Auto-refresh: OFF", width=170, height=36,
                                      fg_color=COLORS["card"], hover_color=COLORS["card_hover"],
                                      text_color=COLORS["text"],
                                      font=("Inter", 12, "bold"), corner_radius=8,
                                      command=self._toggle_auto_refresh)
        self.auto_btn.pack(side="right", padx=4)

        # Body container
        body = ctk.CTkFrame(self, fg_color=COLORS["bg"])
        body.pack(fill="both", expand=True)

        # Sidebar
        sidebar = ctk.CTkFrame(body, fg_color=COLORS["bg_alt"], width=240, corner_radius=0)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        ctk.CTkLabel(sidebar, text="NAVIGATION",
                     font=("Inter", 10, "bold"), text_color=COLORS["text_muted"]
                     ).pack(anchor="w", padx=20, pady=(20, 8))

        self._sidebar_btn(sidebar, "⚡  Live Matches",
                          self._show_live_matches).pack(fill="x", padx=12, pady=4)
        self._sidebar_btn(sidebar, "📅  Today",
                          lambda: self._show_date_matches(datetime.now().date())
                          ).pack(fill="x", padx=12, pady=4)
        self._sidebar_btn(sidebar, "▶  Tomorrow",
                          lambda: self._show_date_matches(
                              datetime.now().date() + timedelta(days=1))
                          ).pack(fill="x", padx=12, pady=4)
        self._sidebar_btn(sidebar, "◀  Yesterday",
                          lambda: self._show_date_matches(
                              datetime.now().date() - timedelta(days=1))
                          ).pack(fill="x", padx=12, pady=4)

        ctk.CTkLabel(sidebar, text="DATE PICKER",
                     font=("Inter", 10, "bold"), text_color=COLORS["text_muted"]
                     ).pack(anchor="w", padx=20, pady=(24, 8))

        self.date_btn = ctk.CTkButton(sidebar, text=self.current_date.strftime("%b %d, %Y"),
                                      height=44, fg_color=COLORS["card"],
                                      hover_color=COLORS["card_hover"],
                                      text_color=COLORS["text"],
                                      font=("Inter", 13, "bold"), corner_radius=10,
                                      command=self._open_calendar)
        self.date_btn.pack(fill="x", padx=12, pady=4)

        ctk.CTkButton(sidebar, text="Show matches",
                      height=40, fg_color=COLORS["accent"],
                      hover_color=COLORS["accent_hover"],
                      text_color="#FFFFFF",
                      font=("Inter", 12, "bold"), corner_radius=10,
                      command=lambda: self._show_date_matches(self.current_date)
                      ).pack(fill="x", padx=12, pady=(8, 4))

        ctk.CTkLabel(sidebar, text="Powered by RapidAPI · Livescore6",
                     font=("Inter", 9), text_color=COLORS["text_muted"]
                     ).pack(side="bottom", pady=14)

        # Content area
        self.content = ctk.CTkFrame(body, fg_color=COLORS["bg"])
        self.content.pack(side="right", fill="both", expand=True, padx=24, pady=20)

    def _sidebar_btn(self, parent, text, command):
        return ctk.CTkButton(parent, text=text, height=42, anchor="w",
                             fg_color="transparent",
                             hover_color=COLORS["card"],
                             text_color=COLORS["text"],
                             font=("Inter", 13), corner_radius=10,
                             command=command)

    # ----- Helpers -----
    def _clear_content(self):
        for w in self.content.winfo_children():
            w.destroy()

    def _show_loading(self, message="Loading..."):
        self._clear_content()
        wrap = ctk.CTkFrame(self.content, fg_color="transparent")
        wrap.pack(expand=True)
        ctk.CTkLabel(wrap, text="⏳", font=("Inter", 36),
                     text_color=COLORS["accent"]).pack(pady=(120, 8))
        ctk.CTkLabel(wrap, text=message, font=("Inter", 14),
                     text_color=COLORS["text_muted"]).pack()

    def _show_error(self, message, retry=None):
        self._clear_content()
        wrap = ctk.CTkFrame(self.content, fg_color="transparent")
        wrap.pack(expand=True)
        ctk.CTkLabel(wrap, text="⚠", font=("Inter", 42),
                     text_color=COLORS["warn"]).pack(pady=(100, 12))
        ctk.CTkLabel(wrap, text="Couldn't load data", font=("Inter", 18, "bold"),
                     text_color=COLORS["text"]).pack(pady=(0, 4))
        ctk.CTkLabel(wrap, text=message, font=("Inter", 12),
                     text_color=COLORS["text_muted"]).pack()
        if retry:
            ctk.CTkButton(wrap, text="Try again", height=38, width=140,
                          fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
                          font=("Inter", 12, "bold"), corner_radius=8,
                          command=retry).pack(pady=20)

    def _show_empty(self, message):
        self._clear_content()
        wrap = ctk.CTkFrame(self.content, fg_color="transparent")
        wrap.pack(expand=True)
        ctk.CTkLabel(wrap, text="○", font=("Inter", 48),
                     text_color=COLORS["text_muted"]).pack(pady=(120, 12))
        ctk.CTkLabel(wrap, text=message, font=("Inter", 14),
                     text_color=COLORS["text_muted"]).pack()

    # ----- Search -----
    def _on_search(self, *_):
        self.search_text = self.search_var.get().strip().lower()
        if self.last_matches_data and self.current_view in ("live", "date"):
            self._render_matches(self.last_matches_data, self._current_title())

    def _current_title(self):
        if self.current_view == "live":
            return "Live Matches"
        return f"Matches · {self.current_date.strftime('%A, %B %d, %Y')}"

    # ----- Refresh / auto-refresh -----
    def _refresh(self):
        if self.current_view == "live":
            cache.invalidate("live")
            self._show_live_matches()
        elif self.current_view == "date":
            cache.invalidate(f"date:{self.current_date.strftime('%Y%m%d')}")
            self._show_date_matches(self.current_date)

    def _toggle_auto_refresh(self):
        self.auto_refresh = not self.auto_refresh
        if self.auto_refresh:
            self.auto_btn.configure(text="⏱  Auto-refresh: ON",
                                    fg_color=COLORS["accent"], text_color="#FFFFFF")
            self._schedule_refresh()
        else:
            self.auto_btn.configure(text="⏱  Auto-refresh: OFF",
                                    fg_color=COLORS["card"], text_color=COLORS["text"])
            if self.refresh_after_id:
                self.after_cancel(self.refresh_after_id)
                self.refresh_after_id = None

    def _schedule_refresh(self):
        if not self.auto_refresh:
            return
        self._refresh()
        self.refresh_after_id = self.after(AUTO_REFRESH_MS, self._schedule_refresh)

    # ----- Calendar -----
    def _open_calendar(self):
        CalendarPopup(self, self.current_date, self._on_date_picked)

    def _on_date_picked(self, d):
        self.current_date = d
        self.date_btn.configure(text=d.strftime("%b %d, %Y"))
        self._show_date_matches(d)

    # ----- Live matches view -----
    def _show_live_matches(self):
        self.current_view = "live"
        self._show_loading("Fetching live matches...")

        def on_done(result):
            data, err = result
            if err:
                self._show_error(err, retry=self._show_live_matches)
                return
            self.last_matches_data = data
            self._render_matches(data, "Live Matches")

        run_async(self, fetch_live_matches, on_done)

    # ----- Date matches view -----
    def _show_date_matches(self, d):
        self.current_view = "date"
        self.current_date = d
        self.date_btn.configure(text=d.strftime("%b %d, %Y"))
        self._show_loading(f"Loading matches for {d.strftime('%B %d, %Y')}...")

        def on_done(result):
            data, err = result
            if err:
                self._show_error(err, retry=lambda: self._show_date_matches(d))
                return
            self.last_matches_data = data
            self._render_matches(data, f"Matches · {d.strftime('%A, %B %d, %Y')}")

        run_async(self, lambda: fetch_matches_by_date(d.strftime("%Y%m%d")), on_done)

    # ----- Render match list -----
    def _render_matches(self, data, title):
        self._clear_content()

        # Header
        header = ctk.CTkFrame(self.content, fg_color="transparent")
        header.pack(fill="x", pady=(0, 14))
        ctk.CTkLabel(header, text=title, font=("Inter", 22, "bold"),
                     text_color=COLORS["text"]).pack(side="left")

        stages = data.get("Stages", []) if data else []
        total_events = sum(len(s.get("Events", [])) for s in stages)
        total_leagues = len(stages)

        if self.search_text:
            ctk.CTkLabel(header, text=f"Filter: '{self.search_text}'",
                         font=("Inter", 11),
                         text_color=COLORS["accent"]).pack(side="right", padx=10)

        ctk.CTkLabel(header, text=f"{total_events} matches · {total_leagues} competitions",
                     font=("Inter", 11),
                     text_color=COLORS["text_muted"]).pack(side="right")

        # Scrollable area
        scroll = ctk.CTkScrollableFrame(self.content, fg_color="transparent",
                                        scrollbar_button_color=COLORS["card"],
                                        scrollbar_button_hover_color=COLORS["card_hover"])
        scroll.pack(fill="both", expand=True)

        any_shown = False
        for stage in stages:
            league_name = stage.get("Snm", "Unknown")
            country = stage.get("Cnm", "")
            events = stage.get("Events", [])

            if self.search_text:
                events = [e for e in events if self._match_in_search(e, league_name, country)]
            if not events:
                continue
            any_shown = True

            league_header = ctk.CTkFrame(scroll, fg_color="transparent")
            league_header.pack(fill="x", pady=(12, 6))
            ctk.CTkLabel(league_header, text=f"{country}  ·  {league_name}".strip(" ·"),
                         font=("Inter", 12, "bold"),
                         text_color=COLORS["text_muted"]).pack(side="left")
            ctk.CTkLabel(league_header, text=f"{len(events)}",
                         font=("Inter", 10, "bold"),
                         text_color=COLORS["text_muted"],
                         fg_color=COLORS["card"], corner_radius=10,
                         padx=8, pady=2).pack(side="right")

            for event in events:
                MatchCard(scroll, event, self._show_match_details, height=78
                          ).pack(fill="x", pady=4)

        if not any_shown:
            msg = "No matches match your search." if self.search_text else "No matches available."
            self._show_empty(msg)

    def _match_in_search(self, event, league, country):
        q = self.search_text
        targets = [
            event.get("T1", [{}])[0].get("Nm", ""),
            event.get("T2", [{}])[0].get("Nm", ""),
            league, country,
        ]
        return any(q in t.lower() for t in targets if t)

    # ----- Match details view -----
    def _show_match_details(self, event):
        self.current_view = "details"
        eid = event.get("Eid")
        if not eid:
            return

        self._clear_content()

        header = ctk.CTkFrame(self.content, fg_color="transparent")
        header.pack(fill="x", pady=(0, 14))

        ctk.CTkButton(header, text="← Back", width=80, height=32,
                      fg_color=COLORS["card"], hover_color=COLORS["card_hover"],
                      text_color=COLORS["text"],
                      font=("Inter", 12, "bold"), corner_radius=8,
                      command=self._back_to_list).pack(side="left")

        # Banner
        banner = ctk.CTkFrame(self.content, fg_color=COLORS["card"], corner_radius=12,
                              border_width=1, border_color=COLORS["border"])
        banner.pack(fill="x", pady=(0, 16))

        home = event.get("T1", [{}])[0].get("Nm", "Home")
        away = event.get("T2", [{}])[0].get("Nm", "Away")
        s1 = event.get("Tr1", "-")
        s2 = event.get("Tr2", "-")
        status = event.get("Eps", "")

        banner_inner = ctk.CTkFrame(banner, fg_color="transparent")
        banner_inner.pack(fill="x", padx=20, pady=20)

        ctk.CTkLabel(banner_inner, text=home, font=("Inter", 20, "bold"),
                     text_color=COLORS["text"], anchor="e"
                     ).pack(side="left", expand=True, fill="x")

        score_box = ctk.CTkFrame(banner_inner, fg_color="transparent", width=200)
        score_box.pack(side="left", padx=20)
        score_box.pack_propagate(False)
        ctk.CTkLabel(score_box, text=f"{s1}  :  {s2}", font=("Inter", 32, "bold"),
                     text_color=COLORS["accent"]).pack()
        ctk.CTkLabel(score_box, text=status, font=("Inter", 11, "bold"),
                     text_color=COLORS["text_muted"]).pack()

        ctk.CTkLabel(banner_inner, text=away, font=("Inter", 20, "bold"),
                     text_color=COLORS["text"], anchor="w"
                     ).pack(side="left", expand=True, fill="x")

        # Tabs
        tabview = ctk.CTkTabview(
            self.content, fg_color=COLORS["card"],
            segmented_button_fg_color=COLORS["bg_alt"],
            segmented_button_selected_color=COLORS["accent"],
            segmented_button_selected_hover_color=COLORS["accent_hover"],
            segmented_button_unselected_color=COLORS["bg_alt"],
            segmented_button_unselected_hover_color=COLORS["card_hover"],
            text_color=COLORS["text"],
        )
        tabview.pack(fill="both", expand=True)
        tabview.add("Statistics")
        tabview.add("Lineups")

        for tab_name in ("Statistics", "Lineups"):
            ctk.CTkLabel(tabview.tab(tab_name), text="⏳ Loading...",
                         font=("Inter", 14), text_color=COLORS["text_muted"]
                         ).pack(pady=80)

        def stats_done(result):
            data, err = result
            tab = tabview.tab("Statistics")
            for w in tab.winfo_children():
                w.destroy()
            if err:
                ctk.CTkLabel(tab, text=f"Couldn't load: {err}",
                             text_color=COLORS["warn"], font=("Inter", 12)
                             ).pack(pady=40)
                return
            self._render_statistics(tab, data, home, away)

        def lineups_done(result):
            data, err = result
            tab = tabview.tab("Lineups")
            for w in tab.winfo_children():
                w.destroy()
            if err:
                ctk.CTkLabel(tab, text=f"Couldn't load: {err}",
                             text_color=COLORS["warn"], font=("Inter", 12)
                             ).pack(pady=40)
                return
            self._render_lineups(tab, data, home, away)

        run_async(self, lambda: fetch_statistics(eid), stats_done)
        run_async(self, lambda: fetch_lineups(eid), lineups_done)

    def _back_to_list(self):
        if self.last_matches_data:
            self._render_matches(self.last_matches_data, self._current_title())
        else:
            self._show_live_matches()

    # ----- Statistics rendering -----
    def _render_statistics(self, parent, data, home_name, away_name):
        stat_order = [
            ("Ths", "Total Shots"),
            ("Shon", "Shots on Target"),
            ("Shof", "Shots off Target"),
            ("Shbl", "Shots Blocked"),
            ("Shwd", "Shots Woodwork"),
            ("Att", "Attacks"),
            ("Pss", "Passes"),
            ("Cos", "Corners"),
            ("Ofs", "Offsides"),
            ("Fls", "Fouls"),
            ("Crs", "Crosses"),
            ("Gks", "Goal Kicks"),
            ("Ycs", "Yellow Cards"),
            ("Rcs", "Red Cards"),
            ("YRcs", "Yellow/Red"),
        ]

        teams = data.get("Stat", [])
        if len(teams) < 2:
            ctk.CTkLabel(parent, text="No statistics available for this match.",
                         font=("Inter", 13), text_color=COLORS["text_muted"]
                         ).pack(pady=40)
            return

        scroll = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=10, pady=10)

        head = ctk.CTkFrame(scroll, fg_color="transparent")
        head.pack(fill="x", pady=(4, 12))
        ctk.CTkLabel(head, text=home_name, font=("Inter", 13, "bold"),
                     text_color=COLORS["accent"], anchor="w"
                     ).pack(side="left", expand=True, fill="x")
        ctk.CTkLabel(head, text=away_name, font=("Inter", 13, "bold"),
                     text_color=COLORS["blue"], anchor="e"
                     ).pack(side="right", expand=True, fill="x")

        t1, t2 = teams[0], teams[1]
        any_stat = False
        for key, label in stat_order:
            if key in t1 or key in t2:
                any_stat = True
                StatBar(scroll, label, t1.get(key, 0), t2.get(key, 0)
                        ).pack(fill="x", pady=2)

        if not any_stat:
            ctk.CTkLabel(scroll, text="No statistics available for this match.",
                         font=("Inter", 13), text_color=COLORS["text_muted"]
                         ).pack(pady=40)

    # ----- Lineups rendering -----
    def _render_lineups(self, parent, data, home_name, away_name):
        teams = data.get("Lu", [])
        if not teams or len(teams) < 2:
            ctk.CTkLabel(parent, text="Lineups not available for this match.",
                         font=("Inter", 13), text_color=COLORS["text_muted"]
                         ).pack(pady=40)
            return

        scroll = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=10, pady=10)

        cols = ctk.CTkFrame(scroll, fg_color="transparent")
        cols.pack(fill="both", expand=True)

        for i, (team_data, name, color) in enumerate([
            (teams[0], home_name, COLORS["accent"]),
            (teams[1], away_name, COLORS["blue"]),
        ]):
            col = ctk.CTkFrame(cols, fg_color=COLORS["bg_alt"], corner_radius=10,
                               border_width=1, border_color=COLORS["border"])
            col.grid(row=0, column=i, sticky="nsew", padx=6, pady=6)
            cols.grid_columnconfigure(i, weight=1)

            ctk.CTkLabel(col, text=name, font=("Inter", 14, "bold"),
                         text_color=color).pack(pady=(12, 4), padx=12, anchor="w")

            players = team_data.get("Ps", [])
            starters, staff = [], []
            for p in players:
                fn = p.get("Fn", "").strip()
                ln = p.get("Ln", "").strip()
                pos = p.get("Pon", "").strip() or p.get("Pos", "").strip()
                shirt = p.get("Snu") or p.get("Shn") or ""
                full = f"{fn} {ln}".strip()
                if pos.lower() in ("manager", "coach"):
                    staff.append((full, pos))
                else:
                    starters.append((shirt, full, pos))

            if starters:
                ctk.CTkLabel(col, text="STARTING XI",
                             font=("Inter", 10, "bold"),
                             text_color=COLORS["text_muted"]
                             ).pack(anchor="w", padx=12, pady=(8, 4))
                for shirt, full, pos in starters:
                    row = ctk.CTkFrame(col, fg_color="transparent")
                    row.pack(fill="x", padx=12, pady=2)
                    if shirt:
                        ctk.CTkLabel(row, text=str(shirt),
                                     font=("Inter", 11, "bold"),
                                     text_color=color, fg_color=COLORS["card"],
                                     corner_radius=6, padx=6, pady=2, width=28
                                     ).pack(side="left")
                    ctk.CTkLabel(row, text=full, font=("Inter", 12),
                                 text_color=COLORS["text"], anchor="w"
                                 ).pack(side="left", padx=8, fill="x", expand=True)
                    if pos:
                        ctk.CTkLabel(row, text=pos, font=("Inter", 10),
                                     text_color=COLORS["text_muted"]
                                     ).pack(side="right")

            if staff:
                ctk.CTkLabel(col, text="STAFF",
                             font=("Inter", 10, "bold"),
                             text_color=COLORS["text_muted"]
                             ).pack(anchor="w", padx=12, pady=(12, 4))
                for full, pos in staff:
                    row = ctk.CTkFrame(col, fg_color="transparent")
                    row.pack(fill="x", padx=12, pady=2)
                    ctk.CTkLabel(row, text=full, font=("Inter", 12),
                                 text_color=COLORS["text"], anchor="w"
                                 ).pack(side="left", fill="x", expand=True)
                    ctk.CTkLabel(row, text=pos, font=("Inter", 10),
                                 text_color=COLORS["text_muted"]
                                 ).pack(side="right")

            ctk.CTkFrame(col, fg_color="transparent", height=12).pack()
