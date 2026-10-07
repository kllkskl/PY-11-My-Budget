"""Точка входа. Запуск: python main.py"""
from service import BudgetService
from storage import Storage
from ui import App


def main():
    App(BudgetService(Storage())).mainloop()


if __name__ == "__main__":
    main()
