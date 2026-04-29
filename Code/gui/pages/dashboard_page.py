import customtkinter as ctk

from gui.theme import (
    make_font,
    PRIMARY, PRIMARY_DARK, SUCCESS, WARNING, ERROR,
    CARD_BG, BORDER, TEXT_PRIMARY, TEXT_SECONDARY, TEXT_HINT,
    FONT_BODY, FONT_CAPTION, FONT_SECTION, FONT_STAT_TITLE,
    CORNER_RADIUS_CARD, CORNER_RADIUS_BTN,
)
from gui.components.widgets import StatCard, RepoListItem, PageHeader, PageDivider
from service.dashboard_service import DashboardService


class DashboardPage(ctk.CTkScrollableFrame):
    """仪表盘页面。"""

    def __init__(self, master, dashboard_svc: DashboardService, **kwargs):
        super().__init__(master, **kwargs)
        self._svc = dashboard_svc
        self._build_ui()

    def _build_ui(self) -> None:
        PageHeader(self, "推送概览", "今日数据统计")
        PageDivider(self)

        stats_frame = ctk.CTkFrame(self, fg_color="transparent")
        stats_frame.pack(fill="x", padx=20, pady=(0, 16))

        self._candidate_card = StatCard(stats_frame, title="候选项目", value="0", accent_color=PRIMARY)
        self._candidate_card.pack(side="left", fill="x", expand=True, padx=(0, 6))

        self._matched_card = StatCard(stats_frame, title="匹配仓库", value="0", accent_color=SUCCESS)
        self._matched_card.pack(side="left", fill="x", expand=True, padx=6)

        self._recommended_card = StatCard(stats_frame, title="推荐项目", value="0", accent_color=PRIMARY_DARK)
        self._recommended_card.pack(side="left", fill="x", expand=True, padx=(6, 0))

        top_label = ctk.CTkLabel(
            self, text="TOP 5 推荐项目",
            font=make_font(FONT_SECTION),
            text_color=TEXT_PRIMARY,
        )
        top_label.pack(anchor="w", padx=20, pady=(4, 8))

        self._top_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._top_frame.pack(fill="x", padx=20, pady=(0, 16))

        ctk.CTkLabel(
            self._top_frame,
            text="暂无推送记录，点击左侧「立即执行」开始第一次推送",
            font=make_font(FONT_BODY), text_color=TEXT_HINT,
        ).pack(pady=20)

        latest_label = ctk.CTkLabel(
            self, text="最新推送日志",
            font=make_font(FONT_SECTION),
            text_color=TEXT_PRIMARY,
        )
        latest_label.pack(anchor="w", padx=20, pady=(4, 8))

        self._latest_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._latest_frame.pack(fill="x", padx=20, pady=(0, 16))

        ctk.CTkLabel(
            self._latest_frame, text="暂无推送日志",
            font=make_font(FONT_BODY), text_color=TEXT_HINT,
        ).pack(pady=20)

    def refresh(self) -> None:
        stats = self._svc.get_today_stats()
        self._candidate_card.set_value(str(stats.get("candidate_count", 0)))
        self._matched_card.set_value(str(stats.get("matched_count", 0)))
        self._recommended_card.set_value(str(stats.get("recommended_count", 0)))

        for widget in self._top_frame.winfo_children():
            widget.destroy()

        top_repos = self._svc.get_top_repos(5)
        if top_repos:
            for i, repo in enumerate(top_repos, 1):
                item = RepoListItem(
                    self._top_frame,
                    rank=i,
                    full_name=repo.get("full_name", ""),
                    stars_growth=repo.get("stars_growth", 0),
                    eval_score=repo.get("eval_score", 0),
                    language=repo.get("language", ""),
                )
                item.pack(fill="x", pady=2)
        else:
            ctk.CTkLabel(
                self._top_frame,
                text="暂无推送记录，点击左侧「立即执行」开始第一次推送",
                font=make_font(FONT_BODY), text_color=TEXT_HINT,
            ).pack(pady=20)

        for widget in self._latest_frame.winfo_children():
            widget.destroy()

        latest = self._svc.get_latest_summary()
        if latest:
            ctk.CTkLabel(
                self._latest_frame,
                text=f"{latest.get('generated_at', '')[:10]}  |  "
                     f"{latest.get('repo_count', 0)} 个项目  |  "
                     f"{latest.get('title', '')}",
                font=make_font(FONT_BODY), anchor="w", text_color=TEXT_PRIMARY,
            ).pack(fill="x", pady=4)
        else:
            ctk.CTkLabel(
                self._latest_frame, text="暂无推送日志",
                font=make_font(FONT_BODY), text_color=TEXT_HINT,
            ).pack(pady=20)
