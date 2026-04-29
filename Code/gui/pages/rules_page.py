import customtkinter as ctk

from gui.theme import (
    make_font,
    PRIMARY, PRIMARY_DARK, ERROR as RED, ACCENT_RED,
    CARD_BG, BORDER, TEXT_PRIMARY, TEXT_SECONDARY, TEXT_HINT,
    FONT_BODY, FONT_CAPTION, FONT_ICON_MD, CORNER_RADIUS_CARD,
)
from gui.components.widgets import RuleCard, PageHeader, PageDivider
from service.rule_service import RuleService


class RulesPage(ctk.CTkScrollableFrame):
    """规则管理页面。"""

    def __init__(self, master, rule_svc: RuleService, **kwargs):
        super().__init__(master, **kwargs)
        self._svc = rule_svc
        self._build_ui()

    def _build_ui(self) -> None:
        header = PageHeader(self, "推送规则", "管理关键词匹配规则")
        ctk.CTkButton(
            header.right_frame, text="+ 新建规则", width=100, height=30,
            font=make_font(FONT_BODY), fg_color=PRIMARY_DARK, hover_color=PRIMARY,
            command=self._show_add_dialog,
        ).pack(side="right")
        PageDivider(self)

        self._rules_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._rules_frame.pack(fill="both", expand=True, padx=20, pady=(0, 16))

    def refresh(self) -> None:
        for widget in self._rules_frame.winfo_children():
            widget.destroy()

        rules = self._svc.get_rules()
        if not rules:
            ctk.CTkLabel(
                self._rules_frame,
                text="暂无规则，点击右上角「新建规则」添加",
                font=make_font(FONT_BODY), text_color=TEXT_HINT,
            ).pack(pady=40)
            return

        for rule in rules:
            card = RuleCard(self._rules_frame, rule_data=rule)
            card.pack(fill="x", pady=4)

            rule_id = rule.get("id")
            card.edit_button.configure(
                command=lambda rid=rule_id, rd=rule: self._show_edit_dialog(rid, rd)
            )
            card.delete_button.configure(
                command=lambda rid=rule_id: self._confirm_delete(rid)
            )

    def _show_add_dialog(self) -> None:
        self._show_rule_dialog("新建规则")

    def _show_edit_dialog(self, rule_id: int, rule_data: dict) -> None:
        self._show_rule_dialog("编辑规则", rule_id, rule_data)

    def _show_rule_dialog(self, title: str, rule_id: int | None = None,
                          rule_data: dict | None = None) -> None:
        dialog = ctk.CTkToplevel(self)
        dialog.title(title)
        dialog.geometry("420x480")
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()

        ctk.CTkLabel(dialog, text=title,
                     font=make_font(FONT_ICON_MD),
                     text_color=TEXT_PRIMARY).pack(pady=(16, 12))

        form = ctk.CTkFrame(dialog, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=20)

        def _add_field(label, placeholder="", default=""):
            ctk.CTkLabel(form, text=label, font=make_font(FONT_CAPTION), anchor="w",
                         text_color=TEXT_SECONDARY).pack(fill="x", pady=(4, 2))
            entry = ctk.CTkEntry(form, placeholder_text=placeholder, height=30)
            entry.pack(fill="x", pady=(0, 6))
            if default:
                entry.insert(0, default)
            return entry

        name_entry = _add_field("规则名称 *", "如：AI大模型技能",
                                rule_data.get("name", "") if rule_data else "")
        keywords_entry = _add_field("关键词 *（逗号分隔）", "如：AI, LLM, Agent",
                                    ", ".join(rule_data.get("keywords", [])) if rule_data else "")
        topics_entry = _add_field("GitHub主题（逗号分隔）", "如：machine-learning, nlp",
                                  ", ".join(rule_data.get("topics", [])) if rule_data and rule_data.get("topics") else "")
        language_entry = _add_field("编程语言（留空不限）", "如：Python",
                                    rule_data.get("language", "") if rule_data else "")
        min_stars_entry = _add_field("最低Star数（0=使用全局配置）", "0",
                                     str(rule_data.get("min_stars", 0)) if rule_data else "")

        ctk.CTkLabel(form, text="优先级（1-10）", font=make_font(FONT_CAPTION), anchor="w",
                     text_color=TEXT_SECONDARY).pack(fill="x", pady=(4, 2))
        priority_slider = ctk.CTkSlider(form, from_=1, to=10, number_of_steps=9)
        priority_slider.pack(fill="x", pady=(0, 4))
        priority_label = ctk.CTkLabel(form, text="5", font=make_font(FONT_CAPTION), text_color=TEXT_HINT)
        priority_label.pack(anchor="w")
        priority_val = rule_data.get("priority", 5) if rule_data else 5
        priority_slider.set(priority_val)
        priority_slider.configure(command=lambda v: priority_label.configure(text=str(int(v))))

        enabled_var = ctk.BooleanVar(value=rule_data.get("enabled", True) if rule_data else True)
        ctk.CTkCheckBox(form, text="启用规则", variable=enabled_var,
                        font=make_font(FONT_BODY), text_color=TEXT_PRIMARY).pack(anchor="w", pady=8)

        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(pady=12)

        def on_cancel():
            dialog.grab_release()
            dialog.destroy()

        def on_save():
            name = name_entry.get().strip()
            keywords_text = keywords_entry.get().strip()
            if not name or not keywords_text:
                return
            keywords = [k.strip() for k in keywords_text.split(",") if k.strip()]
            topics = [t.strip() for t in topics_entry.get().strip().split(",") if t.strip()]
            language = language_entry.get().strip()
            min_stars = int(min_stars_entry.get().strip() or "0")
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
                ctk.CTkLabel(dialog, text=f"保存失败: {e}", text_color=RED,
                             font=make_font(FONT_CAPTION)).pack()

        ctk.CTkButton(btn_frame, text="取消", command=on_cancel, width=100, height=30,
                       fg_color="transparent", border_width=1, border_color=BORDER,
                       text_color=TEXT_PRIMARY, font=make_font(FONT_BODY)).pack(side="left", padx=8)
        ctk.CTkButton(btn_frame, text="保存", command=on_save, width=100, height=30,
                       fg_color=PRIMARY_DARK, hover_color=PRIMARY,
                       font=make_font(FONT_BODY)).pack(side="left", padx=8)

    def _confirm_delete(self, rule_id: int) -> None:
        dialog = ctk.CTkToplevel(self)
        dialog.title("确认删除")
        dialog.geometry("300x140")
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()

        ctk.CTkLabel(dialog, text="确定要删除此规则吗？",
                     font=make_font(FONT_BODY), text_color=TEXT_PRIMARY).pack(pady=(20, 16))

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

        ctk.CTkButton(btn_frame, text="取消", command=on_cancel, width=80, height=30,
                       fg_color="transparent", border_width=1, border_color=BORDER,
                       text_color=TEXT_PRIMARY, font=make_font(FONT_BODY)).pack(side="left", padx=8)
        ctk.CTkButton(btn_frame, text="删除", command=on_delete, width=80, height=30,
                       fg_color=(ACCENT_RED, "#b62324"), hover_color=(RED, ACCENT_RED),
                       font=make_font(FONT_BODY)).pack(side="left", padx=8)
