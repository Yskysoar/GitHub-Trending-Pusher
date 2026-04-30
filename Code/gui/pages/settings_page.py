import threading

import customtkinter as ctk

from gui.theme import (
    make_font,
    ACTION_BLUE, ACTION_BLUE_DARK, ACTION_BLUE_HOVER,
    SUCCESS, WARNING, ERROR,
    CARD_BG, BORDER, TEXT_PRIMARY, TEXT_SECONDARY, TEXT_HINT,
    ACCENT_TEAL, ACCENT_PURPLE, ACCENT_ORANGE, BRAND_DARK,
    FONT_BODY, FONT_CAPTION, FONT_BTN_BOLD, FONT_LABEL,
    CORNER_RADIUS_BTN, CORNER_RADIUS_ENTRY, CORNER_RADIUS_CARD,
    PAGE_BG,
    SECTION_COLORS, SECTION_ICONS,
    SHORT_FIELD_WIDTH, MEDIUM_FIELD_WIDTH, LONG_FIELD_WIDTH,
    BTN_HEIGHT, BTN_HEIGHT_SM, ENTRY_HEIGHT,
)
from gui.components.widgets import (
    SectionCard, FieldRow, TimePicker, SaveIndicator,
    PrimaryButton, SecondaryButton, GhostButton, MessageBox,
)
from service.settings_service import SettingsService


class SettingsPage(ctk.CTkScrollableFrame):
    def __init__(self, master, settings_svc: SettingsService, **kwargs):
        super().__init__(master, fg_color=PAGE_BG, **kwargs)
        self._svc = settings_svc
        self._fetched_models: list[str] = []
        self._api_key_visible = False
        self._token_visible = False
        self._loading = False
        self._save_timer = None
        self._build_ui()

    def _build_ui(self) -> None:
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=(16, 0))
        self._save_indicator = SaveIndicator(header_frame)
        self._save_indicator.pack(side="right")

        self._build_github_section()
        self._build_llm_section()
        self._build_evaluation_section()
        self._build_output_section()
        self._build_app_section()

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(8, 20))
        SecondaryButton(btn_frame, text="\u6062\u590D\u9ED8\u8BA4", width=110,
                        command=self._restore_defaults).pack(side="left")

    def _build_github_section(self) -> None:
        card = SectionCard(self, "GitHub \u914D\u7F6E", SECTION_ICONS["github"], SECTION_COLORS["github"])
        card.pack(fill="x", padx=20, pady=(0, 10))
        body = card.body

        row_token = FieldRow(body, "Access Token")
        self._token_entry = ctk.CTkEntry(row_token.widget_frame, show="\u2022",
                                          width=MEDIUM_FIELD_WIDTH, height=ENTRY_HEIGHT,
                                          corner_radius=CORNER_RADIUS_ENTRY)
        self._token_entry.pack(side="left", padx=(0, 4))
        self._token_toggle = GhostButton(row_token.widget_frame, text="\u25D0", width=28,
                                          command=self._toggle_token_visibility)
        self._token_toggle.pack(side="left", padx=(0, 4))
        self._github_status = ctk.CTkLabel(
            row_token.widget_frame, text="", font=make_font(FONT_CAPTION), text_color=TEXT_HINT,
        )
        self._github_status.pack(side="left", padx=(4, 0))
        PrimaryButton(row_token.widget_frame, text="\u6D4B\u8BD5", width=56, height=BTN_HEIGHT_SM,
                      command=self._test_github).pack(side="right")
        self._token_entry.bind("<FocusOut>", lambda e: self._schedule_save())
        self._token_entry.bind("<Return>", lambda e: self._do_auto_save())

        row_interval = FieldRow(body, "\u6293\u53D6\u95F4\u9694(\u5C0F\u65F6)")
        self._interval_entry = ctk.CTkEntry(row_interval.widget_frame, width=SHORT_FIELD_WIDTH,
                                             height=ENTRY_HEIGHT, corner_radius=CORNER_RADIUS_ENTRY)
        self._interval_entry.pack(side="left")
        self._interval_entry.bind("<FocusOut>", lambda e: self._schedule_save())
        self._interval_entry.bind("<Return>", lambda e: self._do_auto_save())

        row_time = FieldRow(body, "\u6267\u884C\u65F6\u95F4")
        self._run_time_picker = TimePicker(row_time.widget_frame)
        self._run_time_picker.pack(side="left")
        self._run_time_picker.configure_command(self._on_time_changed)

        row_max = FieldRow(body, "\u6700\u5927\u6293\u53D6\u6570")
        self._max_repos_entry = ctk.CTkEntry(row_max.widget_frame, width=SHORT_FIELD_WIDTH,
                                              height=ENTRY_HEIGHT, corner_radius=CORNER_RADIUS_ENTRY)
        self._max_repos_entry.pack(side="left")
        self._max_repos_entry.bind("<FocusOut>", lambda e: self._schedule_save())
        self._max_repos_entry.bind("<Return>", lambda e: self._do_auto_save())

        row_stars = FieldRow(body, "\u6700\u4F4EStar\u6570")
        self._min_stars_entry = ctk.CTkEntry(row_stars.widget_frame, width=SHORT_FIELD_WIDTH,
                                              height=ENTRY_HEIGHT, corner_radius=CORNER_RADIUS_ENTRY)
        self._min_stars_entry.pack(side="left")
        self._min_stars_entry.bind("<FocusOut>", lambda e: self._schedule_save())
        self._min_stars_entry.bind("<Return>", lambda e: self._do_auto_save())

        self._scheduler_var = ctk.BooleanVar()
        cb_frame = ctk.CTkFrame(body, fg_color="transparent")
        cb_frame.pack(fill="x", pady=(4, 0))
        ctk.CTkCheckBox(
            cb_frame, text="\u542F\u7528\u5B9A\u65F6\u4EFB\u52A1", variable=self._scheduler_var,
            font=make_font(FONT_BODY), text_color=TEXT_PRIMARY,
            checkbox_width=18, checkbox_height=18, corner_radius=3,
            command=self._on_checkbox_changed,
        ).pack(side="left")

    def _build_llm_section(self) -> None:
        card = SectionCard(self, "\u5927\u6A21\u578B\u914D\u7F6E", SECTION_ICONS["llm"], SECTION_COLORS["llm"])
        card.pack(fill="x", padx=20, pady=(0, 10))
        body = card.body

        row_provider = FieldRow(body, "\u4EE3\u7406\u5382\u5BB6")
        config = self._svc.get_settings_for_edit()
        providers = config.get("llm", {}).get("providers", {})
        provider_names = [info.get("name", key) for key, info in providers.items()]
        if not provider_names:
            provider_names = ["\u706B\u5C71\u65B9\u821F Coding Plan"]
        self._provider_menu = ctk.CTkOptionMenu(
            row_provider.widget_frame, values=provider_names, width=MEDIUM_FIELD_WIDTH,
            fg_color=CARD_BG, button_color=ACTION_BLUE_DARK, button_hover_color=ACTION_BLUE,
            text_color=TEXT_PRIMARY, font=make_font(FONT_BODY),
            corner_radius=CORNER_RADIUS_ENTRY,
            command=self._on_provider_changed,
        )
        self._provider_menu.pack(side="left")

        row_key = FieldRow(body, "API Key")
        self._api_key_entry = ctk.CTkEntry(row_key.widget_frame, show="\u2022",
                                            width=MEDIUM_FIELD_WIDTH, height=ENTRY_HEIGHT,
                                            corner_radius=CORNER_RADIUS_ENTRY)
        self._api_key_entry.pack(side="left", padx=(0, 4))
        self._api_key_toggle = GhostButton(row_key.widget_frame, text="\u25D0", width=28,
                                            command=self._toggle_api_key_visibility)
        self._api_key_toggle.pack(side="left", padx=(0, 4))
        self._llm_status = ctk.CTkLabel(
            row_key.widget_frame, text="", font=make_font(FONT_CAPTION), text_color=TEXT_HINT,
        )
        self._llm_status.pack(side="left", padx=(4, 0))
        PrimaryButton(row_key.widget_frame, text="\u6D4B\u8BD5", width=56, height=BTN_HEIGHT_SM,
                      command=self._test_llm).pack(side="right", padx=(4, 0))
        PrimaryButton(row_key.widget_frame, text="\u83B7\u53D6\u6A21\u578B", width=80, height=BTN_HEIGHT_SM,
                      command=self._fetch_models).pack(side="right")
        self._api_key_entry.bind("<FocusOut>", lambda e: self._schedule_save())
        self._api_key_entry.bind("<Return>", lambda e: self._do_auto_save())

        row_url = FieldRow(body, "Base URL")
        self._base_url_entry = ctk.CTkEntry(row_url.widget_frame, width=LONG_FIELD_WIDTH,
                                             height=ENTRY_HEIGHT, corner_radius=CORNER_RADIUS_ENTRY)
        self._base_url_entry.pack(side="left")
        self._base_url_entry.bind("<FocusOut>", lambda e: self._schedule_save())
        self._base_url_entry.bind("<Return>", lambda e: self._do_auto_save())

        row_model = FieldRow(body, "\u6A21\u578B\u9009\u62E9")
        self._model_menu = ctk.CTkOptionMenu(
            row_model.widget_frame, values=["GLM-4.7", "\u81EA\u5B9A\u4E49"], width=MEDIUM_FIELD_WIDTH,
            fg_color=CARD_BG, button_color=ACTION_BLUE_DARK, button_hover_color=ACTION_BLUE,
            text_color=TEXT_PRIMARY, font=make_font(FONT_BODY),
            corner_radius=CORNER_RADIUS_ENTRY,
            command=lambda v: self._schedule_save(),
        )
        self._model_menu.pack(side="left")

        row_custom = FieldRow(body, "\u81EA\u5B9A\u4E49\u6A21\u578B")
        self._custom_model_entry = ctk.CTkEntry(
            row_custom.widget_frame, width=MEDIUM_FIELD_WIDTH, height=ENTRY_HEIGHT,
            placeholder_text="\u7559\u7A7A\u5219\u4F7F\u7528\u4E0A\u65B9\u9009\u62E9\u7684\u6A21\u578B",
            corner_radius=CORNER_RADIUS_ENTRY,
        )
        self._custom_model_entry.pack(side="left")
        self._custom_model_entry.bind("<FocusOut>", lambda e: self._schedule_save())
        self._custom_model_entry.bind("<Return>", lambda e: self._do_auto_save())

        hint_frame = ctk.CTkFrame(body, fg_color="transparent")
        hint_frame.pack(fill="x", pady=(4, 0))
        ctk.CTkLabel(
            hint_frame,
            text="\u8F93\u5165API Key\u540E\u70B9\u51FB\u300C\u83B7\u53D6\u6A21\u578B\u300D\u52A0\u8F7D\u60A8\u53EF\u7528\u7684\u6A21\u578B\u5217\u8868\uFF0C\u4E5F\u53EF\u76F4\u63A5\u5728\u300C\u81EA\u5B9A\u4E49\u6A21\u578B\u300D\u4E2D\u8F93\u5165",
            font=make_font(FONT_CAPTION), text_color=TEXT_HINT,
        ).pack(side="left")

    def _build_evaluation_section(self) -> None:
        card = SectionCard(self, "\u63A8\u9001\u4E0E\u8BC4\u4F30", SECTION_ICONS["evaluation"], SECTION_COLORS["evaluation"])
        card.pack(fill="x", padx=20, pady=(0, 10))
        body = card.body

        row_topn = FieldRow(body, "\u63A8\u9001\u9879\u76EE\u6570\u91CF")
        self._top_n_entry = ctk.CTkEntry(row_topn.widget_frame, width=SHORT_FIELD_WIDTH,
                                          height=ENTRY_HEIGHT, corner_radius=CORNER_RADIUS_ENTRY)
        self._top_n_entry.pack(side="left")
        self._top_n_entry.bind("<FocusOut>", lambda e: self._schedule_save())
        self._top_n_entry.bind("<Return>", lambda e: self._do_auto_save())

        ctk.CTkLabel(
            body, text="\u8BC4\u4F30\u6743\u91CD\uFF08\u4E4B\u548C\u987B\u4E3A1.0\uFF09",
            font=make_font(FONT_LABEL), text_color=TEXT_SECONDARY,
        ).pack(anchor="w", pady=(6, 2))

        self._weight_entries = {}
        weight_labels = [
            ("rule_match", "\u89C4\u5219\u5339\u914D\u5EA6"),
            ("star_threshold", "Star\u8FBE\u6807\u5EA6"),
            ("growth_speed", "\u589E\u957F\u901F\u5EA6"),
            ("learning_value", "\u5B66\u4E60\u4EF7\u503C"),
        ]
        for key, label in weight_labels:
            row = FieldRow(body, label)
            entry = ctk.CTkEntry(row.widget_frame, width=SHORT_FIELD_WIDTH,
                                  height=ENTRY_HEIGHT, corner_radius=CORNER_RADIUS_ENTRY)
            entry.pack(side="left")
            entry.bind("<FocusOut>", lambda e: self._schedule_save())
            entry.bind("<Return>", lambda e: self._do_auto_save())
            self._weight_entries[key] = entry

        self._weight_sum_label = ctk.CTkLabel(
            body, text="\u6743\u91CD\u4E4B\u548C: 1.0",
            font=make_font(FONT_CAPTION), text_color=TEXT_HINT,
        )
        self._weight_sum_label.pack(anchor="w", pady=(2, 0))

    def _build_output_section(self) -> None:
        card = SectionCard(self, "\u8F93\u51FA\u8BBE\u7F6E", SECTION_ICONS["output"], SECTION_COLORS["output"])
        card.pack(fill="x", padx=20, pady=(0, 10))
        body = card.body

        row_dir = FieldRow(body, "\u8F93\u51FA\u76EE\u5F55")
        self._save_dir_entry = ctk.CTkEntry(row_dir.widget_frame, width=LONG_FIELD_WIDTH,
                                             height=ENTRY_HEIGHT, corner_radius=CORNER_RADIUS_ENTRY)
        self._save_dir_entry.pack(side="left", padx=(0, 4))
        SecondaryButton(row_dir.widget_frame, text="\u6D4F\u89C8", width=56, height=BTN_HEIGHT_SM,
                        command=self._browse_dir).pack(side="left")
        self._save_dir_entry.bind("<FocusOut>", lambda e: self._schedule_save())
        self._save_dir_entry.bind("<Return>", lambda e: self._do_auto_save())

    def _build_app_section(self) -> None:
        card = SectionCard(self, "\u5E94\u7528\u8BBE\u7F6E", SECTION_ICONS["app"], SECTION_COLORS["app"])
        card.pack(fill="x", padx=20, pady=(0, 10))
        body = card.body

        row_theme = FieldRow(body, "\u4E3B\u9898\u6A21\u5F0F")
        self._theme_menu = ctk.CTkOptionMenu(
            row_theme.widget_frame, values=["system", "light", "dark"], width=MEDIUM_FIELD_WIDTH,
            fg_color=CARD_BG, button_color=ACTION_BLUE_DARK, button_hover_color=ACTION_BLUE,
            text_color=TEXT_PRIMARY, font=make_font(FONT_BODY),
            corner_radius=CORNER_RADIUS_ENTRY,
            command=lambda v: self._on_theme_changed(),
        )
        self._theme_menu.pack(side="left")

        self._tray_var = ctk.BooleanVar()
        cb_frame = ctk.CTkFrame(body, fg_color="transparent")
        cb_frame.pack(fill="x", pady=(4, 0))
        ctk.CTkCheckBox(
            cb_frame, text="\u5173\u95ED\u65F6\u6700\u5C0F\u5316\u5230\u6258\u76D8", variable=self._tray_var,
            font=make_font(FONT_BODY), text_color=TEXT_PRIMARY,
            checkbox_width=18, checkbox_height=18, corner_radius=3,
            command=self._on_checkbox_changed,
        ).pack(side="left")

    def _schedule_save(self) -> None:
        if self._loading:
            return
        if self._save_timer:
            self.after_cancel(self._save_timer)
        self._save_timer = self.after(600, self._do_auto_save)

    def _do_auto_save(self) -> None:
        if self._loading:
            return
        try:
            self._save_settings()
            self._save_indicator.show_saved()
        except Exception as e:
            self._save_indicator.show_error(f"\u4FDD\u5B58\u5931\u8D25: {e}")

    def _on_time_changed(self) -> None:
        if not self._loading:
            self._do_auto_save()

    def _on_checkbox_changed(self) -> None:
        if not self._loading:
            self._do_auto_save()

    def _on_theme_changed(self) -> None:
        if not self._loading:
            self._do_auto_save()

    def _toggle_token_visibility(self) -> None:
        self._token_visible = not self._token_visible
        self._token_entry.configure(show="" if self._token_visible else "\u2022")
        self._token_toggle.configure(text="\u25D1" if self._token_visible else "\u25D0")

    def _toggle_api_key_visibility(self) -> None:
        self._api_key_visible = not self._api_key_visible
        self._api_key_entry.configure(show="" if self._api_key_visible else "\u2022")
        self._api_key_toggle.configure(text="\u25D1" if self._api_key_visible else "\u25D0")

    def _on_provider_changed(self, selected: str) -> None:
        if self._loading:
            return
        provider_key = self._get_provider_key_by_name(selected)
        if provider_key:
            providers = self._svc.get_settings_for_edit().get("llm", {}).get("providers", {})
            provider_info = providers.get(provider_key, {})
            base_url = provider_info.get("base_url", "")
            self._base_url_entry.delete(0, "end")
            self._base_url_entry.insert(0, base_url)

            plans = provider_info.get("plans", [])
            if plans:
                models = [p.get("model", "") for p in plans if p.get("model")]
                if models:
                    display_values = models + ["\u81EA\u5B9A\u4E49"]
                    self._model_menu.configure(values=display_values)
                    self._model_menu.set(models[0])
        self._do_auto_save()

    def _get_provider_key_by_name(self, name: str) -> str | None:
        providers = self._svc.get_settings_for_edit().get("llm", {}).get("providers", {})
        for key, info in providers.items():
            if info.get("name") == name:
                return key
        return None

    def _get_provider_name_by_key(self, key: str) -> str:
        providers = self._svc.get_settings_for_edit().get("llm", {}).get("providers", {})
        return providers.get(key, {}).get("name", key)

    def _fetch_models(self) -> None:
        api_key = self._api_key_entry.get().strip()
        base_url = self._base_url_entry.get().strip()

        if not api_key:
            MessageBox(self.winfo_toplevel(), title="\u83B7\u53D6\u6A21\u578B",
                       message="\u8BF7\u5148\u8F93\u5165API Key", icon="warning")
            return

        self._model_menu.configure(values=["\u52A0\u8F7D\u4E2D..."])
        self._model_menu.set("\u52A0\u8F7D\u4E2D...")

        def _do_fetch():
            result = self._svc.fetch_available_models(
                api_key=api_key if api_key else None,
                base_url=base_url if base_url else None,
            )
            self.after(0, lambda: self._on_models_fetched(result))

        threading.Thread(target=_do_fetch, daemon=True).start()

    def _on_models_fetched(self, result: dict) -> None:
        if result.get("success"):
            models = result.get("models", [])
            self._fetched_models = models
            if models:
                display_values = models + ["\u81EA\u5B9A\u4E49"]
                self._model_menu.configure(values=display_values)
                self._model_menu.set(models[0])
            else:
                self._model_menu.configure(values=["\u81EA\u5B9A\u4E49"])
                self._model_menu.set("\u81EA\u5B9A\u4E49")
            MessageBox(
                self.winfo_toplevel(), title="\u83B7\u53D6\u6A21\u578B",
                message=result.get("message", f"\u83B7\u53D6\u6210\u529F\uFF0C\u5171{len(models)}\u4E2A\u53EF\u7528\u6A21\u578B"),
                icon="check",
            )
        else:
            self._model_menu.configure(values=["\u81EA\u5B9A\u4E49"])
            self._model_menu.set("\u81EA\u5B9A\u4E49")
            MessageBox(
                self.winfo_toplevel(), title="\u83B7\u53D6\u6A21\u578B",
                message=result.get("message", "\u83B7\u53D6\u5931\u8D25"), icon="cancel",
            )

    def refresh(self) -> None:
        self._loading = True
        config = self._svc.get_settings_for_edit()

        gh = config.get("github", {})
        self._token_entry.delete(0, "end")
        self._token_entry.insert(0, gh.get("token", ""))
        self._interval_entry.delete(0, "end")
        self._interval_entry.insert(0, str(gh.get("fetch_interval_hours", 24)))
        self._run_time_picker.set(config.get("scheduler", {}).get("run_time", "09:00"))
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
        self._provider_menu.configure(values=provider_names if provider_names else ["\u706B\u5C71\u65B9\u821F Coding Plan"])

        current_provider_key = llm.get("provider", "volcengine_coding")
        current_provider_name = self._get_provider_name_by_key(current_provider_key)
        self._provider_menu.set(current_provider_name)

        self._api_key_entry.delete(0, "end")
        self._api_key_entry.insert(0, llm.get("api_key", ""))

        self._base_url_entry.delete(0, "end")
        self._base_url_entry.insert(0, llm.get("base_url", ""))

        current_model = llm.get("model", "GLM-4.7")
        self._fetched_models = []
        self._model_menu.configure(values=[current_model, "\u81EA\u5B9A\u4E49"])
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

        self._loading = False

    def _save_settings(self) -> None:
        weights = {}
        for key, entry in self._weight_entries.items():
            val_str = entry.get().strip()
            if val_str:
                weights[key] = float(val_str)
            else:
                weights[key] = 0.0

        weight_sum = sum(weights.values())
        if abs(weight_sum - 1.0) >= 0.01:
            self._weight_sum_label.configure(
                text=f"\u6743\u91CD\u4E4B\u548C: {weight_sum:.2f} (\u5FC5\u987B\u4E3A1.0)",
                text_color=ERROR,
            )
            return
        self._weight_sum_label.configure(
            text=f"\u6743\u91CD\u4E4B\u548C: {weight_sum:.2f}",
            text_color=TEXT_HINT,
        )

        provider_name = self._provider_menu.get()
        provider_key = self._get_provider_key_by_name(provider_name)

        selected_model = self._model_menu.get()
        custom_model = self._custom_model_entry.get().strip()
        final_model = custom_model if custom_model else selected_model
        if final_model == "\u81EA\u5B9A\u4E49":
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
                "run_time": self._run_time_picker.get(),
            },
            "app": {
                "theme": self._theme_menu.get(),
                "minimize_to_tray": self._tray_var.get(),
            },
        }

        self._svc.save_settings(settings_data)

        theme = settings_data["app"]["theme"]
        ctk.set_appearance_mode(theme)

    def _restore_defaults(self) -> None:
        self._svc.restore_default_settings()
        self.refresh()
        self._save_indicator.show_saved()

    def _test_github(self) -> None:
        token = self._token_entry.get().strip()
        self._github_status.configure(text="\u6D4B\u8BD5\u4E2D...", text_color=WARNING)

        def _do_test():
            result = self._svc.test_github_connection(token=token if token else None)
            self.after(0, lambda: self._on_github_tested(result))

        threading.Thread(target=_do_test, daemon=True).start()

    def _on_github_tested(self, result: dict) -> None:
        msg = result.get("message", "")
        if result.get("success"):
            self._github_status.configure(text="\u5DF2\u8FDE\u63A5", text_color=SUCCESS)
            MessageBox(self.winfo_toplevel(), title="\u8FDE\u63A5\u6D4B\u8BD5", message=msg, icon="check")
        else:
            self._github_status.configure(text="\u8FDE\u63A5\u5931\u8D25", text_color=ERROR)
            MessageBox(self.winfo_toplevel(), title="\u8FDE\u63A5\u6D4B\u8BD5", message=msg, icon="cancel")

    def _test_llm(self) -> None:
        api_key = self._api_key_entry.get().strip()
        base_url = self._base_url_entry.get().strip()
        selected_model = self._model_menu.get()
        custom_model = self._custom_model_entry.get().strip()
        model = custom_model if custom_model else selected_model
        if model == "\u81EA\u5B9A\u4E49":
            model = None

        self._llm_status.configure(text="\u6D4B\u8BD5\u4E2D...", text_color=WARNING)

        def _do_test():
            result = self._svc.test_llm_connection(
                api_key=api_key if api_key else None,
                base_url=base_url if base_url else None,
                model=model,
            )
            self.after(0, lambda: self._on_llm_tested(result))

        threading.Thread(target=_do_test, daemon=True).start()

    def _on_llm_tested(self, result: dict) -> None:
        msg = result.get("message", "")
        if result.get("success"):
            self._llm_status.configure(text="\u5DF2\u8FDE\u63A5", text_color=SUCCESS)
            MessageBox(self.winfo_toplevel(), title="\u8FDE\u63A5\u6D4B\u8BD5", message=msg, icon="check")
        else:
            self._llm_status.configure(text="\u8FDE\u63A5\u5931\u8D25", text_color=ERROR)
            MessageBox(self.winfo_toplevel(), title="\u8FDE\u63A5\u6D4B\u8BD5", message=msg, icon="cancel")

    def _browse_dir(self) -> None:
        from tkinter import filedialog
        dir_path = filedialog.askdirectory()
        if dir_path:
            self._save_dir_entry.delete(0, "end")
            self._save_dir_entry.insert(0, dir_path)
            self._do_auto_save()
