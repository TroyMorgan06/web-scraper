#!/usr/bin/env python3
"""Desktop UI for the Universal Product Tracker."""

from __future__ import annotations

import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from app.config import DATA_DIR
from app.db import init_db, list_products
from app.export import export_history_csv
from app.tracker import check_product


class TrackerApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Universal Product Tracker")
        self.geometry("780x480")
        self.minsize(640, 360)

        init_db()
        self._busy = False
        self._build()
        self.refresh_list()

    def _build(self) -> None:
        pad = {"padx": 10, "pady": 6}

        header = ttk.Frame(self)
        header.pack(fill="x", **pad)
        ttk.Label(
            header,
            text="Universal Product Tracker",
            font=("Segoe UI", 14, "bold"),
        ).pack(anchor="w")
        ttk.Label(
            header,
            text="Paste a product URL to scrape title, price, and availability.",
        ).pack(anchor="w")

        frm = ttk.Frame(self)
        frm.pack(fill="x", **pad)
        ttk.Label(frm, text="Product URL").pack(anchor="w")

        row = ttk.Frame(frm)
        row.pack(fill="x", pady=(4, 0))
        self.url_var = tk.StringVar()
        self.url_entry = ttk.Entry(row, textvariable=self.url_var)
        self.url_entry.pack(side="left", fill="x", expand=True)
        self.url_entry.bind("<Return>", lambda _e: self.on_track())

        self.track_btn = ttk.Button(row, text="Track / refresh", command=self.on_track)
        self.track_btn.pack(side="left", padx=(8, 0))

        actions = ttk.Frame(self)
        actions.pack(fill="x", **pad)
        ttk.Button(actions, text="Refresh list", command=self.refresh_list).pack(
            side="left"
        )
        ttk.Button(actions, text="Export CSV…", command=self.on_export).pack(
            side="left", padx=(8, 0)
        )

        self.status_var = tk.StringVar(value="Ready.")
        ttk.Label(self, textvariable=self.status_var).pack(anchor="w", **pad)

        cols = ("id", "title", "price", "availability")
        tree_frame = ttk.Frame(self)
        tree_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.tree = ttk.Treeview(tree_frame, columns=cols, show="headings")
        self.tree.heading("id", text="ID")
        self.tree.heading("title", text="Title")
        self.tree.heading("price", text="Price")
        self.tree.heading("availability", text="Availability")
        self.tree.column("id", width=50, anchor="center", stretch=False)
        self.tree.column("title", width=340)
        self.tree.column("price", width=90, anchor="e", stretch=False)
        self.tree.column("availability", width=200)

        scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

    def refresh_list(self) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)
        for p in list_products():
            price = p["last_price"]
            self.tree.insert(
                "",
                "end",
                values=(
                    p["id"],
                    p["title"] or "(no title)",
                    f"${price}" if price is not None else "—",
                    p["availability"] or "—",
                ),
            )

    def on_track(self) -> None:
        if self._busy:
            return

        url = self.url_var.get().strip()
        if not url:
            messagebox.showwarning("Missing URL", "Please enter a product URL.")
            return

        self._set_busy(True, "Scraping… this may take a few seconds.")
        thread = threading.Thread(target=self._track_worker, args=(url,), daemon=True)
        thread.start()

    def _track_worker(self, url: str) -> None:
        try:
            result = check_product(url, send_alerts=False)
            product = result["product"]
            msg = f"Tracked: {product['title'] or url} — ${product['last_price']}"
            self.after(0, lambda: self._on_track_success(msg))
        except Exception as exc:  # noqa: BLE001
            err = str(exc)
            self.after(0, lambda: self._on_track_error(err))

    def _on_track_success(self, msg: str) -> None:
        self.status_var.set(msg)
        self.refresh_list()
        self._set_busy(False)

    def _on_track_error(self, err: str) -> None:
        self.status_var.set("Error.")
        self._set_busy(False)
        messagebox.showerror("Scrape failed", err)

    def on_export(self) -> None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        path = filedialog.asksaveasfilename(
            title="Export price history",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialdir=str(DATA_DIR),
            initialfile="history_export.csv",
        )
        if not path:
            return
        try:
            out = export_history_csv(path)
            self.status_var.set(f"Exported to {out}")
            messagebox.showinfo("Export complete", f"Saved to:\n{out}")
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Export failed", str(exc))

    def _set_busy(self, busy: bool, status: str | None = None) -> None:
        self._busy = busy
        state = "disabled" if busy else "normal"
        self.track_btn.config(state=state)
        self.url_entry.config(state=state)
        if status is not None:
            self.status_var.set(status)


def main() -> None:
    app = TrackerApp()
    app.mainloop()


if __name__ == "__main__":
    main()
