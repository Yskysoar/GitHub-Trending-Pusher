import customtkinter as ctk

from gui.theme import (
    ACTION_BLUE, ACTION_BLUE_HOVER, ACTION_BLUE_DARK,
    SUCCESS, WARNING, ERROR, ERROR_LIGHT,
    CARD_BG, BORDER, BORDER_SUBTLE, HOVER_BG,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_HINT,
    ACCENT_TEAL, ACCENT_PURPLE, ACCENT_ORANGE,
    BRAND_DARK,
    FONT_PAGE_TITLE, FONT_SECTION, FONT_BODY, FONT_BODY_EMPH, FONT_CAPTION,
    FONT_STAT_VALUE, FONT_STAT_TITLE, FONT_LIST_TITLE, FONT_ICON_SM, FONT_ICON_MD,
    FONT_LABEL, FONT_BTN, FONT_BTN_BOLD,
    CORNER_RADIUS_CARD, CORNER_RADIUS_BTN, CORNER_RADIUS_ENTRY,
    CORNER_RADIUS_STANDARD, CORNER_RADIUS_SUBTLE,
    FORM_LABEL_WIDTH, SHORT_FIELD_WIDTH, MEDIUM_FIELD_WIDTH,
    BTN_HEIGHT, BTN_HEIGHT_SM, ENTRY_HEIGHT,
    BTN_PRIMARY_FG, BTN_PRIMARY_HOVER, BTN_PRIMARY_TEXT,
    BTN_SECONDARY_FG, BTN_SECONDARY_HOVER, BTN_SECONDARY_BORDER, BTN_SECONDARY_TEXT,
    BTN_DANGER_FG, BTN_DANGER_HOVER, BTN_DANGER_TEXT,
    BTN_GHOST_FG, BTN_GHOST_HOVER, BTN_GHOST_TEXT,
    GITHUB_LANGUAGES,
    make_font,
)


class PrimaryButton(ctk.CTkButton):
    def __init__(self, master, text: str = "", width: int = 100, height: int = BTN_HEIGHT,
                 command=None, **kwargs):
        super().__init__(
            master, text=text, width=width, height=height,
            font=make_font(FONT_BTN_BOLD), command=command,
            fg_color=BTN_PRIMARY_FG, hover_color=BTN_PRIMARY_HOVER,
            text_color=BTN_PRIMARY_TEXT,
            corner_radius=CORNER_RADIUS_BTN,
            border_width=0, **kwargs,
        )


class SecondaryButton(ctk.CTkButton):
    def __init__(self, master, text: str = "", width: int = 100, height: int = BTN_HEIGHT,
                 command=None, **kwargs):
        super().__init__(
            master, text=text, width=width, height=height,
            font=make_font(FONT_BTN), command=command,
            fg_color=BTN_SECONDARY_FG, hover_color=BTN_SECONDARY_HOVER,
            text_color=BTN_SECONDARY_TEXT,
            corner_radius=CORNER_RADIUS_BTN,
            border_width=1, border_color=BTN_SECONDARY_BORDER,
            **kwargs,
        )


class DangerButton(ctk.CTkButton):
    def __init__(self, master, text: str = "", width: int = 80, height: int = BTN_HEIGHT_SM,
                 command=None, **kwargs):
        super().__init__(
            master, text=text, width=width, height=height,
            font=make_font(FONT_BTN), command=command,
            fg_color=BTN_DANGER_FG, hover_color=BTN_DANGER_HOVER,
            text_color=BTN_DANGER_TEXT,
            corner_radius=CORNER_RADIUS_BTN,
            border_width=0, **kwargs,
        )


class GhostButton(ctk.CTkButton):
    def __init__(self, master, text: str = "", width: int = 80, height: int = BTN_HEIGHT_SM,
                 command=None, **kwargs):
        super().__init__(
            master, text=text, width=width, height=height,
            font=make_font(FONT_BTN), command=command,
            fg_color=BTN_GHOST_FG, hover_color=BTN_GHOST_HOVER,
            text_color=BTN_GHOST_TEXT,
            corner_radius=CORNER_RADIUS_BTN,
            border_width=0, **kwargs,
        )


class SectionCard(ctk.CTkFrame):
    def __init__(self, master, title: str = "", icon: str = "",
                 accent_color: str = ACTION_BLUE, **kwargs):
        super().__init__(master, corner_radius=CORNER_RADIUS_CARD,
                         border_width=1, border_color=BORDER, **kwargs)

        header = ctk.CTkFrame(self, fg_color="transparent", height=32)
        header.pack(fill="x", padx=(16, 16), pady=(12, 0))
        header.pack_propagate(False)

        accent_bar = ctk.CTkFrame(header, width=3, fg_color=accent_color,
                                   corner_radius=CORNER_RADIUS_SUBTLE)
        accent_bar.pack(side="left", fill="y", padx=(0, 8))

        ctk.CTkLabel(
            header, text=f"{icon}  {title}" if icon else title,
            font=make_font(FONT_SECTION), text_color=TEXT_PRIMARY,
        ).pack(side="left")

        self._body = ctk.CTkFrame(self, fg_color="transparent")
        self._body.pack(fill="x", padx=16, pady=(8, 14))

    @property
    def body(self) -> ctk.CTkFrame:
        return self._body


class FieldRow(ctk.CTkFrame):
    def __init__(self, master, label: str = "", label_width: int = FORM_LABEL_WIDTH,
                 hint: str = "", **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.pack(fill="x", pady=3)

        ctk.CTkLabel(
            self, text=label, font=make_font(FONT_LABEL),
            text_color=TEXT_SECONDARY, width=label_width, anchor="w",
        ).pack(side="left", pady=(6, 0))

        self._widget_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._widget_frame.pack(side="left", fill="x", expand=True)

        if hint:
            ctk.CTkLabel(
                self, text=hint, font=make_font(FONT_CAPTION),
                text_color=TEXT_HINT,
            ).pack(side="left", padx=(8, 0), pady=(6, 0))

    @property
    def widget_frame(self) -> ctk.CTkFrame:
        return self._widget_frame


class TimePicker(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        hours = [f"{h:02d}" for h in range(24)]
        minutes = [f"{m:02d}" for m in range(0, 60, 5)]

        self._hour_menu = ctk.CTkOptionMenu(
            self, values=hours, width=68, height=ENTRY_HEIGHT,
            fg_color=CARD_BG, button_color=ACTION_BLUE_DARK,
            button_hover_color=ACTION_BLUE, text_color=TEXT_PRIMARY,
            font=make_font(FONT_BODY),
            corner_radius=CORNER_RADIUS_ENTRY,
        )
        self._hour_menu.pack(side="left")

        ctk.CTkLabel(self, text=":", font=make_font(FONT_BODY),
                     text_color=TEXT_PRIMARY, width=12).pack(side="left")

        self._minute_menu = ctk.CTkOptionMenu(
            self, values=minutes, width=68, height=ENTRY_HEIGHT,
            fg_color=CARD_BG, button_color=ACTION_BLUE_DARK,
            button_hover_color=ACTION_BLUE, text_color=TEXT_PRIMARY,
            font=make_font(FONT_BODY),
            corner_radius=CORNER_RADIUS_ENTRY,
        )
        self._minute_menu.pack(side="left")

    def get(self) -> str:
        return f"{self._hour_menu.get()}:{self._minute_menu.get()}"

    def set(self, time_str: str) -> None:
        try:
            parts = time_str.split(":")
            hour = parts[0].strip()
            minute = parts[1].strip() if len(parts) > 1 else "00"
            self._hour_menu.set(hour)
            self._minute_menu.set(minute)
        except (ValueError, IndexError):
            self._hour_menu.set("09")
            self._minute_menu.set("00")

    def configure_command(self, command):
        self._hour_menu.configure(command=lambda v: command())
        self._minute_menu.configure(command=lambda v: command())


class LanguageMultiSelect(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self._selected: list[str] = []

        self._display = ctk.CTkEntry(
            self, height=ENTRY_HEIGHT, width=MEDIUM_FIELD_WIDTH,
            placeholder_text="\u70B9\u51FB\u9009\u62E9\u7F16\u7A0B\u8BED\u8A00",
            font=make_font(FONT_BODY), state="readonly",
            corner_radius=CORNER_RADIUS_ENTRY,
        )
        self._display.pack(side="left")

        self._dropdown_open = False
        self._dropdown_win = None

        self._display.bind("<Button-1>", lambda e: self._toggle_dropdown())

    def _toggle_dropdown(self) -> None:
        if self._dropdown_open and self._dropdown_win:
            self._close_dropdown()
        else:
            self._open_dropdown()

    def _open_dropdown(self) -> None:
        self._dropdown_open = True
        self._dropdown_win = ctk.CTkToplevel(self)
        self._dropdown_win.overrideredirect(True)
        self._dropdown_win.attributes("-topmost", True)
        self._dropdown_win.focus_force()

        x = self._display.winfo_rootx()
        y = self._display.winfo_rooty() + self._display.winfo_height()
        self._dropdown_win.geometry(f"+{x}+{y}")

        scroll = ctk.CTkScrollableFrame(
            self._dropdown_win, width=MEDIUM_FIELD_WIDTH, height=200,
            fg_color=CARD_BG, corner_radius=CORNER_RADIUS_CARD,
        )
        scroll.pack()

        self._lang_vars: dict[str, ctk.BooleanVar] = {}
        for lang in GITHUB_LANGUAGES:
            var = ctk.BooleanVar(value=lang in self._selected)
            self._lang_vars[lang] = var
            cb = ctk.CTkCheckBox(
                scroll, text=lang, variable=var,
                font=make_font(FONT_BODY), text_color=TEXT_PRIMARY,
                checkbox_width=18, checkbox_height=18,
                corner_radius=CORNER_RADIUS_SUBTLE,
                command=lambda l=lang: self._on_toggle(l),
            )
            cb.pack(fill="x", padx=8, pady=2)

        self._dropdown_win.bind("<FocusOut>", lambda e: self._close_dropdown())
        self._dropdown_win.bind("<Escape>", lambda e: self._close_dropdown())

    def _close_dropdown(self) -> None:
        self._dropdown_open = False
        if self._dropdown_win:
            try:
                self._dropdown_win.destroy()
            except Exception:
                pass
            self._dropdown_win = None

    def _on_toggle(self, lang: str) -> None:
        var = self._lang_vars.get(lang)
        if var and var.get():
            if lang not in self._selected:
                self._selected.append(lang)
        else:
            if lang in self._selected:
                self._selected.remove(lang)
        self._update_display()

    def _update_display(self) -> None:
        self._display.configure(state="normal")
        self._display.delete(0, "end")
        self._display.insert(0, ", ".join(self._selected))
        self._display.configure(state="readonly")

    def get(self) -> list[str]:
        return self._selected

    def set(self, languages: list[str] | str) -> None:
        if isinstance(languages, str):
            languages = [l.strip() for l in languages.split(",") if l.strip()]
        self._selected = [l for l in languages if l]
        self._update_display()


class SaveIndicator(ctk.CTkLabel):
    def __init__(self, master, **kwargs):
        super().__init__(master, text="", font=make_font(FONT_CAPTION),
                         text_color=SUCCESS, **kwargs)
        self._timer = None

    def show_saved(self) -> None:
        self.configure(text="\u2713 \u5DF2\u81EA\u52A8\u4FDD\u5B58", text_color=SUCCESS)
        if self._timer:
            self.after_cancel(self._timer)
        self._timer = self.after(2000, lambda: self.configure(text=""))

    def show_error(self, msg: str = "\u4FDD\u5B58\u5931\u8D25") -> None:
        self.configure(text=msg, text_color=ERROR)
        if self._timer:
            self.after_cancel(self._timer)
        self._timer = self.after(3000, lambda: self.configure(text=""))


class StatCard(ctk.CTkFrame):
    def __init__(self, master, title: str = "", value: str = "0",
                 accent_color: str = ACTION_BLUE, **kwargs):
        super().__init__(master, corner_radius=CORNER_RADIUS_CARD,
                         border_width=1, border_color=BORDER, **kwargs)

        top_bar = ctk.CTkFrame(self, height=3, fg_color=accent_color,
                                corner_radius=CORNER_RADIUS_SUBTLE)
        top_bar.pack(fill="x", padx=0, pady=(0, 0))

        self._title_label = ctk.CTkLabel(
            self, text=title, font=make_font(FONT_STAT_TITLE),
            text_color=TEXT_SECONDARY,
        )
        self._title_label.pack(pady=(10, 2), padx=16)

        self._value_label = ctk.CTkLabel(
            self, text=value, font=make_font(FONT_STAT_VALUE),
            text_color=TEXT_PRIMARY,
        )
        self._value_label.pack(pady=(0, 12), padx=16)

    def set_value(self, value: str) -> None:
        self._value_label.configure(text=value)


class TagLabel(ctk.CTkFrame):
    def __init__(self, master, text: str = "", color: str = ACTION_BLUE, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        bg_light, bg_dark = self._make_tinted_pair(color, 0.12)
        inner = ctk.CTkFrame(
            self, fg_color=(bg_light, bg_dark),
            corner_radius=CORNER_RADIUS_SUBTLE,
        )
        inner.pack(padx=1, pady=1)
        ctk.CTkLabel(
            inner, text=text, font=make_font(FONT_CAPTION),
            text_color=color, padx=6, pady=2,
        ).pack()

    @staticmethod
    def _make_tinted_pair(hex_color: str, alpha: float) -> tuple[str, str]:
        hex_color = hex_color.lstrip("#")
        r, g, b = (int(hex_color[i:i + 2], 16) for i in (0, 2, 4))
        lr = int(r * alpha + 241 * (1 - alpha))
        lg = int(g * alpha + 242 * (1 - alpha))
        lb = int(b * alpha + 243 * (1 - alpha))
        dr = int(r * alpha + 13 * (1 - alpha))
        dg = int(g * alpha + 14 * (1 - alpha))
        db = int(b * alpha + 18 * (1 - alpha))
        return f"#{lr:02x}{lg:02x}{lb:02x}", f"#{dr:02x}{dg:02x}{db:02x}"


class RepoListItem(ctk.CTkFrame):
    def __init__(self, master, rank: int = 0, full_name: str = "",
                 stars_growth: int = 0, eval_score: float = 0,
                 language: str = "", **kwargs):
        super().__init__(master, corner_radius=CORNER_RADIUS_CARD,
                         border_width=1, border_color=BORDER, **kwargs)

        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill="x", padx=12, pady=8)

        ctk.CTkLabel(
            row, text=str(rank), font=make_font(FONT_BODY_EMPH),
            text_color=ACTION_BLUE, width=24,
        ).pack(side="left")

        ctk.CTkLabel(
            row, text=full_name, font=make_font(FONT_BODY), anchor="w",
            text_color=TEXT_PRIMARY,
        ).pack(side="left", fill="x", expand=True, padx=(4, 8))

        if stars_growth > 0:
            TagLabel(row, f"+{stars_growth}", color=SUCCESS).pack(side="left", padx=2)

        TagLabel(row, f"{eval_score:.0f}pts", color=ACTION_BLUE).pack(side="left", padx=2)

        if language:
            TagLabel(row, language, color=ACCENT_PURPLE).pack(side="left", padx=2)


class RuleCard(ctk.CTkFrame):
    def __init__(self, master, rule_data: dict | None = None, **kwargs):
        super().__init__(master, corner_radius=CORNER_RADIUS_CARD,
                         border_width=1, border_color=BORDER, **kwargs)
        self._rule_data = rule_data or {}

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=12, pady=(10, 4))

        enabled = self._rule_data.get("enabled", True)
        ctk.CTkLabel(
            header, text="\u25CF" if enabled else "\u25CB",
            font=make_font(FONT_ICON_SM),
            text_color=SUCCESS if enabled else TEXT_HINT,
        ).pack(side="left")

        ctk.CTkLabel(
            header, text=self._rule_data.get("name", ""),
            font=make_font(FONT_LIST_TITLE),
            text_color=TEXT_PRIMARY,
        ).pack(side="left", padx=8)

        btn_frame = ctk.CTkFrame(header, fg_color="transparent")
        btn_frame.pack(side="right")

        self._edit_btn = GhostButton(btn_frame, text="\u7F16\u8F91",
                                      command=None)
        self._edit_btn.pack(side="left", padx=2)

        self._delete_btn = DangerButton(btn_frame, text="\u5220\u9664",
                                         command=None)
        self._delete_btn.pack(side="left", padx=2)

        tags_frame = ctk.CTkFrame(self, fg_color="transparent")
        tags_frame.pack(fill="x", padx=12, pady=(0, 4))

        keywords = self._rule_data.get("keywords", [])
        if isinstance(keywords, list):
            for kw in keywords[:4]:
                TagLabel(tags_frame, kw, color=ACTION_BLUE).pack(side="left", padx=2)

        detail_frame = ctk.CTkFrame(self, fg_color="transparent")
        detail_frame.pack(fill="x", padx=12, pady=(0, 10))

        language = self._rule_data.get("language", "")
        if language:
            ctk.CTkLabel(
                detail_frame, text=language, font=make_font(FONT_CAPTION),
                text_color=TEXT_HINT,
            ).pack(side="left")

        ctk.CTkLabel(
            detail_frame,
            text=f"P{self._rule_data.get('priority', 5)}",
            font=make_font(FONT_CAPTION), text_color=TEXT_HINT,
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


class MessageBox(ctk.CTkToplevel):
    def __init__(self, master, title: str = "\u63D0\u793A", message: str = "",
                 icon: str = "info", **kwargs):
        super().__init__(master, **kwargs)
        self.title(title)
        self.geometry("360x150")
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()

        icon_map = {
            "check": ("\u2713", SUCCESS),
            "cancel": ("\u2717", ERROR),
            "info": ("i", ACTION_BLUE),
            "warning": ("!", WARNING),
        }
        icon_text, icon_color = icon_map.get(icon, ("i", ACTION_BLUE))

        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=20, pady=(16, 8))

        icon_frame = ctk.CTkFrame(content, width=32, height=32,
                                   corner_radius=16, fg_color=icon_color)
        icon_frame.pack(side="left", padx=(0, 14))
        icon_frame.pack_propagate(False)
        ctk.CTkLabel(
            icon_frame, text=icon_text,
            font=make_font(FONT_ICON_MD), text_color="white",
        ).pack(expand=True)

        ctk.CTkLabel(
            content, text=message, font=make_font(FONT_BODY),
            wraplength=240, justify="left", text_color=TEXT_PRIMARY,
        ).pack(side="left", fill="both", expand=True)

        PrimaryButton(self, text="\u786E\u5B9A", width=80, height=BTN_HEIGHT_SM,
                      command=self._on_close).pack(pady=(0, 14))

    def _on_close(self) -> None:
        self.grab_release()
        self.destroy()


class PageHeader(ctk.CTkFrame):
    def __init__(self, master, title: str = "", subtitle: str = "", **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        ctk.CTkLabel(
            self, text=title,
            font=make_font(FONT_PAGE_TITLE),
            text_color=TEXT_PRIMARY,
        ).pack(side="left")

        if subtitle:
            ctk.CTkLabel(
                self, text=subtitle,
                font=make_font(FONT_CAPTION), text_color=TEXT_SECONDARY,
            ).pack(side="left", padx=(10, 0), pady=(4, 0))

        self._right_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._right_frame.pack(side="right")

    @property
    def right_frame(self) -> ctk.CTkFrame:
        return self._right_frame


class PageDivider(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, height=1, fg_color=BORDER, **kwargs)
        self.pack(fill="x", pady=(0, 12))
