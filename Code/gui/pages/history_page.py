import customtkinter as ctk

from service.history_service import HistoryService


class HistoryPage(ctk.CTkScrollableFrame):
    """历史记录页面。

    提供历史日志列表、搜索、查看/打开/删除功能。
    """

    def __init__(self, master, history_svc: HistoryService, **kwargs):
        super().__init__(master, **kwargs)
        self._svc = history_svc
        self._current_page = 1
        self._page_size = 10
        self._build_ui()

    def _build_ui(self) -> None:
        """构建UI。"""
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=16, pady=(16, 8))

        ctk.CTkLabel(
            header, text="历史记录",
            font=ctk.CTkFont(size=20, weight="bold"),
        ).pack(side="left")

        self._search_entry = ctk.CTkEntry(
            header, placeholder_text="🔍 搜索日志...", width=200,
        )
        self._search_entry.pack(side="right", padx=(8, 0))

        self._search_btn = ctk.CTkButton(
            header, text="搜索", width=60,
            command=self._on_search,
        )
        self._search_btn.pack(side="right")

        self._list_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._list_frame.pack(fill="both", expand=True, padx=16, pady=(0, 8))

        self._pagination_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._pagination_frame.pack(fill="x", padx=16, pady=(0, 16))

    def refresh(self) -> None:
        """刷新历史记录列表。"""
        self._load_page(self._current_page)

    def _load_page(self, page: int) -> None:
        """加载指定页的数据。"""
        self._current_page = page

        for widget in self._list_frame.winfo_children():
            widget.destroy()
        for widget in self._pagination_frame.winfo_children():
            widget.destroy()

        result = self._svc.get_summaries(page, self._page_size)
        items = result.get("items", [])
        total_pages = result.get("total_pages", 0)

        if not items:
            ctk.CTkLabel(
                self._list_frame,
                text="暂无历史记录",
                font=ctk.CTkFont(size=13),
                text_color=("gray50", "gray200"),
            ).pack(pady=40)
            return

        for item in items:
            row = ctk.CTkFrame(self._list_frame, corner_radius=8)
            row.pack(fill="x", pady=3)

            info_frame = ctk.CTkFrame(row, fg_color="transparent")
            info_frame.pack(fill="x", padx=12, pady=8)

            ctk.CTkLabel(
                info_frame,
                text=item.get("title", ""),
                font=ctk.CTkFont(size=13, weight="bold"),
            ).pack(side="left")

            ctk.CTkLabel(
                info_frame,
                text=f"📅 {item.get('generated_at', '')[:10]}  |  📊 {item.get('repo_count', 0)} 个项目",
                font=ctk.CTkFont(size=12),
                text_color=("gray50", "gray200"),
            ).pack(side="left", padx=12)

            btn_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
            btn_frame.pack(side="right")

            log_id = item.get("id")
            file_path = item.get("file_path", "")

            ctk.CTkButton(
                btn_frame, text="打开", width=50, height=26,
                font=ctk.CTkFont(size=11),
                command=lambda fp=file_path: self._svc.open_file(fp),
            ).pack(side="left", padx=2)

            ctk.CTkButton(
                btn_frame, text="删除", width=50, height=26,
                font=ctk.CTkFont(size=11),
                fg_color=("#DA3633", "#b62324"),
                command=lambda lid=log_id: self._confirm_delete(lid),
            ).pack(side="left", padx=2)

        if total_pages > 1:
            ctk.CTkButton(
                self._pagination_frame, text="◀ 上一页", width=90,
                command=lambda: self._load_page(max(1, page - 1)),
                state="normal" if page > 1 else "disabled",
            ).pack(side="left", padx=4)

            ctk.CTkLabel(
                self._pagination_frame,
                text=f"第 {page}/{total_pages} 页",
                font=ctk.CTkFont(size=12),
            ).pack(side="left", padx=8)

            ctk.CTkButton(
                self._pagination_frame, text="下一页 ▶", width=90,
                command=lambda: self._load_page(min(total_pages, page + 1)),
                state="normal" if page < total_pages else "disabled",
            ).pack(side="left", padx=4)

    def _on_search(self) -> None:
        """搜索日志。"""
        keyword = self._search_entry.get().strip()
        if not keyword:
            self._load_page(1)
            return

        for widget in self._list_frame.winfo_children():
            widget.destroy()
        for widget in self._pagination_frame.winfo_children():
            widget.destroy()

        result = self._svc.search_summaries(keyword, 1, self._page_size)
        items = result.get("items", [])

        if not items:
            ctk.CTkLabel(
                self._list_frame,
                text=f"未找到包含「{keyword}」的日志",
                font=ctk.CTkFont(size=13),
                text_color=("gray50", "gray200"),
            ).pack(pady=40)
            return

        for item in items:
            row = ctk.CTkFrame(self._list_frame, corner_radius=8)
            row.pack(fill="x", pady=3)

            info_frame = ctk.CTkFrame(row, fg_color="transparent")
            info_frame.pack(fill="x", padx=12, pady=8)

            ctk.CTkLabel(
                info_frame, text=item.get("title", ""),
                font=ctk.CTkFont(size=13, weight="bold"),
            ).pack(side="left")

            log_id = item.get("id")
            file_path = item.get("file_path", "")

            ctk.CTkButton(
                info_frame, text="打开", width=50, height=26,
                font=ctk.CTkFont(size=11),
                command=lambda fp=file_path: self._svc.open_file(fp),
            ).pack(side="right", padx=2)

    def _confirm_delete(self, log_id: int) -> None:
        """确认删除日志。"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("确认删除")
        dialog.geometry("300x140")
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()

        ctk.CTkLabel(dialog, text="确定要删除此日志吗？\n将同时删除磁盘上的日志文件。",
                     font=ctk.CTkFont(size=13)).pack(pady=(20, 16))

        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(pady=8)

        def on_cancel():
            dialog.grab_release()
            dialog.destroy()

        def on_delete():
            try:
                self._svc.delete_summary(log_id)
                self.refresh()
            except Exception:
                pass
            dialog.grab_release()
            dialog.destroy()

        ctk.CTkButton(btn_frame, text="取消", command=on_cancel, width=80,
                       fg_color="transparent", border_width=1).pack(side="left", padx=8)
        ctk.CTkButton(btn_frame, text="删除", command=on_delete, width=80,
                       fg_color=("#DA3633", "#b62324")).pack(side="left", padx=8)
