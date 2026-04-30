import customtkinter as ctk

from gui.theme import (
    make_font,
    SUCCESS, ACTION_BLUE,
    CARD_BG, BORDER, TEXT_PRIMARY, TEXT_SECONDARY, TEXT_HINT,
    FONT_BODY, FONT_CAPTION, FONT_BODY_EMPH,
    CORNER_RADIUS_CARD, PAGE_BG,
)
from service.history_service import HistoryService


class HistoryPage(ctk.CTkScrollableFrame):
    def __init__(self, master, history_svc: HistoryService, **kwargs):
        super().__init__(master, fg_color=PAGE_BG, **kwargs)
        self._svc = history_svc
        self._build_ui()

    def _build_ui(self) -> None:
        self._history_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._history_frame.pack(fill="both", expand=True, padx=20, pady=(16, 16))

    def refresh(self) -> None:
        for widget in self._history_frame.winfo_children():
            widget.destroy()

        records = self._svc.get_history()
        if not records:
            ctk.CTkLabel(
                self._history_frame,
                text="\u6682\u65E0\u5386\u53F2\u8BB0\u5F55",
                font=make_font(FONT_BODY), text_color=TEXT_HINT,
            ).pack(pady=40)
            return

        for record in records:
            self._add_record_card(record)

    def _add_record_card(self, record: dict) -> None:
        card = ctk.CTkFrame(
            self._history_frame, corner_radius=CORNER_RADIUS_CARD,
            border_width=1, border_color=BORDER,
        )
        card.pack(fill="x", pady=2)

        header = ctk.CTkFrame(card, fg_color="transparent")
        header.pack(fill="x", padx=12, pady=(8, 2))

        ctk.CTkLabel(
            header, text=record.get("date", ""),
            font=make_font(FONT_BODY), text_color=TEXT_PRIMARY,
        ).pack(side="left")

        status = record.get("status", "")
        status_color = SUCCESS if status == "success" else TEXT_HINT
        ctk.CTkLabel(
            header, text=status,
            font=make_font(FONT_CAPTION), text_color=status_color,
        ).pack(side="right")

        detail = ctk.CTkFrame(card, fg_color="transparent")
        detail.pack(fill="x", padx=12, pady=(0, 8))

        pushed = record.get("pushed_count", 0)
        ctk.CTkLabel(
            detail, text=f"\u63A8\u9001\u9879\u76EE: {pushed}",
            font=make_font(FONT_CAPTION), text_color=TEXT_SECONDARY,
        ).pack(side="left")

        repos = record.get("repos", [])
        if repos:
            repo_text = ", ".join(repos[:3])
            if len(repos) > 3:
                repo_text += f" \u7B49{len(repos)}\u9879"
            ctk.CTkLabel(
                detail, text=repo_text,
                font=make_font(FONT_CAPTION), text_color=TEXT_HINT,
            ).pack(side="left", padx=(10, 0))
