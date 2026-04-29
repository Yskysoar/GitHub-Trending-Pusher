import customtkinter as ctk


class StatCard(ctk.CTkFrame):
    """统计卡片组件。"""

    def __init__(self, master, title: str = "", value: str = "0", **kwargs):
        super().__init__(master, **kwargs)
        self.configure(corner_radius=8)

        self._title_label = ctk.CTkLabel(
            self, text=title, font=ctk.CTkFont(size=12),
            text_color=("gray50", "gray200"),
        )
        self._title_label.pack(pady=(12, 2), padx=16)

        self._value_label = ctk.CTkLabel(
            self, text=value, font=ctk.CTkFont(size=24, weight="bold"),
        )
        self._value_label.pack(pady=(2, 12), padx=16)

    def set_value(self, value: str) -> None:
        self._value_label.configure(text=value)


class RepoListItem(ctk.CTkFrame):
    """仓库列表项组件。"""

    def __init__(self, master, rank: int = 0, full_name: str = "",
                 stars_growth: int = 0, eval_score: float = 0,
                 language: str = "", **kwargs):
        super().__init__(master, **kwargs)
        self.configure(corner_radius=8)

        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill="x", padx=12, pady=8)

        rank_label = ctk.CTkLabel(
            row, text=f"{rank}.", font=ctk.CTkFont(size=14, weight="bold"),
            width=25,
        )
        rank_label.pack(side="left")

        name_label = ctk.CTkLabel(
            row, text=full_name, font=ctk.CTkFont(size=13),
            anchor="w",
        )
        name_label.pack(side="left", fill="x", expand=True, padx=(4, 8))

        if stars_growth > 0:
            growth_label = ctk.CTkLabel(
                row, text=f"⭐ +{stars_growth}",
                font=ctk.CTkFont(size=12),
                text_color=("#238636", "#3fb950"),
            )
            growth_label.pack(side="left", padx=4)

        score_label = ctk.CTkLabel(
            row, text=f"评分 {eval_score:.0f}",
            font=ctk.CTkFont(size=12),
            text_color=("#1F6FEB", "#58a6ff"),
        )
        score_label.pack(side="left", padx=4)

        if language:
            lang_label = ctk.CTkLabel(
                row, text=language, font=ctk.CTkFont(size=11),
                text_color=("gray50", "gray200"),
            )
            lang_label.pack(side="left", padx=4)


class RuleCard(ctk.CTkFrame):
    """规则卡片组件。"""

    def __init__(self, master, rule_data: dict | None = None, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(corner_radius=8)
        self._rule_data = rule_data or {}

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=12, pady=(10, 4))

        enabled = self._rule_data.get("enabled", True)
        status_color = ("#238636", "#3fb950") if enabled else ("#DA3633", "#f85149")
        status_text = "🟢" if enabled else "🔴"

        self._status_label = ctk.CTkLabel(
            header, text=status_text, font=ctk.CTkFont(size=14),
        )
        self._status_label.pack(side="left")

        self._name_label = ctk.CTkLabel(
            header, text=self._rule_data.get("name", ""),
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        self._name_label.pack(side="left", padx=8)

        btn_frame = ctk.CTkFrame(header, fg_color="transparent")
        btn_frame.pack(side="right")

        self._edit_btn = ctk.CTkButton(
            btn_frame, text="编辑", width=60, height=28,
            font=ctk.CTkFont(size=12),
        )
        self._edit_btn.pack(side="left", padx=2)

        self._delete_btn = ctk.CTkButton(
            btn_frame, text="删除", width=60, height=28,
            font=ctk.CTkFont(size=12),
            fg_color=("#DA3633", "#b62324"),
            hover_color=("#f85149", "#da3633"),
        )
        self._delete_btn.pack(side="left", padx=2)

        keywords = self._rule_data.get("keywords", [])
        if isinstance(keywords, list):
            kw_text = ", ".join(keywords)
        else:
            kw_text = str(keywords)
        self._keywords_label = ctk.CTkLabel(
            self, text=f"关键词: {kw_text}",
            font=ctk.CTkFont(size=12), anchor="w",
            text_color=("gray50", "gray200"),
        )
        self._keywords_label.pack(fill="x", padx=16, pady=1)

        topics = self._rule_data.get("topics", [])
        if isinstance(topics, list) and topics:
            topics_text = ", ".join(topics)
            self._topics_label = ctk.CTkLabel(
                self, text=f"主题: {topics_text}",
                font=ctk.CTkFont(size=12), anchor="w",
                text_color=("gray50", "gray200"),
            )
            self._topics_label.pack(fill="x", padx=16, pady=1)

        detail_frame = ctk.CTkFrame(self, fg_color="transparent")
        detail_frame.pack(fill="x", padx=16, pady=(1, 10))

        language = self._rule_data.get("language", "")
        if language:
            ctk.CTkLabel(
                detail_frame, text=f"语言: {language}",
                font=ctk.CTkFont(size=11),
                text_color=("gray50", "gray200"),
            ).pack(side="left")

        ctk.CTkLabel(
            detail_frame,
            text=f"优先级: {self._rule_data.get('priority', 5)}/10",
            font=ctk.CTkFont(size=11),
            text_color=("gray50", "gray200"),
        ).pack(side="left", padx=8)

    @property
    def edit_button(self) -> ctk.CTkButton:
        return self._edit_btn

    @property
    def delete_button(self) -> ctk.CTkButton:
        return self._delete_btn

    @property
    def rule_data(self) -> dict:
        return self._rule_data


class ProgressDialog(ctk.CTkToplevel):
    """进度对话框。"""

    def __init__(self, master, title: str = "执行中...", **kwargs):
        super().__init__(master, **kwargs)
        self.title(title)
        self.geometry("400x150")
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()

        self._label = ctk.CTkLabel(
            self, text="正在执行...", font=ctk.CTkFont(size=14),
        )
        self._label.pack(pady=(20, 10), padx=20)

        self._progress = ctk.CTkProgressBar(self, width=340)
        self._progress.pack(pady=(0, 20), padx=20)
        self._progress.set(0)

    def update_progress(self, step: str, current: int, total: int) -> None:
        """更新进度。"""
        self._label.configure(text=step)
        if total > 0:
            self._progress.set(current / total)

    def close(self) -> None:
        self.grab_release()
        self.destroy()


class MessageBox(ctk.CTkToplevel):
    """自定义消息弹窗（替代CTkMessagebox）。"""

    def __init__(self, master, title: str = "提示", message: str = "",
                 icon: str = "info", **kwargs):
        super().__init__(master, **kwargs)
        self.title(title)
        self.geometry("360x160")
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()

        icon_map = {"check": "✅", "cancel": "❌", "info": "ℹ️", "warning": "⚠️"}
        icon_text = icon_map.get(icon, "ℹ️")

        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=20, pady=(16, 8))

        ctk.CTkLabel(
            content, text=icon_text, font=ctk.CTkFont(size=28),
        ).pack(side="left", padx=(0, 16))

        ctk.CTkLabel(
            content, text=message, font=ctk.CTkFont(size=13),
            wraplength=250, justify="left",
        ).pack(side="left", fill="both", expand=True)

        ctk.CTkButton(
            self, text="确定", width=80, command=self._on_close,
        ).pack(pady=(0, 16))

    def _on_close(self) -> None:
        self.grab_release()
        self.destroy()
