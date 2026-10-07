"""Окно приложения (Tkinter). Работает только через BudgetService."""
import tkinter as tk
from datetime import datetime
from tkinter import ttk, messagebox

from models import DATE_FMT, INCOME, EXPENSE, Operation
from service import ALL, BudgetService, parse_amount, parse_date, money

CATEGORIES = ["Поступления", "Питание", "Транспорт", "Книги", "Развлечения", "Другое"]

# Цвета в стиле макета
BG = "#ffffff"
TEXT = "#1f2a44"
MUTED = "#6b7a90"
BORDER = "#d9e0ea"
TEAL = "#2f7f86"
TEAL_DARK = "#276a70"
GREEN, GREEN_BG = "#2f7d57", "#eaf5ef"
ORANGE, ORANGE_BG = "#c06a1f", "#fdf0e6"
BLUE, BLUE_BG = "#3558a8", "#e8eefb"
STRIPE = "#f6f8fb"
HEADER_BG = "#eef1f6"


def fix_treeview_tags(style: ttk.Style) -> None:
    """Обход бага Tk 8.6.9: без этого цвета строк Treeview не отображаются."""
    def fixed_map(option):
        return [e for e in style.map("Treeview", query_opt=option)
                if e[:2] != ("!disabled", "!selected")]
    style.map("Treeview",
              foreground=fixed_map("foreground"),
              background=fixed_map("background"))


class App(tk.Tk):
    def __init__(self, service: BudgetService):
        super().__init__()
        self.service = service
        self.editing_id: str | None = None

        self.title("Мой бюджет")
        self.geometry("1020x600")
        self.minsize(900, 520)
        self.configure(bg=BG)

        self.month_var = tk.StringVar(value=ALL)
        self.kind_var = tk.StringVar(value=ALL)
        self.type_var = tk.StringVar(value=EXPENSE)
        self.category_var = tk.StringVar(value=CATEGORIES[1])
        self.amount_var = tk.StringVar()
        self.date_var = tk.StringVar(value=datetime.now().strftime(DATE_FMT))
        self.comment_var = tk.StringVar()
        self.income_var = tk.StringVar()
        self.expense_var = tk.StringVar()
        self.balance_var = tk.StringVar()

        self._setup_style()
        self._build_header()
        self._build_summary()
        self._build_body()
        self.refresh()

    # --- стили ---
    def _setup_style(self):
        s = ttk.Style(self)
        s.theme_use("clam")  # одинаково красиво на Windows / macOS / Linux
        s.configure(".", background=BG, foreground=TEXT, font=("Segoe UI", 10))
        s.configure("TFrame", background=BG)
        s.configure("TLabel", background=BG, foreground=TEXT)
        s.configure("Muted.TLabel", foreground=MUTED)
        s.configure("H2.TLabel", font=("Segoe UI", 13, "bold"))
        s.configure("TEntry", fieldbackground=BG, bordercolor=BORDER,
                    lightcolor=BORDER, darkcolor=BORDER, padding=5)
        s.configure("TCombobox", fieldbackground=BG, bordercolor=BORDER,
                    lightcolor=BORDER, darkcolor=BORDER, padding=5)
        s.map("TCombobox", fieldbackground=[("readonly", BG)])

        s.configure("TButton", background=BG, bordercolor=BORDER,
                    lightcolor=BG, darkcolor=BG, padding=(14, 7))
        s.map("TButton", background=[("active", STRIPE)])
        s.configure("Accent.TButton", background=TEAL, foreground="#ffffff",
                    bordercolor=TEAL, lightcolor=TEAL, darkcolor=TEAL,
                    font=("Segoe UI", 10, "bold"))
        s.map("Accent.TButton", background=[("active", TEAL_DARK)])

        s.configure("Treeview", background=BG, fieldbackground=BG,
                    foreground=TEXT, rowheight=30, bordercolor=BORDER,
                    borderwidth=0)
        s.configure("Treeview.Heading", background=HEADER_BG, foreground=MUTED,
                    font=("Segoe UI", 9, "bold"), relief="flat", padding=6)
        s.map("Treeview", background=[("selected", "#d6e4f7")],
              foreground=[("selected", TEXT)])
        fix_treeview_tags(s)

    # --- построение окна ---
    def _build_header(self):
        head = ttk.Frame(self, padding=(16, 14, 16, 0))
        head.pack(fill="x")
        ttk.Label(head, text="Мой бюджет",
                  font=("Segoe UI", 20, "bold")).pack(anchor="w")
        ttk.Label(head, text="Доходы и расходы", style="Muted.TLabel").pack(anchor="w")

    def _build_summary(self):
        bar = ttk.Frame(self, padding=(16, 12, 16, 8))
        bar.pack(fill="x")
        for title, var, fg, bg in [("Доходы", self.income_var, GREEN, GREEN_BG),
                                   ("Расходы", self.expense_var, ORANGE, ORANGE_BG),
                                   ("Остаток", self.balance_var, BLUE, BLUE_BG)]:
            card = tk.Frame(bar, bg=bg, padx=14, pady=10)
            card.pack(side="left", expand=True, fill="x", padx=(0, 10))
            tk.Label(card, text=title, bg=bg, fg=MUTED,
                     font=("Segoe UI", 9)).pack(anchor="w")
            tk.Label(card, textvariable=var, bg=bg, fg=fg,
                     font=("Segoe UI", 16, "bold")).pack(anchor="w")

    def _build_body(self):
        body = ttk.Frame(self, padding=(16, 4, 16, 14))
        body.pack(fill="both", expand=True)

        # левая часть: фильтры + таблица + кнопки
        left = ttk.Frame(body)
        left.pack(side="left", fill="both", expand=True)

        filters = ttk.Frame(left)
        filters.pack(fill="x", pady=(0, 8))
        ttk.Label(filters, text="Операции", style="H2.TLabel").pack(side="left")
        kind_box = ttk.Combobox(
            filters, textvariable=self.kind_var, state="readonly", width=9,
            values=[ALL, INCOME, EXPENSE])
        kind_box.pack(side="right")
        ttk.Label(filters, text="Тип:", style="Muted.TLabel").pack(side="right", padx=(0, 5))
        self.month_box = ttk.Combobox(
            filters, textvariable=self.month_var, state="readonly", width=9)
        self.month_box.pack(side="right", padx=(0, 12))
        ttk.Label(filters, text="Период:", style="Muted.TLabel").pack(side="right", padx=(0, 5))
        self.month_box.bind("<<ComboboxSelected>>", lambda e: self.refresh())
        kind_box.bind("<<ComboboxSelected>>", lambda e: self.refresh())

        columns = ("date", "comment", "category", "kind", "amount")
        self.tree = ttk.Treeview(left, columns=columns, show="headings",
                                 selectmode="browse")
        for col, text, width, anchor in [("date", "Дата", 90, "w"),
                                         ("comment", "Комментарий", 190, "w"),
                                         ("category", "Категория", 110, "w"),
                                         ("kind", "Тип", 70, "w"),
                                         ("amount", "Сумма", 110, "e")]:
            self.tree.heading(col, text=text, anchor=anchor)
            self.tree.column(col, width=width, anchor=anchor)
        self.tree.tag_configure("income", foreground=GREEN)
        self.tree.tag_configure("expense", foreground=ORANGE)
        self.tree.tag_configure("stripe", background=STRIPE)
        self.tree.pack(fill="both", expand=True)

        buttons = ttk.Frame(left)
        buttons.pack(fill="x", pady=(10, 0))
        ttk.Button(buttons, text="Изменить",
                   command=self.start_edit).pack(side="left")
        ttk.Button(buttons, text="Удалить",
                   command=self.delete_selected).pack(side="left", padx=8)

        # правая часть: форма
        form = tk.Frame(body, bg=BG, highlightbackground=BORDER,
                        highlightthickness=1, padx=14, pady=12)
        form.pack(side="right", fill="y", padx=(16, 0))
        self.form_title = ttk.Label(form, text="Новая операция", style="H2.TLabel")
        self.form_title.pack(anchor="w", pady=(0, 8))

        def row(label, widget):
            ttk.Label(form, text=label, style="Muted.TLabel").pack(anchor="w")
            widget.pack(fill="x", pady=(2, 10))

        row("Тип операции", ttk.Combobox(
            form, textvariable=self.type_var, state="readonly",
            values=[INCOME, EXPENSE]))
        row("Категория", ttk.Combobox(
            form, textvariable=self.category_var, values=CATEGORIES))
        row("Сумма, ₸", ttk.Entry(form, textvariable=self.amount_var))
        row("Дата", ttk.Entry(form, textvariable=self.date_var))
        row("Комментарий", ttk.Entry(form, textvariable=self.comment_var))

        self.submit_btn = ttk.Button(form, text="Добавить операцию",
                                     style="Accent.TButton", command=self.submit)
        self.submit_btn.pack(fill="x", pady=(4, 0))
        self.cancel_btn = ttk.Button(form, text="Отмена", command=self.reset_form)

    # --- обновление экрана ---
    def refresh(self):
        months = [ALL] + self.service.months()
        self.month_box["values"] = months
        if self.month_var.get() not in months:
            self.month_var.set(ALL)

        ops = self.service.filtered(self.month_var.get(), self.kind_var.get())
        self.tree.delete(*self.tree.get_children())
        for i, op in enumerate(ops):
            sign = "+" if op.kind == INCOME else "−"
            tags = ["income" if op.kind == INCOME else "expense"]
            if i % 2:
                tags.append("stripe")
            self.tree.insert("", "end", iid=op.id, tags=tags, values=(
                op.date, op.comment, op.category, op.kind,
                f"{sign}{money(op.value)}"))

        # итоги считаются по выбранному периоду
        period_ops = self.service.filtered(self.month_var.get())
        income, expense, balance = self.service.totals(period_ops)
        self.income_var.set(money(income))
        self.expense_var.set(money(expense))
        self.balance_var.set(money(balance))

    def reset_form(self):
        self.editing_id = None
        self.form_title.config(text="Новая операция")
        self.submit_btn.config(text="Добавить операцию")
        self.cancel_btn.pack_forget()
        self.amount_var.set("")
        self.comment_var.set("")
        self.date_var.set(datetime.now().strftime(DATE_FMT))

    # --- действия ---
    def read_form(self) -> Operation | None:
        try:
            amount = parse_amount(self.amount_var.get())
            date = parse_date(self.date_var.get())
        except ValueError as e:
            messagebox.showerror("Ошибка ввода", str(e))
            return None
        return Operation(
            date=date, amount=str(amount),
            category=self.category_var.get().strip() or "Другое",
            comment=self.comment_var.get().strip(),
            kind=self.type_var.get())

    def submit(self):
        op = self.read_form()
        if op is None:
            return
        if self.editing_id:
            self.service.update(self.editing_id, op)
        else:
            self.service.add(op)
        self.reset_form()
        self.refresh()

    def selected_id(self) -> str | None:
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Мой бюджет", "Сначала выберите запись в таблице")
            return None
        return sel[0]

    def start_edit(self):
        op_id = self.selected_id()
        op = self.service.get(op_id) if op_id else None
        if op is None:
            return
        self.editing_id = op.id
        self.type_var.set(op.kind)
        self.category_var.set(op.category)
        self.amount_var.set(op.amount)
        self.date_var.set(op.date)
        self.comment_var.set(op.comment)
        self.form_title.config(text="Редактирование")
        self.submit_btn.config(text="Сохранить изменения")
        self.cancel_btn.pack(fill="x", pady=(6, 0))

    def delete_selected(self):
        op_id = self.selected_id()
        if op_id and messagebox.askyesno("Удаление", "Удалить выбранную операцию?"):
            self.service.delete(op_id)
            if self.editing_id == op_id:
                self.reset_form()
            self.refresh()
