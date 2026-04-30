import customtkinter as ctk

from gui.theme import (
    make_font,
    ACTION_BLUE, ACTION_BLUE_DARK, ERROR as RED,
    CARD_BG, BORDER, TEXT_PRIMARY, TEXT_SECONDARY, TEXT_HINT,
    FONT_BODY, FONT_CAPTION, FONT_BODY_EMPH, FONT_LABEL,
    CORNER_RADIUS_CARD, CORNER_RADIUS_BTN, CORNER_RADIUS_ENTRY,
    CORNER_RADIUS_SUBTLE, PAGE_BG,
    MEDIUM_FIELD_WIDTH, SHORT_FIELD_WIDTH,
    BTN_HEIGHT, BTN_HEIGHT_SM, ENTRY_HEIGHT,
)
from gui.components.widgets import (
    RuleCard, PrimaryButton, SecondaryButton, DangerButton, GhostButton,
    LanguageMultiSelect,
)
from service.rule_service import RuleService


class RulesPage(ctk.CTkScrollableFrame):
    def __init__(self, master, rule_svc: RuleService, **kwargs):
        super().__init__(master, fg_color=PAGE_BG, **kwargs)
        self._svc = rule_svc
        self._build_ui()

    def _build_ui(self) -> None:
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(16, 0))

        ctk.CTkLabel(
            header, text="\u63A8\u9001\u89C4\u5219",
            font=make_font(FONT_BODY_EMPH), text_color=TEXT_SECONDARY,
        ).pack(side="left")

        PrimaryButton(header, text="+ \u65B0\u5EFA\u89C4\u5219", width=110, height=BTN_HEIGHT_SM,
                      command=self._show_add_dialog).pack(side="right")

        self._rules_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._rules_frame.pack(fill="both", expand=True, padx=20, pady=(8, 16))

    def refresh(self) -> None:
        for widget in self._rules_frame.winfo_children():
            widget.destroy()

        rules = self._svc.get_rules()
        if not rules:
            ctk.CTkLabel(
                self._rules_frame,
                text="\u6682\u65E0\u89C4\u5219\uFF0C\u70B9\u51FB\u300C\u65B0\u5EFA\u89C4\u5219\u300D\u6DFB\u52A0",
                font=make_font(FONT_BODY), text_color=TEXT_HINT,
            ).pack(pady=40)
            return

        for rule in rules:
            card = RuleCard(self._rules_frame, rule_data=rule)
            card.pack(fill="x", pady=3)

            rule_id = rule.get("id")
            card.edit_button.configure(
                command=lambda rid=rule_id, rd=rule: self._show_edit_dialog(rid, rd)
            )
            card.delete_button.configure(
                command=lambda rid=rule_id: self._confirm_delete(rid)
            )

    def _show_add_dialog(self) -> None:
        self._show_rule_dialog("\u65B0\u5EFA\u89C4\u5219")

    def _show_edit_dialog(self, rule_id: int, rule_data: dict) -> None:
        self._show_rule_dialog("\u7F16\u8F91\u89C4\u5219", rule_id, rule_data)

    def _show_rule_dialog(self, title: str, rule_id: int | None = None,
                          rule_data: dict | None = None) -> None:
        dialog = ctk.CTkToplevel(self)
        dialog.title(title)
        dialog.geometry("440x560")
        dialog.resizable(False, False)
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()

        ctk.CTkLabel(dialog, text=title,
                     font=make_font(FONT_BODY_EMPH),
                     text_color=TEXT_PRIMARY).pack(pady=(16, 8))

        form = ctk.CTkScrollableFrame(dialog, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=20)

        def _add_field(label, placeholder="", default="", width=MEDIUM_FIELD_WIDTH):
            ctk.CTkLabel(form, text=label, font=make_font(FONT_LABEL), anchor="w",
                         text_color=TEXT_SECONDARY).pack(fill="x", pady=(6, 2))
            entry = ctk.CTkEntry(form, placeholder_text=placeholder, height=ENTRY_HEIGHT,
                                  width=width, corner_radius=CORNER_RADIUS_ENTRY)
            entry.pack(fill="x", pady=(0, 2))
            if default:
                entry.insert(0, str(default))
            return entry

        name_entry = _add_field("\u89C4\u5219\u540D\u79F0 *", "\u5982\uFF1AAI\u5927\u6A21\u578B\u6280\u80FD",
                                rule_data.get("name", "") if rule_data else "")
        keywords_entry = _add_field("\u5173\u952E\u8BCD *\uFF08\u9017\u53F7\u5206\u9694\uFF09", "\u5982\uFF1AAI, LLM, Agent",
                                    ", ".join(rule_data.get("keywords", [])) if rule_data else "")
        topics_entry = _add_field("GitHub\u4E3B\u9898\uFF08\u9017\u53F7\u5206\u9694\uFF09", "\u5982\uFF1Amachine-learning, nlp",
                                  ", ".join(rule_data.get("topics", [])) if rule_data and rule_data.get("topics") else "")

        ctk.CTkLabel(form, text="\u7F16\u7A0B\u8BED\u8A00", font=make_font(FONT_LABEL), anchor="w",
                     text_color=TEXT_SECONDARY).pack(fill="x", pady=(6, 2))
        lang_select = LanguageMultiSelect(form)
        lang_select.pack(fill="x", pady=(0, 2))
        if rule_data and rule_data.get("language"):
            lang_select.set(rule_data.get("language", ""))

        min_stars_entry = _add_field("\u6700\u4F4EStar\u6570", "0",
                                     str(rule_data.get("min_stars", 0)) if rule_data else "0",
                                     width=SHORT_FIELD_WIDTH)

        ctk.CTkLabel(form, text="\u4F18\u5148\u7EA7\uFF081-10\uFF09", font=make_font(FONT_LABEL), anchor="w",
                     text_color=TEXT_SECONDARY).pack(fill="x", pady=(6, 2))
        priority_frame = ctk.CTkFrame(form, fg_color="transparent")
        priority_frame.pack(fill="x", pady=(0, 2))

        priority_val = rule_data.get("priority", 5) if rule_data else 5
        priority_label = ctk.CTkLabel(priority_frame, text=str(priority_val),
                                       font=make_font(FONT_BODY_EMPH), text_color=ACTION_BLUE,
                                       width=24)
        priority_label.pack(side="left", padx=(0, 8))

        priority_slider = ctk.CTkSlider(priority_frame, from_=1, to=10, number_of_steps=9,
                                         width=200, button_color=ACTION_BLUE,
                                         button_hover_color=ACTION_BLUE_HOVER,
                                         progress_color=ACTION_BLUE)
        priority_slider.pack(side="left")
        priority_slider.set(priority_val)
        priority_slider.configure(command=lambda v: priority_label.configure(text=str(int(v))))

        enabled_var = ctk.BooleanVar(value=rule_data.get("enabled", True) if rule_data else True)
        ctk.CTkCheckBox(form, text="\u542F\u7528\u89C4\u5219", variable=enabled_var,
                        font=make_font(FONT_BODY), text_color=TEXT_PRIMARY,
                        checkbox_width=18, checkbox_height=18, corner_radius=3).pack(anchor="w", pady=6)

        error_label = ctk.CTkLabel(form, text="", font=make_font(FONT_CAPTION), text_color=RED)
        error_label.pack(fill="x", pady=(0, 4))

        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(pady=(8, 16))

        def on_cancel():
            dialog.grab_release()
            dialog.destroy()

        def on_save():
            name = name_entry.get().strip()
            keywords_text = keywords_entry.get().strip()
            if not name or not keywords_text:
                error_label.configure(text="\u89C4\u5219\u540D\u79F0\u548C\u5173\u952E\u8BCD\u4E0D\u80FD\u4E3A\u7A7A")
                return
            keywords = [k.strip() for k in keywords_text.split(",") if k.strip()]
            if not keywords:
                error_label.configure(text="\u5173\u952E\u8BCD\u4E0D\u80FD\u4E3A\u7A7A")
                return
            topics = [t.strip() for t in topics_entry.get().strip().split(",") if t.strip()]
            languages = lang_select.get()
            language = ", ".join(languages) if languages else ""
            min_stars_str = min_stars_entry.get().strip()
            min_stars = int(min_stars_str) if min_stars_str else 0
            priority = int(priority_slider.get())

            data = {
                "name": name,
                "keywords": keywords,
                "topics": topics,
                "language": language,
                "min_stars": min_stars,
                "priority": priority,
                "enabled": enabled_var.get(),
            }

            try:
                if rule_id:
                    self._svc.update_rule(rule_id, data)
                else:
                    self._svc.add_rule(data)
                self.refresh()
                dialog.grab_release()
                dialog.destroy()
            except Exception as e:
                error_label.configure(text=f"\u4FDD\u5B58\u5931\u8D25: {e}")

        SecondaryButton(btn_frame, text="\u53D6\u6D88", width=90,
                        command=on_cancel).pack(side="left", padx=6)
        PrimaryButton(btn_frame, text="\u4FDD\u5B58", width=90,
                      command=on_save).pack(side="left", padx=6)

    def _confirm_delete(self, rule_id: int) -> None:
        dialog = ctk.CTkToplevel(self)
        dialog.title("\u786E\u8BA4\u5220\u9664")
        dialog.geometry("300x140")
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()

        ctk.CTkLabel(dialog, text="\u786E\u5B9A\u8981\u5220\u9664\u6B64\u89C4\u5219\u5417\uFF1F",
                     font=make_font(FONT_BODY), text_color=TEXT_PRIMARY).pack(pady=(20, 12))

        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(pady=8)

        def on_cancel():
            dialog.grab_release()
            dialog.destroy()

        def on_delete():
            try:
                self._svc.delete_rule(rule_id)
                self.refresh()
            except Exception:
                pass
            dialog.grab_release()
            dialog.destroy()

        SecondaryButton(btn_frame, text="\u53D6\u6D88", width=72,
                        command=on_cancel).pack(side="left", padx=6)
        DangerButton(btn_frame, text="\u5220\u9664", width=72,
                     command=on_delete).pack(side="left", padx=6)
