"""Модель данных: одна операция (доход или расход)."""
import uuid
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

DATE_FMT = "%d.%m.%Y"
INCOME, EXPENSE = "Доход", "Расход"


@dataclass
class Operation:
    date: str          # ДД.ММ.ГГГГ
    amount: str        # Decimal хранится строкой, чтобы не терять точность
    category: str
    comment: str
    kind: str          # INCOME или EXPENSE
    id: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = uuid.uuid4().hex

    @property
    def value(self) -> Decimal:
        return Decimal(self.amount)

    @property
    def dt(self) -> datetime:
        return datetime.strptime(self.date, DATE_FMT)

    @property
    def month(self) -> str:
        return self.dt.strftime("%m.%Y")
