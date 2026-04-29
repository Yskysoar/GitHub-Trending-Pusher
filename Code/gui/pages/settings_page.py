import threading

import customtkinter as ctk

from service.settings_service import SettingsService

ACCENT = "#00B4D8"
ACCENT_DIM = "#0077B6"
ACCENT_BRIGHT = "#48CAE4"
SUCCESS = "#3FB950"
ERROR = "#F85149"
WARNING = "#D29922"
BG_CARD = ("#F0F0F0", "#1A1D23")
BG_CARD_HOVER = ("#E5E5E5", "#21262D")
BORDER_COLOR = ("#D0D0D0", "#30363D")
LABEL_COLOR = ("#333333", "#C9D1D9")
HINT_COLOR = ("#666666", "#8B949E")
SECTION_ICON = {
    "github": "◈",
    "evaluation": "◆",
    "llm": "⬡",
    "output": "◎",
    "app": "⚙",
}


class _SectionCard(ctk.CTkFrame):
    """科技感分区卡片。"""

    def __init__(self, master, title: str = "", icon: str = "",
                 accent_color: str = ACCENT, **kwargs):
        super().__init__(master, corner_radius=10, border_width=1,
                         border_color=BORDER_COLOR, **kwargs)

        header = ctk.CTkFrame(self, fg_color="transparent", height=36)
        header.pack(fill="x", padx=(16, 16), pady=(12, 0))
        header.pack_propagate(False)

        accent_bar = ctk.CTkFrame(header, width=4, fg_color=accent_color, corner_radius=2)
        accent_bar.pack(side="left", fill="y", padx=(0, 10))

        ctk.CTkLabel(
            header, text=f"{icon}  {title}" if icon else title,
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=LABEL_COLOR,
        ).pack(side="left")

        self._body = ctk.CTkFrame(self, fg_color="transparent")
        self._body.pack(fill="x", padx=20, pady=(8, 16))

    @property
    def body(self) -> ctk.CTkFrame:
        return self._body


class _FieldRow(ctk.CTkFrame):
    """表单行：标签 + 输入控件。"""

    def __init__(self, master, label: str = "", width: int = 220, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.pack(fill="x", pady=3)

        ctk.CTkLabel(
            self, text=label, font=ctk.CTkFont(size=12),
            text_color=LABEL_COLOR, width=120, anchor="w",
        ).pack(side="left")

        self._widget_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._widget_frame.pack(side="left", fill="x", expand=True)

    @property
    def widget_frame(self) -> ctk.CTkFrame:
        return self._widget_frame


class SettingsPage(ctk.CTkScrollableFrame):
    """系统设置页面。

    包含GitHub配置、推送与评估设置、大模型配置、输出设置、应用设置。
    采用科技感暗色主题设计。
    """

    def __init__(self, master, settings_svc: SettingsService, **kwargs):
        super().__init__(master, **kwargs)
        self._svc = settings_svc
        self._fetched_models: list[str] = []
        self._api_key_visible = False
        self._token_visible = False
        self._build_ui()

    def _build_ui(self) -> None:
        """构建UI。"""
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=(20, 8))

        ctk.CTkLabel(
            header_frame, text="系统设置",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=LABEL_COLOR,
        ).pack(side="left")

        ctk.CTkLabel(
            header_frame, text="配置应用参数与API密钥",
            font=ctk.CTkFont(size=12),
            text_color=HINT_COLOR,
        ).pack(side="left", padx=(12, 0), pady=(6, 0))

        sep = ctk.CTkFrame(self, height=2, fg_color=ACCENT_DIM)
        sep.pack(fill="x", padx=20, pady=(4, 16))

        self._build_github_section()
        self._build_llm_section()
        self._build_evaluation_section()
        self._build_output_section()
        self._build_app_section()
        self._build_action_buttons()

    def _build_github_section(self) -> None:
        """GitHub配置区域。"""
        card = _SectionCard(self, "GitHub 配置", SECTION_ICON["github"], "#238636")
        card.pack(fill="x", padx=20, pady=(0, 12))
        body = card.body

        row_token = _FieldRow(body, "Access Token")
        self._token_entry = ctk.CTkEntry(row_token.widget_frame, show="•", width=240)
        self._token_entry.pack(side="left", padx=(0, 4))
        self._token_toggle = ctk.CTkButton(
            row_token.widget_frame, text="👁", width=32, height=28,
            fg_color="transparent", border_width=1, border_color=BORDER_COLOR,
            font=ctk.CTkFont(size=12),
            command=self._toggle_token_visibility,
        )
        self._token_toggle.pack(side="left", padx=(0, 4))
        self._github_status = ctk.CTkLabel(
            row_token.widget_frame, text="", font=ctk.CTkFont(size=11),
            text_color=HINT_COLOR,
        )
        self._github_status.pack(side="left", padx=(4, 0))
        ctk.CTkButton(
            row_token.widget_frame, text="测试连接", width=70, height=28,
            fg_color=ACCENT_DIM, hover_color=ACCENT,
            font=ctk.CTkFont(size=11),
            command=self._test_github,
        ).pack(side="right")

        row_interval = _FieldRow(body, "抓取间隔(小时)")
        self._interval_entry = ctk.CTkEntry(row_interval.widget_frame, width=80)
        self._interval_entry.pack(side="left")

        row_time = _FieldRow(body, "执行时间")
        self._run_time_entry = ctk.CTkEntry(row_time.widget_frame, width=80, placeholder_text="09:00")
        self._run_time_entry.pack(side="left")

        row_max = _FieldRow(body, "最大抓取数")
        self._max_repos_entry = ctk.CTkEntry(row_max.widget_frame, width=80)
        self._max_repos_entry.pack(side="left")

        row_stars = _FieldRow(body, "最低Star数")
        self._min_stars_entry = ctk.CTkEntry(row_stars.widget_frame, width=80)
        self._min_stars_entry.pack(side="left")

        self._scheduler_var = ctk.BooleanVar()
        cb_frame = ctk.CTkFrame(body, fg_color="transparent")
        cb_frame.pack(fill="x", pady=(6, 0))
        ctk.CTkCheckBox(
            cb_frame, text="启用定时任务", variable=self._scheduler_var,
            font=ctk.CTkFont(size=12), text_color=LABEL_COLOR,
            checkbox_width=20, checkbox_height=20,
            corner_radius=4,
        ).pack(side="left")

    def _build_llm_section(self) -> None:
        """大模型配置区域。"""
        card = _SectionCard(self, "大模型配置", SECTION_ICON["llm"], ACCENT)
        card.pack(fill="x", padx=20, pady=(0, 12))
        body = card.body

        row_provider = _FieldRow(body, "代理厂家")
        self._provider_menu = ctk.CTkOptionMenu(
            row_provider.widget_frame, values=["火山方舟"], width=180,
            fg_color=BG_CARD, button_color=ACCENT_DIM, button_hover_color=ACCENT,
            text_color=LABEL_COLOR, font=ctk.CTkFont(size=12),
            command=self._on_provider_changed,
        )
        self._provider_menu.pack(side="left")

        row_key = _FieldRow(body, "API Key")
        self._api_key_entry = ctk.CTkEntry(row_key.widget_frame, show="•", width=220)
        self._api_key_entry.pack(side="left", padx=(0, 4))
        self._api_key_toggle = ctk.CTkButton(
            row_key.widget_frame, text="👁", width=32, height=28,
            fg_color="transparent", border_width=1, border_color=BORDER_COLOR,
            font=ctk.CTkFont(size=12),
            command=self._toggle_api_key_visibility,
        )
        self._api_key_toggle.pack(side="left", padx=(0, 4))
        self._llm_status = ctk.CTkLabel(
            row_key.widget_frame, text="", font=ctk.CTkFont(size=11),
            text_color=HINT_COLOR,
        )
        self._llm_status.pack(side="left", padx=(4, 0))
        ctk.CTkButton(
            row_key.widget_frame, text="测试", width=50, height=28,
            fg_color=ACCENT_DIM, hover_color=ACCENT,
            font=ctk.CTkFont(size=11),
            command=self._test_llm,
        ).pack(side="right", padx=(4, 0))
        ctk.CTkButton(
            row_key.widget_frame, text="获取模型", width=70, height=28,
            fg_color=ACCENT_DIM, hover_color=ACCENT,
            font=ctk.CTkFont(size=11),
            command=self._fetch_models,
        ).pack(side="right")

        row_url = _FieldRow(body, "Base URL")
        self._base_url_entry = ctk.CTkEntry(row_url.widget_frame, width=340)
        self._base_url_entry.pack(side="left")

        row_model = _FieldRow(body, "模型选择")
        self._model_menu = ctk.CTkOptionMenu(
            row_model.widget_frame, values=["GLM-4.7", "自定义"], width=220,
            fg_color=BG_CARD, button_color=ACCENT_DIM, button_hover_color=ACCENT,
            text_color=LABEL_COLOR, font=ctk.CTkFont(size=12),
        )
        self._model_menu.pack(side="left")

        row_custom = _FieldRow(body, "自定义模型")
        self._custom_model_entry = ctk.CTkEntry(
            row_custom.widget_frame, width=220,
            placeholder_text="留空则使用上方选择的模型",
        )
        self._custom_model_entry.pack(side="left")

        hint_frame = ctk.CTkFrame(body, fg_color="transparent")
        hint_frame.pack(fill="x", pady=(6, 0))
        ctk.CTkLabel(
            hint_frame,
            text='提示：输入API Key后点击「获取模型」可加载可用模型列表，也可直接在「自定义模型」中输入',
            font=ctk.CTkFont(size=11),
            text_color=HINT_COLOR,
        ).pack(side="left")

    def _build_evaluation_section(self) -> None:
        """推送与评估设置区域。"""
        card = _SectionCard(self, "推送与评估", SECTION_ICON["evaluation"], "#8957E5")
        card.pack(fill="x", padx=20, pady=(0, 12))
        body = card.body

        row_topn = _FieldRow(body, "推送项目数量")
        self._top_n_entry = ctk.CTkEntry(row_topn.widget_frame, width=80)
        self._top_n_entry.pack(side="left")

        ctk.CTkLabel(
            body, text="评估权重（之和须为1.0）",
            font=ctk.CTkFont(size=12), text_color=LABEL_COLOR,
        ).pack(anchor="w", pady=(8, 4))

        self._weight_entries = {}
        weight_labels = [
            ("rule_match", "规则匹配度"),
            ("star_threshold", "Star达标度"),
            ("growth_speed", "增长速度"),
            ("learning_value", "学习价值"),
        ]
        for key, label in weight_labels:
            row = _FieldRow(body, label)
            entry = ctk.CTkEntry(row.widget_frame, width=80)
            entry.pack(side="left")
            self._weight_entries[key] = entry

        self._weight_sum_label = ctk.CTkLabel(
            body, text="权重之和: 1.0",
            font=ctk.CTkFont(size=11),
            text_color=HINT_COLOR,
        )
        self._weight_sum_label.pack(anchor="w", pady=(4, 0))

    def _build_output_section(self) -> None:
        """输出设置区域。"""
        card = _SectionCard(self, "输出设置", SECTION_ICON["output"], "#DA3633")
        card.pack(fill="x", padx=20, pady=(0, 12))
        body = card.body

        row_dir = _FieldRow(body, "输出目录")
        self._save_dir_entry = ctk.CTkEntry(row_dir.widget_frame, width=280)
        self._save_dir_entry.pack(side="left", padx=(0, 4))
        ctk.CTkButton(
            row_dir.widget_frame, text="浏览", width=50, height=28,
            fg_color=ACCENT_DIM, hover_color=ACCENT,
            font=ctk.CTkFont(size=11),
            command=self._browse_dir,
        ).pack(side="left")

    def _build_app_section(self) -> None:
        """应用设置区域。"""
        card = _SectionCard(self, "应用设置", SECTION_ICON["app"], "#F0883E")
        card.pack(fill="x", padx=20, pady=(0, 12))
        body = card.body

        row_theme = _FieldRow(body, "主题模式")
        self._theme_menu = ctk.CTkOptionMenu(
            row_theme.widget_frame,
            values=["system", "light", "dark"], width=140,
            fg_color=BG_CARD, button_color=ACCENT_DIM, button_hover_color=ACCENT,
            text_color=LABEL_COLOR, font=ctk.CTkFont(size=12),
        )
        self._theme_menu.pack(side="left")

        self._tray_var = ctk.BooleanVar()
        cb_frame = ctk.CTkFrame(body, fg_color="transparent")
        cb_frame.pack(fill="x", pady=(6, 0))
        ctk.CTkCheckBox(
            cb_frame, text="关闭时最小化到托盘", variable=self._tray_var,
            font=ctk.CTkFont(size=12), text_color=LABEL_COLOR,
            checkbox_width=20, checkbox_height=20,
            corner_radius=4,
        ).pack(side="left")

    def _build_action_buttons(self) -> None:
        """操作按钮。"""
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(8, 20))

        ctk.CTkButton(
            btn_frame, text="恢复默认", width=110, height=36,
            fg_color="transparent", border_width=1, border_color=BORDER_COLOR,
            text_color=LABEL_COLOR, hover_color=BG_CARD_HOVER,
            font=ctk.CTkFont(size=12),
            command=self._restore_defaults,
        ).pack(side="left", padx=(0, 12))

        ctk.CTkButton(
            btn_frame, text="保存设置", width=110, height=36,
            fg_color=ACCENT_DIM, hover_color=ACCENT,
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._save_settings,
        ).pack(side="left")

    def _toggle_token_visibility(self) -> None:
        """切换Token可见性。"""
        self._token_visible = not self._token_visible
        self._token_entry.configure(show="" if self._token_visible else "•")
        self._token_toggle.configure(text="🔒" if self._token_visible else "👁")

    def _toggle_api_key_visibility(self) -> None:
        """切换API Key可见性。"""
        self._api_key_visible = not self._api_key_visible
        self._api_key_entry.configure(show="" if self._api_key_visible else "•")
        self._api_key_toggle.configure(text="🔒" if self._api_key_visible else "👁")

    def _on_provider_changed(self, selected: str) -> None:
        """厂家选择变更回调。"""
        provider_key = self._get_provider_key_by_name(selected)
        if provider_key:
            providers = self._svc.get_settings_for_edit().get("llm", {}).get("providers", {})
            provider_info = providers.get(provider_key, {})
            base_url = provider_info.get("base_url", "")
            self._base_url_entry.delete(0, "end")
            self._base_url_entry.insert(0, base_url)

    def _get_provider_key_by_name(self, name: str) -> str | None:
        """根据厂家显示名称获取配置key。"""
        providers = self._svc.get_settings_for_edit().get("llm", {}).get("providers", {})
        for key, info in providers.items():
            if info.get("name") == name:
                return key
        return None

    def _get_provider_name_by_key(self, key: str) -> str:
        """根据配置key获取厂家显示名称。"""
        providers = self._svc.get_settings_for_edit().get("llm", {}).get("providers", {})
        return providers.get(key, {}).get("name", key)

    def _fetch_models(self) -> None:
        """获取可用模型列表。"""
        api_key = self._api_key_entry.get().strip()
        base_url = self._base_url_entry.get().strip()

        if not api_key:
            from gui.components.widgets import MessageBox
            MessageBox(self.winfo_toplevel(), title="获取模型", message="请先输入API Key", icon="warning")
            return

        self._model_menu.configure(values=["加载中..."])
        self._model_menu.set("加载中...")

        def _do_fetch():
            result = self._svc.fetch_available_models(
                api_key=api_key if api_key else None,
                base_url=base_url if base_url else None,
            )
            self.after(0, lambda: self._on_models_fetched(result))

        thread = threading.Thread(target=_do_fetch, daemon=True)
        thread.start()

    def _on_models_fetched(self, result: dict) -> None:
        """模型列表获取完成回调。"""
        from gui.components.widgets import MessageBox

        if result.get("success"):
            models = result.get("models", [])
            self._fetched_models = models
            if models:
                display_values = models + ["自定义"]
                self._model_menu.configure(values=display_values)
                self._model_menu.set(models[0])
            else:
                self._model_menu.configure(values=["自定义"])
                self._model_menu.set("自定义")
            MessageBox(
                self.winfo_toplevel(), title="获取模型",
                message=result.get("message", "获取成功"),
                icon="check",
            )
        else:
            self._model_menu.configure(values=["自定义"])
            self._model_menu.set("自定义")
            MessageBox(
                self.winfo_toplevel(), title="获取模型",
                message=result.get("message", "获取失败"),
                icon="cancel",
            )

    def refresh(self) -> None:
        """加载当前配置到UI。"""
        config = self._svc.get_settings_for_edit()

        gh = config.get("github", {})
        self._token_entry.delete(0, "end")
        self._token_entry.insert(0, gh.get("token", ""))
        self._interval_entry.delete(0, "end")
        self._interval_entry.insert(0, str(gh.get("fetch_interval_hours", 24)))
        self._run_time_entry.delete(0, "end")
        self._run_time_entry.insert(0, config.get("scheduler", {}).get("run_time", "09:00"))
        self._scheduler_var.set(config.get("scheduler", {}).get("enabled", True))
        self._max_repos_entry.delete(0, "end")
        self._max_repos_entry.insert(0, str(gh.get("max_repos_per_fetch", 50)))
        self._min_stars_entry.delete(0, "end")
        self._min_stars_entry.insert(0, str(gh.get("min_stars", 100)))

        ev = config.get("evaluation", {})
        self._top_n_entry.delete(0, "end")
        self._top_n_entry.insert(0, str(ev.get("top_n", 10)))
        weights = ev.get("weights", {})
        for key, entry in self._weight_entries.items():
            entry.delete(0, "end")
            entry.insert(0, str(weights.get(key, 0.0)))

        llm = config.get("llm", {})
        providers = llm.get("providers", {})
        provider_names = [info.get("name", key) for key, info in providers.items()]
        self._provider_menu.configure(values=provider_names)

        current_provider_key = llm.get("provider", "volcengine")
        current_provider_name = self._get_provider_name_by_key(current_provider_key)
        self._provider_menu.set(current_provider_name)

        self._api_key_entry.delete(0, "end")
        self._api_key_entry.insert(0, llm.get("api_key", ""))

        self._base_url_entry.delete(0, "end")
        self._base_url_entry.insert(0, llm.get("base_url", ""))

        current_model = llm.get("model", "GLM-4.7")
        self._fetched_models = []
        self._model_menu.configure(values=[current_model, "自定义"])
        self._model_menu.set(current_model)

        self._custom_model_entry.delete(0, "end")

        out = config.get("output", {})
        self._save_dir_entry.delete(0, "end")
        self._save_dir_entry.insert(0, out.get("save_dir", ""))

        app = config.get("app", {})
        self._theme_menu.set(app.get("theme", "system"))
        self._tray_var.set(app.get("minimize_to_tray", True))

        self._github_status.configure(text="")
        self._llm_status.configure(text="")

    def _save_settings(self) -> None:
        """保存设置。"""
        try:
            weights = {}
            for key, entry in self._weight_entries.items():
                val = float(entry.get().strip())
                weights[key] = val

            weight_sum = sum(weights.values())
            if abs(weight_sum - 1.0) >= 0.01:
                self._weight_sum_label.configure(
                    text=f"权重之和: {weight_sum:.2f} (必须为1.0)",
                    text_color=ERROR,
                )
                return
            self._weight_sum_label.configure(
                text=f"权重之和: {weight_sum:.2f}",
                text_color=HINT_COLOR,
            )

            provider_name = self._provider_menu.get()
            provider_key = self._get_provider_key_by_name(provider_name)

            selected_model = self._model_menu.get()
            custom_model = self._custom_model_entry.get().strip()
            final_model = custom_model if custom_model else selected_model
            if final_model == "自定义":
                final_model = ""

            settings_data = {
                "github": {
                    "token": self._token_entry.get().strip(),
                    "fetch_interval_hours": int(self._interval_entry.get().strip() or "24"),
                    "max_repos_per_fetch": int(self._max_repos_entry.get().strip() or "50"),
                    "min_stars": int(self._min_stars_entry.get().strip() or "100"),
                },
                "llm": {
                    "provider": provider_key or "custom",
                    "api_key": self._api_key_entry.get().strip(),
                    "base_url": self._base_url_entry.get().strip(),
                    "model": final_model,
                },
                "evaluation": {
                    "top_n": int(self._top_n_entry.get().strip() or "10"),
                    "weights": weights,
                },
                "output": {
                    "save_dir": self._save_dir_entry.get().strip(),
                },
                "scheduler": {
                    "enabled": self._scheduler_var.get(),
                    "run_time": self._run_time_entry.get().strip() or "09:00",
                },
                "app": {
                    "theme": self._theme_menu.get(),
                    "minimize_to_tray": self._tray_var.get(),
                },
            }

            self._svc.save_settings(settings_data)

            theme = settings_data["app"]["theme"]
            ctk.set_appearance_mode(theme)

        except ValueError as e:
            self._weight_sum_label.configure(
                text=f"输入有误: {e}",
                text_color=ERROR,
            )

    def _restore_defaults(self) -> None:
        """恢复默认设置。"""
        self._svc.restore_default_settings()
        self.refresh()

    def _test_github(self) -> None:
        """测试GitHub连接。"""
        token = self._token_entry.get().strip()
        self._github_status.configure(text="测试中...", text_color=WARNING)

        def _do_test():
            result = self._svc.test_github_connection(token=token if token else None)
            self.after(0, lambda: self._on_github_tested(result))

        threading.Thread(target=_do_test, daemon=True).start()

    def _on_github_tested(self, result: dict) -> None:
        """GitHub测试完成回调。"""
        from gui.components.widgets import MessageBox
        msg = result.get("message", "")
        if result.get("success"):
            self._github_status.configure(text="已连接", text_color=SUCCESS)
            MessageBox(self.winfo_toplevel(), title="连接测试", message=msg, icon="check")
        else:
            self._github_status.configure(text="连接失败", text_color=ERROR)
            MessageBox(self.winfo_toplevel(), title="连接测试", message=msg, icon="cancel")

    def _test_llm(self) -> None:
        """测试LLM连接。"""
        api_key = self._api_key_entry.get().strip()
        base_url = self._base_url_entry.get().strip()
        selected_model = self._model_menu.get()
        custom_model = self._custom_model_entry.get().strip()
        model = custom_model if custom_model else selected_model
        if model == "自定义":
            model = None

        self._llm_status.configure(text="测试中...", text_color=WARNING)

        def _do_test():
            result = self._svc.test_llm_connection(
                api_key=api_key if api_key else None,
                base_url=base_url if base_url else None,
                model=model,
            )
            self.after(0, lambda: self._on_llm_tested(result))

        threading.Thread(target=_do_test, daemon=True).start()

    def _on_llm_tested(self, result: dict) -> None:
        """LLM测试完成回调。"""
        from gui.components.widgets import MessageBox
        msg = result.get("message", "")
        if result.get("success"):
            self._llm_status.configure(text="已连接", text_color=SUCCESS)
            MessageBox(self.winfo_toplevel(), title="连接测试", message=msg, icon="check")
        else:
            self._llm_status.configure(text="连接失败", text_color=ERROR)
            MessageBox(self.winfo_toplevel(), title="连接测试", message=msg, icon="cancel")

    def _browse_dir(self) -> None:
        """浏览选择目录。"""
        from tkinter import filedialog
        dir_path = filedialog.askdirectory()
        if dir_path:
            self._save_dir_entry.delete(0, "end")
            self._save_dir_entry.insert(0, dir_path)
