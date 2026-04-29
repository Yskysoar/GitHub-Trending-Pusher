import customtkinter as ctk

from gui.components.widgets import RuleCard
from service.rule_service import RuleService


class RulesPage(ctk.CTkScrollableFrame):
    """规则管理页面。

    提供规则列表展示、新建/编辑/删除/启禁用规则功能。
    """

    def __init__(self, master, rule_svc: RuleService, **kwargs):
        super().__init__(master, **kwargs)
        self._svc = rule_svc
        self._build_ui()

    def _build_ui(self) -> None:
        """构建UI。"""
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=16, pady=(16, 8))

        ctk.CTkLabel(
            header, text="推送规则",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).pack(side="left")

        ctk.CTkButton(
            header, text="➕ 新建规则",
            command=self._show_add_dialog,
        ).pack(side="right")

        self._rules_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._rules_frame.pack(fill="both", expand=True, padx=16, pady=(0, 16))

    def refresh(self) -> None:
        """刷新规则列表。"""
        for widget in self._rules_frame.winfo_children():
            widget.destroy()

        rules = self._svc.get_rules()
        if not rules:
            ctk.CTkLabel(
                self._rules_frame,
                text="暂无规则，点击右上角「新建规则」添加",
                font=ctk.CTkFont(size=13),
                text_color=("gray50", "gray200"),
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
        """显示新建规则弹窗。"""
        self._show_rule_dialog("新建规则")

    def _show_edit_dialog(self, rule_id: int, rule_data: dict) -> None:
        """显示编辑规则弹窗。"""
        self._show_rule_dialog("编辑规则", rule_id, rule_data)

    def _show_rule_dialog(self, title: str, rule_id: int | None = None,
                          rule_data: dict | None = None) -> None:
        """规则编辑弹窗。"""
        dialog = ctk.CTkToplevel(self)
        dialog.title(title)
        dialog.geometry("420x480")
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()

        ctk.CTkLabel(dialog, text=title, font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(16, 12))

        form = ctk.CTkFrame(dialog, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=20)

        ctk.CTkLabel(form, text="规则名称 *", font=ctk.CTkFont(size=12), anchor="w").pack(fill="x", pady=(4, 2))
        name_entry = ctk.CTkEntry(form, placeholder_text="如：AI大模型技能")
        name_entry.pack(fill="x", pady=(0, 8))
        if rule_data:
            name_entry.insert(0, rule_data.get("name", ""))

        ctk.CTkLabel(form, text="关键词 *（逗号分隔）", font=ctk.CTkFont(size=12), anchor="w").pack(fill="x", pady=(4, 2))
        keywords_entry = ctk.CTkEntry(form, placeholder_text="如：AI, LLM, Agent")
        keywords_entry.pack(fill="x", pady=(0, 8))
        if rule_data:
            kws = rule_data.get("keywords", [])
            if isinstance(kws, list):
                keywords_entry.insert(0, ", ".join(kws))

        ctk.CTkLabel(form, text="GitHub主题（逗号分隔）", font=ctk.CTkFont(size=12), anchor="w").pack(fill="x", pady=(4, 2))
        topics_entry = ctk.CTkEntry(form, placeholder_text="如：machine-learning, nlp")
        topics_entry.pack(fill="x", pady=(0, 8))
        if rule_data:
            tps = rule_data.get("topics", [])
            if isinstance(tps, list):
                topics_entry.insert(0, ", ".join(tps))

        ctk.CTkLabel(form, text="编程语言（留空不限）", font=ctk.CTkFont(size=12), anchor="w").pack(fill="x", pady=(4, 2))
        language_entry = ctk.CTkEntry(form, placeholder_text="如：Python")
        language_entry.pack(fill="x", pady=(0, 8))
        if rule_data:
            language_entry.insert(0, rule_data.get("language", ""))

        ctk.CTkLabel(form, text="最低Star数（0=使用全局配置）", font=ctk.CTkFont(size=12), anchor="w").pack(fill="x", pady=(4, 2))
        min_stars_entry = ctk.CTkEntry(form, placeholder_text="0")
        min_stars_entry.pack(fill="x", pady=(0, 8))
        if rule_data:
            min_stars_entry.insert(0, str(rule_data.get("min_stars", 0)))

        ctk.CTkLabel(form, text=f"优先级（1-10）", font=ctk.CTkFont(size=12), anchor="w").pack(fill="x", pady=(4, 2))
        priority_slider = ctk.CTkSlider(form, from_=1, to=10, number_of_steps=9)
        priority_slider.pack(fill="x", pady=(0, 4))
        priority_label = ctk.CTkLabel(form, text="5", font=ctk.CTkFont(size=12))
        priority_label.pack(anchor="w")
        priority_val = rule_data.get("priority", 5) if rule_data else 5
        priority_slider.set(priority_val)
        priority_slider.configure(command=lambda v: priority_label.configure(text=str(int(v))))

        enabled_var = ctk.BooleanVar(value=rule_data.get("enabled", True) if rule_data else True)
        ctk.CTkCheckBox(form, text="启用规则", variable=enabled_var).pack(anchor="w", pady=8)

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
                ctk.CTkLabel(dialog, text=f"保存失败: {e}", text_color="red").pack()

        ctk.CTkButton(btn_frame, text="取消", command=on_cancel, width=100,
                       fg_color="transparent", border_width=1).pack(side="left", padx=8)
        ctk.CTkButton(btn_frame, text="保存", command=on_save, width=100).pack(side="left", padx=8)

    def _confirm_delete(self, rule_id: int) -> None:
        """确认删除规则。"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("确认删除")
        dialog.geometry("300x140")
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()

        ctk.CTkLabel(dialog, text="确定要删除此规则吗？", font=ctk.CTkFont(size=14)).pack(pady=(20, 16))

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

        ctk.CTkButton(btn_frame, text="取消", command=on_cancel, width=80,
                       fg_color="transparent", border_width=1).pack(side="left", padx=8)
        ctk.CTkButton(btn_frame, text="删除", command=on_delete, width=80,
                       fg_color=("#DA3633", "#b62324")).pack(side="left", padx=8)
