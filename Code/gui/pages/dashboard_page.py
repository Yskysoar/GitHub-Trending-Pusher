import customtkinter as ctk

from gui.components.widgets import StatCard, RepoListItem
from service.dashboard_service import DashboardService


class DashboardPage(ctk.CTkScrollableFrame):
    """仪表盘页面。

    显示推送概览统计、TOP 5项目列表和最新推送日志。
    """

    def __init__(self, master, dashboard_svc: DashboardService, **kwargs):
        super().__init__(master, **kwargs)
        self._svc = dashboard_svc
        self._build_ui()

    def _build_ui(self) -> None:
        """构建UI。"""
        title = ctk.CTkLabel(
            self, text="推送概览",
            font=ctk.CTkFont(size=20, weight="bold"),
        )
        title.pack(anchor="w", padx=16, pady=(16, 8))

        stats_frame = ctk.CTkFrame(self, fg_color="transparent")
        stats_frame.pack(fill="x", padx=16, pady=(0, 16))

        self._candidate_card = StatCard(stats_frame, title="候选项目", value="0")
        self._candidate_card.pack(side="left", fill="x", expand=True, padx=(0, 8))

        self._matched_card = StatCard(stats_frame, title="匹配仓库", value="0")
        self._matched_card.pack(side="left", fill="x", expand=True, padx=4)

        self._recommended_card = StatCard(stats_frame, title="推荐项目", value="0")
        self._recommended_card.pack(side="left", fill="x", expand=True, padx=(8, 0))

        top_title = ctk.CTkLabel(
            self, text="TOP 5 推荐项目",
            font=ctk.CTkFont(size=16, weight="bold"),
        )
        top_title.pack(anchor="w", padx=16, pady=(8, 8))

        self._top_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._top_frame.pack(fill="x", padx=16, pady=(0, 16))

        self._empty_label = ctk.CTkLabel(
            self._top_frame,
            text="暂无推送记录，点击左侧「立即执行」开始第一次推送",
            font=ctk.CTkFont(size=13),
            text_color=("gray50", "gray200"),
        )
        self._empty_label.pack(pady=20)

        latest_title = ctk.CTkLabel(
            self, text="最新推送日志",
            font=ctk.CTkFont(size=16, weight="bold"),
        )
        latest_title.pack(anchor="w", padx=16, pady=(8, 8))

        self._latest_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._latest_frame.pack(fill="x", padx=16, pady=(0, 16))

        self._latest_label = ctk.CTkLabel(
            self._latest_frame,
            text="暂无推送日志",
            font=ctk.CTkFont(size=13),
            text_color=("gray50", "gray200"),
        )
        self._latest_label.pack(pady=20)

    def refresh(self) -> None:
        """刷新仪表盘数据。"""
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
                font=ctk.CTkFont(size=13),
                text_color=("gray50", "gray200"),
            ).pack(pady=20)

        for widget in self._latest_frame.winfo_children():
            widget.destroy()

        latest = self._svc.get_latest_summary()
        if latest:
            info = ctk.CTkLabel(
                self._latest_frame,
                text=f"📅 {latest.get('generated_at', '')[:10]}  |  "
                     f"📊 {latest.get('repo_count', 0)} 个项目  |  "
                     f"{latest.get('title', '')}",
                font=ctk.CTkFont(size=13),
                anchor="w",
            )
            info.pack(fill="x", pady=4)
        else:
            ctk.CTkLabel(
                self._latest_frame,
                text="暂无推送日志",
                font=ctk.CTkFont(size=13),
                text_color=("gray50", "gray200"),
            ).pack(pady=20)
