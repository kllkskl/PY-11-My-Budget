"""Бизнес-логика: операции, фильтры, итоги, проверка ввода."""
from datetime import datetime
from decimal import Decimal, InvalidOperation

from models import DATE_FMT, INCOME, EXPENSE, Operation
from storage import Storage

ALL = "Все"


class BudgetService:
    def __init__(self, storage: Storage):
        self.storage = storage
        self.operations = storage.load()

    def add(self, op: Operation) -> None:
        self.operations.append(op)
        self.storage.save(self.operations)

    def update(self, op_id: str, new: Operation) -> None:
        for i, op in enumerate(self.operations):
            if op.id == op_id:
                new.id = op_id
                self.operations[i] = new
                break
        self.storage.save(self.operations)

    def delete(self, op_id: str) -> None:
        self.operations = [op for op in self.operations if op.id != op_id]
        self.storage.save(self.operations)

    def get(self, op_id: str) -> Operation | None:
        return next((op for op in self.operations if op.id == op_id), None)

    def filtered(self, month: str = ALL, kind: str = ALL) -> list[Operation]:
        result = [
            op for op in self.operations
            if (month == ALL or op.month == month)
            and (kind == ALL or op.kind == kind)
        ]
        return sorted(result, key=lambda op: op.dt)

    def months(self) -> list[str]:
        unique = {op.month for op in self.operations}
        return sorted(unique, key=lambda m: datetime.strptime(m, "%m.%Y"))

    @staticmethod
    def totals(ops: list[Operation]) -> tuple[Decimal, Decimal, Decimal]:
        income = sum((o.value for o in ops if o.kind == INCOME), Decimal(0))
        expense = sum((o.value for o in ops if o.kind == EXPENSE), Decimal(0))
        return income, expense, income - expense


def parse_amount(text: str) -> Decimal:
    """Сумма: число больше нуля. Бросает ValueError."""
    try:
        value = Decimal(text.replace(" ", "").replace(",", "."))
    except InvalidOperation:
        raise ValueError("Сумма должна быть числом")
    if value <= 0 or not value.is_finite():
        raise ValueError("Сумма должна быть больше нуля")
    return value


def parse_date(text: str) -> str:
    """Дата в формате ДД.ММ.ГГГГ. Бросает ValueError."""
    try:
        datetime.strptime(text.strip(), DATE_FMT)
    except ValueError:
        raise ValueError("Дата должна быть в формате ДД.ММ.ГГГГ")
    return text.strip()


def money(value: Decimal) -> str:
    text = f"{value:,.2f}".replace(",", " ")
    if text.endswith(".00"):
        text = text[:-3]
    return f"{text} ₸"
