import threading

import customtkinter as ctk

from service.settings_service import SettingsService


class SettingsPage(ctk.CTkScrollableFrame):
    """系统设置页面。

    包含GitHub配置、推送与评估设置、大模型配置、输出设置、应用设置。
    """

    def __init__(self, master, settings_svc: SettingsService, **kwargs):
        super().__init__(master, **kwargs)
        self._svc = settings_svc
        self._fetched_models: list[str] = []
        self._build_ui()

    def _build_ui(self) -> None:
        """构建UI。"""
        ctk.CTkLabel(
            self, text="系统设置",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).pack(anchor="w", padx=16, pady=(16, 12))

        self._build_github_section()
        self._build_evaluation_section()
        self._build_llm_section()
        self._build_output_section()
        self._build_app_section()
        self._build_action_buttons()

    def _build_github_section(self) -> None:
        """GitHub配置区域。"""
        frame = ctk.CTkFrame(self)
        frame.pack(fill="x", padx=16, pady=(0, 12))

        ctk.CTkLabel(frame, text="GitHub 配置",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=12, pady=(10, 6))

        row = ctk.CTkFrame(frame, fg_color="transparent")
        row.pack(fill="x", padx=12, pady=4)
        ctk.CTkLabel(row, text="Personal Access Token", font=ctk.CTkFont(size=12)).pack(side="left")
        self._token_entry = ctk.CTkEntry(row, show="•", width=280)
        self._token_entry.pack(side="left", padx=8)
        ctk.CTkButton(row, text="测试", width=50, command=self._test_github).pack(side="left")

        row2 = ctk.CTkFrame(frame, fg_color="transparent")
        row2.pack(fill="x", padx=12, pady=4)
        ctk.CTkLabel(row2, text="抓取间隔（小时）", font=ctk.CTkFont(size=12)).pack(side="left")
        self._interval_entry = ctk.CTkEntry(row2, width=80)
        self._interval_entry.pack(side="left", padx=8)

        row3 = ctk.CTkFrame(frame, fg_color="transparent")
        row3.pack(fill="x", padx=12, pady=4)
        ctk.CTkLabel(row3, text="执行时间", font=ctk.CTkFont(size=12)).pack(side="left")
        self._run_time_entry = ctk.CTkEntry(row3, width=80, placeholder_text="09:00")
        self._run_time_entry.pack(side="left", padx=8)

        self._scheduler_var = ctk.BooleanVar()
        ctk.CTkCheckBox(frame, text="启用定时任务", variable=self._scheduler_var,
                        font=ctk.CTkFont(size=12)).pack(anchor="w", padx=12, pady=4)

        row4 = ctk.CTkFrame(frame, fg_color="transparent")
        row4.pack(fill="x", padx=12, pady=4)
        ctk.CTkLabel(row4, text="最大抓取数", font=ctk.CTkFont(size=12)).pack(side="left")
        self._max_repos_entry = ctk.CTkEntry(row4, width=80)
        self._max_repos_entry.pack(side="left", padx=8)

        row5 = ctk.CTkFrame(frame, fg_color="transparent")
        row5.pack(fill="x", padx=12, pady=(4, 10))
        ctk.CTkLabel(row5, text="最低Star数", font=ctk.CTkFont(size=12)).pack(side="left")
        self._min_stars_entry = ctk.CTkEntry(row5, width=80)
        self._min_stars_entry.pack(side="left", padx=8)

    def _build_evaluation_section(self) -> None:
        """推送与评估设置区域。"""
        frame = ctk.CTkFrame(self)
        frame.pack(fill="x", padx=16, pady=(0, 12))

        ctk.CTkLabel(frame, text="推送与评估设置",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=12, pady=(10, 6))

        row = ctk.CTkFrame(frame, fg_color="transparent")
        row.pack(fill="x", padx=12, pady=4)
        ctk.CTkLabel(row, text="推送项目数量", font=ctk.CTkFont(size=12)).pack(side="left")
        self._top_n_entry = ctk.CTkEntry(row, width=80)
        self._top_n_entry.pack(side="left", padx=8)

        ctk.CTkLabel(frame, text="评估权重（之和须为1.0）",
                     font=ctk.CTkFont(size=12)).pack(anchor="w", padx=12, pady=(8, 4))

        self._weight_entries = {}
        weight_labels = [
            ("rule_match", "规则匹配度"),
            ("star_threshold", "Star达标度"),
            ("growth_speed", "增长速度"),
            ("learning_value", "学习价值"),
        ]
        for key, label in weight_labels:
            row = ctk.CTkFrame(frame, fg_color="transparent")
            row.pack(fill="x", padx=12, pady=2)
            ctk.CTkLabel(row, text=label, font=ctk.CTkFont(size=12), width=100).pack(side="left")
            entry = ctk.CTkEntry(row, width=80)
            entry.pack(side="left", padx=8)
            self._weight_entries[key] = entry

        self._weight_sum_label = ctk.CTkLabel(frame, text="权重之和: 1.0",
                                               font=ctk.CTkFont(size=11),
                                               text_color=("gray50", "gray200"))
        self._weight_sum_label.pack(anchor="w", padx=12, pady=(4, 10))

    def _build_llm_section(self) -> None:
        """大模型配置区域。"""
        frame = ctk.CTkFrame(self)
        frame.pack(fill="x", padx=16, pady=(0, 12))

        ctk.CTkLabel(frame, text="大模型配置",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=12, pady=(10, 6))

        row_provider = ctk.CTkFrame(frame, fg_color="transparent")
        row_provider.pack(fill="x", padx=12, pady=4)
        ctk.CTkLabel(row_provider, text="代理厂家", font=ctk.CTkFont(size=12)).pack(side="left")
        self._provider_menu = ctk.CTkOptionMenu(
            row_provider, values=["火山方舟"], width=160,
            command=self._on_provider_changed,
        )
        self._provider_menu.pack(side="left", padx=8)

        row_key = ctk.CTkFrame(frame, fg_color="transparent")
        row_key.pack(fill="x", padx=12, pady=4)
        ctk.CTkLabel(row_key, text="API Key", font=ctk.CTkFont(size=12)).pack(side="left")
        self._api_key_entry = ctk.CTkEntry(row_key, show="•", width=240)
        self._api_key_entry.pack(side="left", padx=8)
        ctk.CTkButton(row_key, text="测试", width=50, command=self._test_llm).pack(side="left", padx=(0, 4))
        ctk.CTkButton(row_key, text="获取模型", width=70, command=self._fetch_models).pack(side="left")

        row_url = ctk.CTkFrame(frame, fg_color="transparent")
        row_url.pack(fill="x", padx=12, pady=4)
        ctk.CTkLabel(row_url, text="Base URL", font=ctk.CTkFont(size=12)).pack(side="left")
        self._base_url_entry = ctk.CTkEntry(row_url, width=300)
        self._base_url_entry.pack(side="left", padx=8)

        row_model = ctk.CTkFrame(frame, fg_color="transparent")
        row_model.pack(fill="x", padx=12, pady=4)
        ctk.CTkLabel(row_model, text="模型选择", font=ctk.CTkFont(size=12)).pack(side="left")
        self._model_menu = ctk.CTkOptionMenu(row_model, values=["GLM-4.7"], width=200)
        self._model_menu.pack(side="left", padx=8)

        row_custom = ctk.CTkFrame(frame, fg_color="transparent")
        row_custom.pack(fill="x", padx=12, pady=(4, 10))
        ctk.CTkLabel(row_custom, text="自定义模型", font=ctk.CTkFont(size=12)).pack(side="left")
        self._custom_model_entry = ctk.CTkEntry(row_custom, width=200, placeholder_text="留空则使用上方选择的模型")
        self._custom_model_entry.pack(side="left", padx=8)

        self._model_hint_label = ctk.CTkLabel(
            frame, text='提示：输入API Key后点击「获取模型」可加载可用模型列表，也可直接在「自定义模型」中输入',
            font=ctk.CTkFont(size=11),
            text_color=("gray50", "gray200"),
        )
        self._model_hint_label.pack(anchor="w", padx=12, pady=(0, 10))

    def _on_provider_changed(self, selected: str) -> None:
        """厂家选择变更回调。"""
        provider_key = self._get_provider_key_by_name(selected)
        if provider_key:
            providers = self._svc.get_settings_for_edit().get("llm", {}).get("providers", {})
            provider_info = providers.get(provider_key, {})
            base_url = provider_info.get("base_url", "")
            self._base_url_entry.delete(0, "end")
            self._base_url_entry.insert(0, base_url)

            if provider_key == "custom":
                self._base_url_entry.configure(state="normal")
            else:
                self._base_url_entry.configure(state="normal")

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

    def _build_output_section(self) -> None:
        """输出设置区域。"""
        frame = ctk.CTkFrame(self)
        frame.pack(fill="x", padx=16, pady=(0, 12))

        ctk.CTkLabel(frame, text="输出设置",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=12, pady=(10, 6))

        row = ctk.CTkFrame(frame, fg_color="transparent")
        row.pack(fill="x", padx=12, pady=(4, 10))
        ctk.CTkLabel(row, text="日志保存目录", font=ctk.CTkFont(size=12)).pack(side="left")
        self._save_dir_entry = ctk.CTkEntry(row, width=280)
        self._save_dir_entry.pack(side="left", padx=8)
        ctk.CTkButton(row, text="浏览", width=50, command=self._browse_dir).pack(side="left")

    def _build_app_section(self) -> None:
        """应用设置区域。"""
        frame = ctk.CTkFrame(self)
        frame.pack(fill="x", padx=16, pady=(0, 12))

        ctk.CTkLabel(frame, text="应用设置",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=12, pady=(10, 6))

        row = ctk.CTkFrame(frame, fg_color="transparent")
        row.pack(fill="x", padx=12, pady=4)
        ctk.CTkLabel(row, text="主题", font=ctk.CTkFont(size=12)).pack(side="left")
        self._theme_menu = ctk.CTkOptionMenu(row, values=["system", "light", "dark"], width=120)
        self._theme_menu.pack(side="left", padx=8)

        self._tray_var = ctk.BooleanVar()
        ctk.CTkCheckBox(frame, text="关闭时最小化到托盘", variable=self._tray_var,
                        font=ctk.CTkFont(size=12)).pack(anchor="w", padx=12, pady=(4, 10))

    def _build_action_buttons(self) -> None:
        """操作按钮。"""
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=16, pady=(0, 16))

        ctk.CTkButton(
            btn_frame, text="恢复默认", width=100,
            fg_color="transparent", border_width=1,
            command=self._restore_defaults,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkButton(
            btn_frame, text="保存设置", width=100,
            command=self._save_settings,
        ).pack(side="left")

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

    def _save_settings(self) -> None:
        """保存设置。"""
        try:
            weights = {}
            for key, entry in self._weight_entries.items():
                val = float(entry.get().strip())
                weights[key] = val

            weight_sum = sum(weights.values())
            if abs(weight_sum - 1.0) >= 0.01:
                self._weight_sum_label.configure(text=f"权重之和: {weight_sum:.2f} (必须为1.0)", text_color="red")
                return
            self._weight_sum_label.configure(text=f"权重之和: {weight_sum:.2f}", text_color=("gray50", "gray200"))

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
            self._weight_sum_label.configure(text=f"输入有误: {e}", text_color="red")

    def _restore_defaults(self) -> None:
        """恢复默认设置。"""
        self._svc.restore_default_settings()
        self.refresh()

    def _test_github(self) -> None:
        """测试GitHub连接。"""
        token = self._token_entry.get().strip()
        result = self._svc.test_github_connection(token=token if token else None)
        msg = result.get("message", "")
        from gui.components.widgets import MessageBox
        if result.get("success"):
            MessageBox(self.winfo_toplevel(), title="连接测试", message=msg, icon="check")
        else:
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

        result = self._svc.test_llm_connection(
            api_key=api_key if api_key else None,
            base_url=base_url if base_url else None,
            model=model,
        )
        msg = result.get("message", "")
        from gui.components.widgets import MessageBox
        if result.get("success"):
            MessageBox(self.winfo_toplevel(), title="连接测试", message=msg, icon="check")
        else:
            MessageBox(self.winfo_toplevel(), title="连接测试", message=msg, icon="cancel")

    def _browse_dir(self) -> None:
        """浏览选择目录。"""
        from tkinter import filedialog
        dir_path = filedialog.askdirectory()
        if dir_path:
            self._save_dir_entry.delete(0, "end")
            self._save_dir_entry.insert(0, dir_path)
