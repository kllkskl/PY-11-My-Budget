"""Хранение операций в JSON-файле."""
import json
from dataclasses import asdict
from pathlib import Path

from models import Operation

DATA_FILE = Path(__file__).with_name("budget.json")


class Storage:
    def __init__(self, path: Path = DATA_FILE):
        self.path = path

    def load(self) -> list[Operation]:
        if not self.path.exists():
            return []
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            return [Operation(**item) for item in raw]
        except (json.JSONDecodeError, TypeError, KeyError):
            return []  # TODO: сообщить пользователю о повреждённом файле

    def save(self, operations: list[Operation]) -> None:
        data = [asdict(op) for op in operations]
        self.path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )
