import threading

import customtkinter as ctk

from gui.theme import (
    make_font,
    ACTION_BLUE, SUCCESS, WARNING, ERROR,
    ACCENT_TEAL, ACCENT_PURPLE, ACCENT_ORANGE,
    CARD_BG, BORDER, TEXT_PRIMARY, TEXT_SECONDARY, TEXT_HINT,
    FONT_BODY, FONT_CAPTION, FONT_BTN_BOLD, FONT_BODY_EMPH,
    CORNER_RADIUS_CARD, CORNER_RADIUS_ENTRY, PAGE_BG,
    BTN_HEIGHT_SM,
)
from gui.components.widgets import StatCard, RepoListItem, PrimaryButton, MessageBox
from service.dashboard_service import DashboardService


class DashboardPage(ctk.CTkScrollableFrame):
    def __init__(self, master, dashboard_svc: DashboardService, **kwargs):
        super().__init__(master, fg_color=PAGE_BG, **kwargs)
        self._svc = dashboard_svc
        self._build_ui()

    def _build_ui(self) -> None:
        stats_frame = ctk.CTkFrame(self, fg_color="transparent")
        stats_frame.pack(fill="x", padx=20, pady=(16, 12))

        self._stat_total = StatCard(stats_frame, "\u4ECA\u65E5\u6293\u53D6", "0", ACCENT_TEAL)
        self._stat_total.pack(side="left", fill="x", expand=True, padx=(0, 4))

        self._stat_hot = StatCard(stats_frame, "\u70ED\u95E8\u9879\u76EE", "0", ERROR)
        self._stat_hot.pack(side="left", fill="x", expand=True, padx=4)

        self._stat_push = StatCard(stats_frame, "\u5DF2\u63A8\u9001", "0", ACCENT_PURPLE)
        self._stat_push.pack(side="left", fill="x", expand=True, padx=4)

        self._stat_rules = StatCard(stats_frame, "\u6D3B\u8DC3\u89C4\u5219", "0", ACCENT_ORANGE)
        self._stat_rules.pack(side="left", fill="x", expand=True, padx=(4, 0))

        section_header = ctk.CTkFrame(self, fg_color="transparent")
        section_header.pack(fill="x", padx=20, pady=(0, 6))
        ctk.CTkLabel(
            section_header, text="\u70ED\u95E8\u9879\u76EE\u6392\u884C",
            font=make_font(FONT_BODY_EMPH), text_color=TEXT_SECONDARY,
        ).pack(side="left")

        self._repos_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._repos_frame.pack(fill="both", expand=True, padx=20, pady=(0, 16))

    def refresh(self) -> None:
        summary = self._svc.get_dashboard_summary()

        self._stat_total.set_value(str(summary.get("total_fetched", 0)))
        self._stat_hot.set_value(str(summary.get("hot_repos", 0)))
        self._stat_push.set_value(str(summary.get("pushed", 0)))
        self._stat_rules.set_value(str(summary.get("active_rules", 0)))

        for widget in self._repos_frame.winfo_children():
            widget.destroy()

        repos = summary.get("top_repos", [])
        if not repos:
            ctk.CTkLabel(
                self._repos_frame,
                text="\u6682\u65E0\u6570\u636E\uFF0C\u70B9\u51FB\u4FA7\u8FB9\u300C\u7ACB\u5373\u6267\u884C\u300D\u83B7\u53D6\u6700\u65B0\u70ED\u70B9",
                font=make_font(FONT_BODY), text_color=TEXT_HINT,
            ).pack(pady=40)
            return

        for i, repo in enumerate(repos[:10], 1):
            item = RepoListItem(
                self._repos_frame,
                rank=i,
                full_name=repo.get("full_name", ""),
                stars_growth=repo.get("stars_growth", 0),
                eval_score=repo.get("eval_score", 0),
                language=repo.get("language", ""),
            )
            item.pack(fill="x", pady=2)
