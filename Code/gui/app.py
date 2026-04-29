import os
import sys
import threading

import customtkinter as ctk

from config.settings import Settings
from core.scheduler import Scheduler
from database.connection import DatabaseConnection
from gui.theme import (
    PRIMARY, PRIMARY_DARK, PRIMARY_LIGHT, SUCCESS, WARNING, ERROR,
    SURFACE, SIDEBAR_BG, CARD_BG, BORDER, DIVIDER,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_HINT,
    FONT_PAGE_TITLE, FONT_SECTION, FONT_BODY, FONT_CAPTION,
    FONT_NAV, FONT_SIDEBAR_TITLE, FONT_STATUS, FONT_BTN_BOLD,
    CORNER_RADIUS_CARD, CORNER_RADIUS_BTN,
    SIDEBAR_WIDTH, STATUSBAR_HEIGHT,
    make_font,
)
from gui.components.widgets import ProgressDialog
from service.dashboard_service import DashboardService
from service.history_service import HistoryService
from service.rule_service import RuleService
from service.settings_service import SettingsService
from utils.helpers import sanitize_ascii

NAV_ITEMS = [
    ("dashboard", "\u25C8  \u63A8\u9001\u6982\u89C8"),
    ("rules",     "\u25C6  \u63A8\u9001\u89C4\u5219"),
    ("history",   "\u25CE  \u5386\u53F2\u8BB0\u5F55"),
    ("settings",  "\u2699  \u7CFB\u7EDF\u8BBE\u7F6E"),
]


class App(ctk.CTk):
    """主应用窗口。"""

    def __init__(self):
        super().__init__()
        self._settings = Settings.get_instance()
        self._db = DatabaseConnection.get_instance()
        self._settings_svc = SettingsService(self._db, self._settings)
        self._dashboard_svc = DashboardService(self._db)
        self._rule_svc = RuleService(self._db)
        self._history_svc = HistoryService(self._db)
        self._scheduler = Scheduler(self._settings)
        self._pages: dict[str, ctk.CTkFrame] = {}
        self._current_page: str = ""

        self.title("GitHub \u70ED\u70B9\u63A8\u9001")
        self.geometry("960x640")
        self.minsize(800, 500)

        theme = self._settings.get("app.theme", "system")
        ctk.set_appearance_mode(theme)
        ctk.set_default_color_theme("blue")

        self._build_ui()

        if not self._settings.github_token and not self._settings.llm_api_key:
            self.after(500, self._show_welcome_dialog)

    def on_closing(self) -> None:
        """窗口关闭事件处理。"""
        minimize = self._settings.get("app.minimize_to_tray", True)
        if minimize:
            self.withdraw()
        else:
            self.destroy()

    def _build_ui(self) -> None:
        self._build_sidebar()
        self._build_main_area()
        self._build_statusbar()
        self._switch_page("dashboard")

    def _build_sidebar(self) -> None:
        self._sidebar = ctk.CTkFrame(
            self, width=SIDEBAR_WIDTH, corner_radius=0,
            fg_color=SIDEBAR_BG,
        )
        self._sidebar.pack(side="left", fill="y")
        self._sidebar.pack_propagate(False)

        logo_frame = ctk.CTkFrame(self._sidebar, fg_color="transparent")
        logo_frame.pack(fill="x", padx=16, pady=(20, 4))

        ctk.CTkLabel(
            logo_frame, text="GH",
            font=make_font(FONT_PAGE_TITLE),
            text_color=PRIMARY,
        ).pack(side="left")

        ctk.CTkLabel(
            logo_frame, text=" Trending",
            font=make_font(FONT_SECTION),
            text_color=TEXT_PRIMARY,
        ).pack(side="left")

        ctk.CTkLabel(
            self._sidebar, text="GitHub \u70ED\u70B9\u63A8\u9001",
            font=make_font(FONT_CAPTION), text_color=TEXT_HINT,
        ).pack(anchor="w", padx=16, pady=(0, 16))

        sep = ctk.CTkFrame(self._sidebar, height=1, fg_color=DIVIDER)
        sep.pack(fill="x", padx=12, pady=(0, 8))

        self._nav_buttons: dict[str, ctk.CTkButton] = {}
        for key, label in NAV_ITEMS:
            btn = ctk.CTkButton(
                self._sidebar, text=label,
                font=make_font(FONT_NAV), anchor="w",
                fg_color="transparent",
                text_color=TEXT_SECONDARY,
                hover_color=CARD_BG,
                corner_radius=CORNER_RADIUS_BTN,
                height=36,
                command=lambda k=key: self._switch_page(k),
            )
            btn.pack(fill="x", padx=8, pady=2)
            self._nav_buttons[key] = btn

        sep2 = ctk.CTkFrame(self._sidebar, height=1, fg_color=DIVIDER)
        sep2.pack(fill="x", padx=12, pady=(8, 8))

        self._run_btn = ctk.CTkButton(
            self._sidebar, text="\u25B6  \u7ACB\u5373\u6267\u884C",
            font=make_font(FONT_BTN_BOLD),
            fg_color=PRIMARY_DARK, hover_color=PRIMARY,
            corner_radius=CORNER_RADIUS_BTN,
            height=36,
            command=self._run_pipeline,
        )
        self._run_btn.pack(fill="x", padx=8, pady=4)

        self._scheduler_label = ctk.CTkLabel(
            self._sidebar, text="",
            font=make_font(FONT_CAPTION), text_color=TEXT_HINT,
        )
        self._scheduler_label.pack(anchor="w", padx=16, pady=(4, 0))

    def _build_main_area(self) -> None:
        self._main_area = ctk.CTkFrame(self, fg_color=SURFACE, corner_radius=0)
        self._main_area.pack(side="left", fill="both", expand=True)

        self._content_frame = ctk.CTkFrame(self._main_area, fg_color="transparent")
        self._content_frame.pack(fill="both", expand=True, padx=0, pady=0)

    def _build_statusbar(self) -> None:
        self._statusbar = ctk.CTkFrame(
            self, height=STATUSBAR_HEIGHT, corner_radius=0,
            fg_color=SIDEBAR_BG,
        )
        self._statusbar.pack(side="bottom", fill="x")
        self._statusbar.pack_propagate(False)

        self._status_label = ctk.CTkLabel(
            self._statusbar, text="\u5C31\u7EEA",
            font=make_font(FONT_STATUS), text_color=TEXT_HINT,
        )
        self._status_label.pack(side="left", padx=12)

        self._status_right = ctk.CTkLabel(
            self._statusbar, text="",
            font=make_font(FONT_STATUS), text_color=TEXT_HINT,
        )
        self._status_right.pack(side="right", padx=12)

        self._update_scheduler_status()

    def _update_scheduler_status(self) -> None:
        if self._settings.get("scheduler.enabled", True):
            run_time = self._settings.get("scheduler.run_time", "09:00")
            self._scheduler_label.configure(text=f"\u23F0 \u5B9A\u65F6: {run_time}")
        else:
            self._scheduler_label.configure(text="\u23F0 \u5B9A\u65F6\u5DF2\u7981\u7528")

    def _switch_page(self, page_key: str) -> None:
        if page_key == self._current_page:
            return

        for key, btn in self._nav_buttons.items():
            if key == page_key:
                btn.configure(fg_color=CARD_BG, text_color=PRIMARY)
            else:
                btn.configure(fg_color="transparent", text_color=TEXT_SECONDARY)

        if self._current_page and self._current_page in self._pages:
            self._pages[self._current_page].pack_forget()

        if page_key not in self._pages:
            self._pages[page_key] = self._create_page(page_key)

        page = self._pages[page_key]
        if hasattr(page, "refresh"):
            page.refresh()
        page.pack(in_=self._content_frame, fill="both", expand=True)

        self._current_page = page_key

    def _create_page(self, page_key: str) -> ctk.CTkFrame:
        if page_key == "dashboard":
            from gui.pages.dashboard_page import DashboardPage
            return DashboardPage(self._content_frame, dashboard_svc=self._dashboard_svc)
        elif page_key == "rules":
            from gui.pages.rules_page import RulesPage
            return RulesPage(self._content_frame, rule_svc=self._rule_svc)
        elif page_key == "history":
            from gui.pages.history_page import HistoryPage
            return HistoryPage(self._content_frame, history_svc=self._history_svc)
        elif page_key == "settings":
            from gui.pages.settings_page import SettingsPage
            return SettingsPage(self._content_frame, settings_svc=self._settings_svc)
        else:
            return ctk.CTkFrame(self._content_frame)

    def _run_pipeline(self) -> None:
        self._run_btn.configure(state="disabled", text="\u25CC  \u6267\u884C\u4E2D...")
        self._status_label.configure(text="\u6B63\u5728\u6267\u884C\u63A8\u9001\u4EFB\u52A1...", text_color=WARNING)

        def _do_run():
            try:
                self._scheduler.execute_pipeline()
                self.after(0, lambda: self._on_pipeline_done(True))
            except Exception as e:
                self.after(0, lambda: self._on_pipeline_done(False, str(e)))

        threading.Thread(target=_do_run, daemon=True).start()

    def _on_pipeline_done(self, success: bool, error: str = "") -> None:
        self._run_btn.configure(state="normal", text="\u25B6  \u7ACB\u5373\u6267\u884C")
        if success:
            self._status_label.configure(text="\u63A8\u9001\u4EFB\u52A1\u5B8C\u6210", text_color=SUCCESS)
        else:
            self._status_label.configure(text=f"\u63A8\u9001\u5931\u8D25: {error}", text_color=ERROR)

        if "dashboard" in self._pages:
            self._pages["dashboard"].refresh()
        if "history" in self._pages:
            self._pages["history"].refresh()

    def _show_welcome_dialog(self) -> None:
        dialog = ctk.CTkToplevel(self)
        dialog.title("\u6B22\u8FCE\u4F7F\u7528")
        dialog.geometry("500x440")
        dialog.transient(self)
        dialog.grab_set()

        header = ctk.CTkFrame(dialog, fg_color="transparent")
        header.pack(fill="x", padx=24, pady=(20, 4))
        ctk.CTkLabel(
            header, text="GitHub \u70ED\u70B9\u63A8\u9001",
            font=make_font(FONT_PAGE_TITLE),
            text_color=PRIMARY,
        ).pack(side="left")
        ctk.CTkLabel(
            dialog, text="\u4E3A\u4E86\u6B63\u5E38\u4F7F\u7528\uFF0C\u8BF7\u5B8C\u6210\u4EE5\u4E0B\u914D\u7F6E\uFF1A",
            font=make_font(FONT_BODY), text_color=TEXT_SECONDARY,
        ).pack(anchor="w", padx=24, pady=(0, 12))

        ctk.CTkLabel(dialog, text="1. GitHub Personal Access Token",
                     font=make_font(FONT_BTN_BOLD), anchor="w",
                     text_color=TEXT_PRIMARY).pack(fill="x", padx=24, pady=(0, 2))
        token_entry = ctk.CTkEntry(dialog, show="\u2022", width=440, placeholder_text="ghp_xxxxxxxxxxxx")
        token_entry.pack(padx=24, pady=(0, 12))

        ctk.CTkLabel(dialog, text="2. LLM API \u914D\u7F6E",
                     font=make_font(FONT_BTN_BOLD), anchor="w",
                     text_color=TEXT_PRIMARY).pack(fill="x", padx=24, pady=(0, 2))

        provider_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        provider_frame.pack(fill="x", padx=24, pady=(0, 4))
        ctk.CTkLabel(provider_frame, text="\u4EE3\u7406\u5382\u5BB6", font=make_font(FONT_BODY), width=70).pack(side="left")
        providers = self._settings.llm_providers
        provider_names = [info.get("name", key) for key, info in providers.items()]
        provider_menu = ctk.CTkOptionMenu(provider_frame, values=provider_names, width=180,
                                           fg_color=CARD_BG, button_color=PRIMARY_DARK,
                                           button_hover_color=PRIMARY, text_color=TEXT_PRIMARY)
        provider_menu.pack(side="left", padx=(0, 8))

        base_url_entry = ctk.CTkEntry(provider_frame, width=200, placeholder_text="Base URL")
        base_url_entry.pack(side="left")

        if providers:
            first_info = list(providers.values())[0]
            base_url_entry.insert(0, first_info.get("base_url", ""))

        def _on_provider_change(selected):
            for key, info in providers.items():
                if info.get("name") == selected:
                    base_url_entry.delete(0, "end")
                    base_url_entry.insert(0, info.get("base_url", ""))
                    break

        provider_menu.configure(command=_on_provider_change)

        key_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        key_frame.pack(fill="x", padx=24, pady=(0, 4))
        ctk.CTkLabel(key_frame, text="API Key", font=make_font(FONT_BODY), width=70).pack(side="left")
        key_entry = ctk.CTkEntry(key_frame, show="\u2022", width=370)
        key_entry.pack(side="left")

        create_demo_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            dialog, text="\u521B\u5EFA\u793A\u4F8B\u63A8\u9001\u89C4\u5219\uFF08AI\u5927\u6A21\u578B\u65B9\u5411\uFF09",
            variable=create_demo_var, font=make_font(FONT_BODY), text_color=TEXT_PRIMARY,
        ).pack(padx=24, pady=8, anchor="w")

        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(pady=8)

        def on_skip():
            dialog.grab_release()
            dialog.destroy()

        def on_start():
            token = token_entry.get().strip()
            api_key = key_entry.get().strip()
            base_url = base_url_entry.get().strip()
            provider_name = provider_menu.get()

            provider_key = None
            for key, info in providers.items():
                if info.get("name") == provider_name:
                    provider_key = key
                    break

            if token:
                self._settings.set("github.token", token)
            if api_key:
                self._settings.set("llm.api_key", api_key)
            if base_url:
                self._settings.set("llm.base_url", base_url)
            if provider_key:
                self._settings.set("llm.provider", provider_key)

            plans = providers.get(provider_key, {}).get("plans", [])
            if plans and plans[0].get("model"):
                self._settings.set("llm.model", plans[0]["model"])

            self._settings.save()

            if create_demo_var.get():
                try:
                    self._rule_svc.add_rule({
                        "name": "AI\u5927\u6A21\u578B\u6280\u80FD",
                        "keywords": ["AI", "LLM", "Agent", "RAG"],
                        "topics": ["machine-learning", "nlp"],
                        "language": "Python",
                        "min_stars": 0,
                        "priority": 8,
                        "enabled": True,
                    })
                except Exception:
                    pass

            dialog.grab_release()
            dialog.destroy()

        ctk.CTkButton(btn_frame, text="\u7A0D\u540E\u914D\u7F6E", command=on_skip, width=110, height=34,
                       fg_color="transparent", border_width=1, border_color=BORDER,
                       text_color=TEXT_PRIMARY, hover_color=CARD_BG,
                       font=make_font(FONT_BODY)).pack(side="left", padx=8)
        ctk.CTkButton(btn_frame, text="\u5F00\u59CB\u4F7F\u7528", command=on_start, width=110, height=34,
                       fg_color=PRIMARY_DARK, hover_color=PRIMARY,
                       font=make_font(FONT_BTN_BOLD)).pack(side="left", padx=8)
