import sys
import threading
import customtkinter as ctk
from loguru import logger

from database.connection import DatabaseConnection
from config.settings import Settings
from service.dashboard_service import DashboardService
from service.rule_service import RuleService
from service.history_service import HistoryService
from service.settings_service import SettingsService
from service.task_service import TaskService
from core.scheduler import TaskCallback, AppError


class App(ctk.CTk):
    """主窗口应用。

    包含侧边栏导航、全局操作（立即执行、开机自启）、系统托盘和状态栏。
    """

    def __init__(self):
        super().__init__()

        self.title("GitHub热点推送")
        self.geometry("960x640")
        self.minsize(800, 500)
        self._tray_icon = None
        self._tray_thread = None

        ctk.set_appearance_mode("system")
        ctk.set_default_color_theme("blue")

        self._init_services()
        self._build_ui()
        self._init_system_tray()
        self._check_first_run()

    def _init_services(self) -> None:
        """初始化服务层。"""
        self._db = DatabaseConnection.get_instance()
        self._settings = Settings.get_instance()
        self._dashboard_svc = DashboardService(self._db)
        self._rule_svc = RuleService(self._db)
        self._history_svc = HistoryService(self._db)
        self._settings_svc = SettingsService(self._db, self._settings)
        self._task_svc = TaskService(self._db, self._settings)
        self._task_svc.set_callback(self._create_task_callback())

    def _build_ui(self) -> None:
        """构建UI。"""
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._build_sidebar()
        self._build_content_area()
        self._build_statusbar()

    def _build_sidebar(self) -> None:
        """构建侧边栏。"""
        self._sidebar = ctk.CTkFrame(self, width=160, corner_radius=0)
        self._sidebar.grid(row=0, column=0, rowspan=2, sticky="nsew")
        self._sidebar.grid_rowconfigure(8, weight=1)

        title_label = ctk.CTkLabel(
            self._sidebar, text="🔵 GitHub热点推送",
            font=ctk.CTkFont(size=14, weight="bold"), corner_radius=8,
        )
        title_label.grid(row=0, column=0, padx=12, pady=(16, 20))

        self._nav_buttons = {}
        nav_items = [
            ("dashboard", "🏠 仪表盘", 1),
            ("rules", "📋 推送规则", 2),
            ("history", "📁 历史记录", 3),
            ("settings", "⚙️ 系统设置", 4),
        ]
        for key, text, row in nav_items:
            btn = ctk.CTkButton(
                self._sidebar, text=text, anchor="w",
                font=ctk.CTkFont(size=13),
                fg_color="transparent",
                text_color=("gray10", "gray90"),
                hover_color=("gray75", "gray30"),
                command=lambda k=key: self._switch_page(k),
            )
            btn.grid(row=row, column=0, padx=8, pady=4, sticky="ew")
            self._nav_buttons[key] = btn

        sep = ctk.CTkFrame(self._sidebar, height=1, fg_color=("gray75", "gray30"))
        sep.grid(row=5, column=0, padx=16, pady=8, sticky="ew")

        self._run_btn = ctk.CTkButton(
            self._sidebar, text="▶ 立即执行",
            font=ctk.CTkFont(size=13),
            command=self._on_run_task,
        )
        self._run_btn.grid(row=6, column=0, padx=12, pady=4, sticky="ew")

        self._autostart_var = ctk.BooleanVar(
            value=self._settings.get("autostart.enabled", False)
        )
        self._autostart_cb = ctk.CTkCheckBox(
            self._sidebar, text="开机自启",
            variable=self._autostart_var,
            font=ctk.CTkFont(size=12),
            command=self._on_toggle_autostart,
        )
        self._autostart_cb.grid(row=7, column=0, padx=12, pady=4, sticky="w")

        self._nav_buttons["dashboard"].configure(fg_color=("#1F6FEB", "#1F6FEB"))

    def _build_content_area(self) -> None:
        """构建内容区域。"""
        self._content = ctk.CTkFrame(self, fg_color="transparent")
        self._content.grid(row=0, column=1, sticky="nsew", padx=8, pady=(8, 0))

        self._pages = {}
        self._current_page = None
        self._switch_page("dashboard")

    def _build_statusbar(self) -> None:
        """构建状态栏。"""
        self._statusbar = ctk.CTkFrame(self, height=28, corner_radius=0)
        self._statusbar.grid(row=1, column=1, sticky="sew", padx=8, pady=(0, 4))

        self._status_label = ctk.CTkLabel(
            self._statusbar, text="就绪",
            font=ctk.CTkFont(size=11),
            text_color=("gray50", "gray200"),
        )
        self._status_label.pack(side="left", padx=12)

    def _switch_page(self, page_key: str) -> None:
        """切换页面。"""
        for key, btn in self._nav_buttons.items():
            if key == page_key:
                btn.configure(fg_color=("#1F6FEB", "#1F6FEB"))
            else:
                btn.configure(fg_color="transparent")

        if self._current_page:
            self._current_page.pack_forget()

        if page_key not in self._pages:
            self._pages[page_key] = self._create_page(page_key)

        self._pages[page_key].pack(in_=self._content, fill="both", expand=True)
        self._current_page = self._pages[page_key]

        if hasattr(self._current_page, "refresh"):
            self._current_page.refresh()

    def _create_page(self, page_key: str) -> ctk.CTkFrame:
        """创建页面实例。"""
        from gui.pages.dashboard_page import DashboardPage
        from gui.pages.rules_page import RulesPage
        from gui.pages.history_page import HistoryPage
        from gui.pages.settings_page import SettingsPage

        page_map = {
            "dashboard": lambda: DashboardPage(self._content, self._dashboard_svc),
            "rules": lambda: RulesPage(self._content, self._rule_svc),
            "history": lambda: HistoryPage(self._content, self._history_svc),
            "settings": lambda: SettingsPage(self._content, self._settings_svc),
        }
        return page_map[page_key]()

    def _on_run_task(self) -> None:
        """立即执行推送任务。"""
        self._run_btn.configure(state="disabled", text="⏳ 执行中...")
        self._status_label.configure(text="正在执行推送任务...")
        self._task_svc.run_task_now()

    def _on_toggle_autostart(self) -> None:
        """切换开机自启动。"""
        enabled = self._autostart_var.get()
        try:
            self._task_svc.toggle_autostart(enabled)
        except Exception as e:
            logger.error(f"切换自启动失败: {e}")
            self._autostart_var.set(not enabled)

    def _create_task_callback(self) -> TaskCallback:
        """创建任务回调。"""
        app = self

        class AppTaskCallback(TaskCallback):
            def on_start(self) -> None:
                pass

            def on_progress(self, step: str, current: int, total: int) -> None:
                app.after(0, lambda: app._status_label.configure(text=step))

            def on_complete(self, result: dict) -> None:
                app.after(0, lambda: app._on_task_complete(result))

            def on_error(self, error: AppError) -> None:
                app.after(0, lambda: app._on_task_error(error))

        return AppTaskCallback()

    def _on_task_complete(self, result: dict) -> None:
        """任务完成回调。"""
        self._run_btn.configure(state="normal", text="▶ 立即执行")
        repo_count = result.get("repo_count", 0)
        self._status_label.configure(text=f"推送完成: {repo_count} 个推荐项目")
        if "dashboard" in self._pages and hasattr(self._pages["dashboard"], "refresh"):
            self._pages["dashboard"].refresh()
        self._show_tray_notification("推送完成", f"已为您推荐 {repo_count} 个项目")

    def _on_task_error(self, error: AppError) -> None:
        """任务错误回调。"""
        self._run_btn.configure(state="normal", text="▶ 立即执行")
        self._status_label.configure(text=f"任务失败: {error.message}")
        self._show_tray_notification("推送失败", error.message)

    def _check_first_run(self) -> None:
        """检测首次运行，弹出引导弹窗。"""
        github_token = self._settings.github_token
        llm_api_key = self._settings.llm_api_key

        if not github_token or not llm_api_key:
            self._show_welcome_dialog()

    def _show_welcome_dialog(self) -> None:
        """显示首次运行引导弹窗。"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("欢迎使用 GitHub热点推送")
        dialog.geometry("450x320")
        dialog.transient(self)
        dialog.grab_set()

        ctk.CTkLabel(
            dialog, text="欢迎使用 GitHub热点推送",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).pack(pady=(20, 8))

        ctk.CTkLabel(
            dialog, text="为了正常使用，请完成以下配置：",
            font=ctk.CTkFont(size=13),
        ).pack(pady=(0, 16))

        ctk.CTkLabel(dialog, text="1. GitHub Personal Access Token",
                     font=ctk.CTkFont(size=12), anchor="w").pack(fill="x", padx=24, pady=2)
        token_entry = ctk.CTkEntry(dialog, show="•", width=380)
        token_entry.pack(padx=24, pady=(0, 8))

        ctk.CTkLabel(dialog, text="2. 火山方舟 API Key",
                     font=ctk.CTkFont(size=12), anchor="w").pack(fill="x", padx=24, pady=2)
        key_entry = ctk.CTkEntry(dialog, show="•", width=380)
        key_entry.pack(padx=24, pady=(0, 8))

        create_demo_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            dialog, text="创建示例推送规则（AI大模型方向）",
            variable=create_demo_var, font=ctk.CTkFont(size=12),
        ).pack(padx=24, pady=8)

        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(pady=8)

        def on_skip():
            dialog.grab_release()
            dialog.destroy()

        def on_start():
            token = token_entry.get().strip()
            api_key = key_entry.get().strip()
            if token:
                self._settings.set("github.token", token)
            if api_key:
                self._settings.set("llm.api_key", api_key)
            self._settings.save()

            if create_demo_var.get():
                try:
                    self._rule_svc.add_rule({
                        "name": "AI大模型技能",
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

        ctk.CTkButton(btn_frame, text="稍后配置", command=on_skip,
                       width=100, fg_color="transparent",
                       border_width=1).pack(side="left", padx=8)
        ctk.CTkButton(btn_frame, text="开始使用", command=on_start,
                       width=100).pack(side="left", padx=8)

    # ==================== 系统托盘 ====================

    def _init_system_tray(self) -> None:
        """初始化系统托盘。"""
        try:
            import pystray
            from PIL import Image, ImageDraw

            icon_size = 64
            image = Image.new("RGBA", (icon_size, icon_size), (0, 0, 0, 0))
            draw = ImageDraw.Draw(image)
            draw.ellipse([8, 8, 56, 56], fill="#1F6FEB")
            draw.ellipse([20, 20, 44, 44], fill="white")

            menu = pystray.Menu(
                pystray.MenuItem("显示窗口", self._tray_show_window, default=True),
                pystray.MenuItem("立即执行", self._tray_run_task),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("退出", self._tray_exit),
            )

            self._tray_icon = pystray.Icon("github_pusher", image, "GitHub热点推送", menu)

            self._tray_thread = threading.Thread(target=self._tray_icon.run, daemon=True)
            self._tray_thread.start()
            logger.info("系统托盘已初始化")
        except Exception as e:
            logger.warning(f"系统托盘初始化失败: {e}")
            self._tray_icon = None

    def _tray_show_window(self, icon=None, item=None) -> None:
        """托盘：显示窗口。"""
        self.after(0, self._restore_window)

    def _restore_window(self) -> None:
        """恢复窗口。"""
        self.deiconify()
        self.lift()
        self.focus_force()

    def _tray_run_task(self, icon=None, item=None) -> None:
        """托盘：立即执行。"""
        self.after(0, self._on_run_task)

    def _tray_exit(self, icon=None, item=None) -> None:
        """托盘：退出应用。"""
        if self._tray_icon:
            self._tray_icon.stop()
        self.after(0, self._cleanup_and_exit)

    def _show_tray_notification(self, title: str, message: str) -> None:
        """显示托盘通知气泡。"""
        if self._tray_icon:
            try:
                self._tray_icon.notify(message, title)
            except Exception:
                pass

    # ==================== 窗口关闭 ====================

    def on_closing(self) -> None:
        """关闭窗口事件。"""
        minimize_to_tray = self._settings.get("app.minimize_to_tray", True)
        if minimize_to_tray and self._tray_icon:
            self.withdraw()
            self._show_tray_notification("GitHub热点推送", "应用已最小化到托盘")
        else:
            self._cleanup_and_exit()

    def _cleanup_and_exit(self) -> None:
        """清理并退出。"""
        self._task_svc.stop_scheduler()
        if self._tray_icon:
            self._tray_icon.stop()
        DatabaseConnection.get_instance().close()
        self.destroy()
