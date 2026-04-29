import customtkinter as ctk

from gui.theme import (
    PRIMARY, PRIMARY_DARK, SUCCESS, ERROR, WARNING,
    CARD_BG, BORDER, TEXT_PRIMARY, TEXT_SECONDARY, TEXT_HINT,
    FONT_SECTION, FONT_BODY, FONT_CAPTION, FONT_STAT_VALUE, FONT_STAT_TITLE,
    CORNER_RADIUS_CARD, CORNER_RADIUS_BTN, ACCENT_GREEN, ACCENT_RED,
)


class SectionCard(ctk.CTkFrame):
    """分区卡片组件。"""

    def __init__(self, master, title: str = "", icon: str = "",
                 accent_color: str = PRIMARY, **kwargs):
        super().__init__(master, corner_radius=CORNER_RADIUS_CARD,
                         border_width=1, border_color=BORDER, **kwargs)

        header = ctk.CTkFrame(self, fg_color="transparent", height=32)
        header.pack(fill="x", padx=(16, 16), pady=(12, 0))
        header.pack_propagate(False)

        accent_bar = ctk.CTkFrame(header, width=3, fg_color=accent_color, corner_radius=2)
        accent_bar.pack(side="left", fill="y", padx=(0, 8))

        ctk.CTkLabel(
            header, text=f"{icon}  {title}" if icon else title,
            font=FONT_SECTION, text_color=TEXT_PRIMARY,
        ).pack(side="left")

        self._body = ctk.CTkFrame(self, fg_color="transparent")
        self._body.pack(fill="x", padx=16, pady=(8, 14))

    @property
    def body(self) -> ctk.CTkFrame:
        return self._body


class FieldRow(ctk.CTkFrame):
    """表单行：标签 + 控件区。"""

    def __init__(self, master, label: str = "", label_width: int = 120, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.pack(fill="x", pady=3)

        ctk.CTkLabel(
            self, text=label, font=FONT_BODY,
            text_color=TEXT_PRIMARY, width=label_width, anchor="w",
        ).pack(side="left")

        self._widget_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._widget_frame.pack(side="left", fill="x", expand=True)

    @property
    def widget_frame(self) -> ctk.CTkFrame:
        return self._widget_frame


class StatCard(ctk.CTkFrame):
    """统计卡片组件。"""

    def __init__(self, master, title: str = "", value: str = "0",
                 accent_color: str = PRIMARY, **kwargs):
        super().__init__(master, corner_radius=CORNER_RADIUS_CARD,
                         border_width=1, border_color=BORDER, **kwargs)

        top_bar = ctk.CTkFrame(self, height=3, fg_color=accent_color, corner_radius=2)
        top_bar.pack(fill="x", padx=12, pady=(0, 0))

        self._title_label = ctk.CTkLabel(
            self, text=title, font=FONT_STAT_TITLE,
            text_color=TEXT_SECONDARY,
        )
        self._title_label.pack(pady=(10, 2), padx=16)

        self._value_label = ctk.CTkLabel(
            self, text=value, font=FONT_STAT_VALUE,
            text_color=TEXT_PRIMARY,
        )
        self._value_label.pack(pady=(2, 12), padx=16)

    def set_value(self, value: str) -> None:
        self._value_label.configure(text=value)


class RepoListItem(ctk.CTkFrame):
    """仓库列表项组件。"""

    def __init__(self, master, rank: int = 0, full_name: str = "",
                 stars_growth: int = 0, eval_score: float = 0,
                 language: str = "", **kwargs):
        super().__init__(master, corner_radius=CORNER_RADIUS_CARD,
                         border_width=1, border_color=BORDER, **kwargs)

        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill="x", padx=12, pady=8)

        rank_label = ctk.CTkLabel(
            row, text=f"#{rank}", font=ctk.CTkFont(size=13, weight="bold"),
            text_color=PRIMARY, width=30,
        )
        rank_label.pack(side="left")

        name_label = ctk.CTkLabel(
            row, text=full_name, font=FONT_BODY, anchor="w",
            text_color=TEXT_PRIMARY,
        )
        name_label.pack(side="left", fill="x", expand=True, padx=(4, 8))

        if stars_growth > 0:
            growth_label = ctk.CTkLabel(
                row, text=f"+{stars_growth}",
                font=FONT_CAPTION,
                text_color=(ACCENT_GREEN, SUCCESS),
            )
            growth_label.pack(side="left", padx=4)

        score_label = ctk.CTkLabel(
            row, text=f"{eval_score:.0f}pts",
            font=FONT_CAPTION,
            text_color=(PRIMARY_DARK, PRIMARY),
        )
        score_label.pack(side="left", padx=4)

        if language:
            lang_label = ctk.CTkLabel(
                row, text=language, font=FONT_CAPTION,
                text_color=TEXT_SECONDARY,
            )
            lang_label.pack(side="left", padx=4)


class RuleCard(ctk.CTkFrame):
    """规则卡片组件。"""

    def __init__(self, master, rule_data: dict | None = None, **kwargs):
        super().__init__(master, corner_radius=CORNER_RADIUS_CARD,
                         border_width=1, border_color=BORDER, **kwargs)
        self._rule_data = rule_data or {}

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=12, pady=(10, 4))

        enabled = self._rule_data.get("enabled", True)
        status_dot = ctk.CTkLabel(
            header, text="\u25CF" if enabled else "\u25CB",
            font=ctk.CTkFont(size=14),
            text_color=SUCCESS if enabled else TEXT_HINT,
        )
        status_dot.pack(side="left")

        self._name_label = ctk.CTkLabel(
            header, text=self._rule_data.get("name", ""),
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=TEXT_PRIMARY,
        )
        self._name_label.pack(side="left", padx=8)

        btn_frame = ctk.CTkFrame(header, fg_color="transparent")
        btn_frame.pack(side="right")

        self._edit_btn = ctk.CTkButton(
            btn_frame, text="编辑", width=56, height=26,
            font=FONT_CAPTION, fg_color="transparent",
            border_width=1, border_color=BORDER,
            text_color=TEXT_PRIMARY, hover_color=CARD_BG,
        )
        self._edit_btn.pack(side="left", padx=2)

        self._delete_btn = ctk.CTkButton(
            btn_frame, text="删除", width=56, height=26,
            font=FONT_CAPTION,
            fg_color=(ACCENT_RED, "#b62324"),
            hover_color=(ERROR, ACCENT_RED),
        )
        self._delete_btn.pack(side="left", padx=2)

        keywords = self._rule_data.get("keywords", [])
        if isinstance(keywords, list):
            kw_text = ", ".join(keywords)
        else:
            kw_text = str(keywords)
        ctk.CTkLabel(
            self, text=f"关键词: {kw_text}",
            font=FONT_CAPTION, anchor="w", text_color=TEXT_SECONDARY,
        ).pack(fill="x", padx=16, pady=1)

        topics = self._rule_data.get("topics", [])
        if isinstance(topics, list) and topics:
            topics_text = ", ".join(topics)
            ctk.CTkLabel(
                self, text=f"主题: {topics_text}",
                font=FONT_CAPTION, anchor="w", text_color=TEXT_SECONDARY,
            ).pack(fill="x", padx=16, pady=1)

        detail_frame = ctk.CTkFrame(self, fg_color="transparent")
        detail_frame.pack(fill="x", padx=16, pady=(1, 10))

        language = self._rule_data.get("language", "")
        if language:
            ctk.CTkLabel(
                detail_frame, text=f"语言: {language}",
                font=FONT_CAPTION, text_color=TEXT_HINT,
            ).pack(side="left")

        ctk.CTkLabel(
            detail_frame,
            text=f"优先级: {self._rule_data.get('priority', 5)}/10",
            font=FONT_CAPTION, text_color=TEXT_HINT,
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
            self, text="正在执行...", font=FONT_BODY,
        )
        self._label.pack(pady=(20, 10), padx=20)

        self._progress = ctk.CTkProgressBar(self, width=340)
        self._progress.pack(pady=(0, 20), padx=20)
        self._progress.set(0)

    def update_progress(self, step: str, current: int, total: int) -> None:
        self._label.configure(text=step)
        if total > 0:
            self._progress.set(current / total)

    def close(self) -> None:
        self.grab_release()
        self.destroy()


class MessageBox(ctk.CTkToplevel):
    """自定义消息弹窗。"""

    def __init__(self, master, title: str = "提示", message: str = "",
                 icon: str = "info", **kwargs):
        super().__init__(master, **kwargs)
        self.title(title)
        self.geometry("360x160")
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()

        icon_map = {
            "check": ("\u2713", SUCCESS),
            "cancel": ("\u2717", ERROR),
            "info": ("i", PRIMARY),
            "warning": ("!", WARNING),
        }
        icon_text, icon_color = icon_map.get(icon, ("i", PRIMARY))

        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=20, pady=(16, 8))

        icon_frame = ctk.CTkFrame(content, width=36, height=36,
                                   corner_radius=18, fg_color=icon_color)
        icon_frame.pack(side="left", padx=(0, 16))
        icon_frame.pack_propagate(False)
        ctk.CTkLabel(
            icon_frame, text=icon_text,
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="white",
        ).pack(expand=True)

        ctk.CTkLabel(
            content, text=message, font=FONT_BODY,
            wraplength=250, justify="left",
            text_color=TEXT_PRIMARY,
        ).pack(side="left", fill="both", expand=True)

        ctk.CTkButton(
            self, text="确定", width=80, height=BTN_HEIGHT if False else 30,
            font=FONT_BODY, fg_color=PRIMARY_DARK, hover_color=PRIMARY,
            command=self._on_close,
        ).pack(pady=(0, 16))

    def _on_close(self) -> None:
        self.grab_release()
        self.destroy()


class PageHeader(ctk.CTkFrame):
    """页面标题栏。"""

    def __init__(self, master, title: str = "", subtitle: str = "", **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.pack(fill="x", padx=20, pady=(20, 4))

        ctk.CTkLabel(
            self, text=title,
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=TEXT_PRIMARY,
        ).pack(side="left")

        if subtitle:
            ctk.CTkLabel(
                self, text=subtitle,
                font=FONT_CAPTION, text_color=TEXT_SECONDARY,
            ).pack(side="left", padx=(12, 0), pady=(6, 0))

        self._right_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._right_frame.pack(side="right")

    @property
    def right_frame(self) -> ctk.CTkFrame:
        return self._right_frame


class PageDivider(ctk.CTkFrame):
    """页面分隔线。"""

    def __init__(self, master, **kwargs):
        super().__init__(master, height=2, fg_color=PRIMARY_DARK, **kwargs)
        self.pack(fill="x", padx=20, pady=(4, 14))
