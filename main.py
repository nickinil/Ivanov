import json
import os
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

DATA_FILE = "expenses.json"

class ExpenseTracker:
    def __init__(self, root):
        self.root = root
        self.root.title("Expense Tracker - Личные расходы")
        self.root.geometry("900x600")

        self.expenses = []
        self.load_data()

        # Создание интерфейса
        self.create_input_frame()
        self.create_filter_frame()
        self.create_table_frame()
        self.create_stats_frame()

        self.refresh_table()
        self.update_stats()

    def create_input_frame(self):
        """Форма добавления расхода"""
        frame = tk.LabelFrame(self.root, text="Добавить расход", padx=10, pady=10)
        frame.pack(fill="x", padx=10, pady=5)

        # Сумма
        tk.Label(frame, text="Сумма:").grid(row=0, column=0, sticky="w")
        self.amount_entry = tk.Entry(frame, width=15)
        self.amount_entry.grid(row=0, column=1, padx=5)

        # Категория
        tk.Label(frame, text="Категория:").grid(row=0, column=2, sticky="w", padx=(10,0))
        self.category_var = tk.StringVar()
        categories = ["Еда", "Транспорт", "Развлечения", "Здоровье", "Жильё", "Другое"]
        self.category_combo = ttk.Combobox(frame, textvariable=self.category_var, values=categories, width=12)
        self.category_combo.grid(row=0, column=3, padx=5)
        self.category_combo.set("Еда")

        # Дата
        tk.Label(frame, text="Дата (ГГГГ-ММ-ДД):").grid(row=0, column=4, sticky="w", padx=(10,0))
        self.date_entry = tk.Entry(frame, width=12)
        self.date_entry.grid(row=0, column=5, padx=5)
        self.date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))

        # Кнопка
        tk.Button(frame, text="Добавить расход", command=self.add_expense, bg="#4CAF50", fg="white").grid(row=0, column=6, padx=10)

    def create_filter_frame(self):
        """Фильтрация"""
        frame = tk.LabelFrame(self.root, text="Фильтрация", padx=10, pady=10)
        frame.pack(fill="x", padx=10, pady=5)

        # Фильтр по категории
        tk.Label(frame, text="Категория:").grid(row=0, column=0, sticky="w")
        self.filter_category_var = tk.StringVar(value="Все")
        categories = ["Все", "Еда", "Транспорт", "Развлечения", "Здоровье", "Жильё", "Другое"]
        self.filter_category_combo = ttk.Combobox(frame, textvariable=self.filter_category_var, values=categories, width=12)
        self.filter_category_combo.grid(row=0, column=1, padx=5)
        self.filter_category_combo.bind("<<ComboboxSelected>>", lambda e: self.apply_filters())

        # Фильтр по дате (период)
        tk.Label(frame, text="Дата от (ГГГГ-ММ-ДД):").grid(row=0, column=2, sticky="w", padx=(10,0))
        self.date_from_entry = tk.Entry(frame, width=12)
        self.date_from_entry.grid(row=0, column=3, padx=5)

        tk.Label(frame, text="до:").grid(row=0, column=4)
        self.date_to_entry = tk.Entry(frame, width=12)
        self.date_to_entry.grid(row=0, column=5, padx=5)

        tk.Button(frame, text="Применить фильтр", command=self.apply_filters).grid(row=0, column=6, padx=10)
        tk.Button(frame, text="Сбросить", command=self.reset_filters).grid(row=0, column=7)

    def create_table_frame(self):
        """Таблица с расходами"""
        frame = tk.Frame(self.root)
        frame.pack(fill="both", expand=True, padx=10, pady=5)

        scrollbar = tk.Scrollbar(frame)
        scrollbar.pack(side="right", fill="y")

        self.tree = ttk.Treeview(frame, columns=("ID", "Сумма", "Категория", "Дата"), show="headings", yscrollcommand=scrollbar.set)
        self.tree.heading("ID", text="ID")
        self.tree.heading("Сумма", text="Сумма (₽)")
        self.tree.heading("Категория", text="Категория")
        self.tree.heading("Дата", text="Дата")

        self.tree.column("ID", width=50, anchor="center")
        self.tree.column("Сумма", width=100, anchor="center")
        self.tree.column("Категория", width=120, anchor="center")
        self.tree.column("Дата", width=100, anchor="center")

        self.tree.pack(fill="both", expand=True)
        scrollbar.config(command=self.tree.yview)

        # Кнопка удаления
        tk.Button(self.root, text="Удалить выбранный расход", command=self.delete_expense, bg="#f44336", fg="white").pack(pady=5)

    def create_stats_frame(self):
        """Статистика суммы за период"""
        frame = tk.LabelFrame(self.root, text="Статистика", padx=10, pady=10)
        frame.pack(fill="x", padx=10, pady=5)

        tk.Label(frame, text="Сумма за период:").pack(side="left", padx=5)
        self.total_label = tk.Label(frame, text="0.00 ₽", font=("Arial", 12, "bold"), fg="green")
        self.total_label.pack(side="left", padx=5)

        tk.Button(frame, text="Рассчитать сумму за выбранный период", command=self.calc_period_sum).pack(side="left", padx=20)

    def add_expense(self):
        """Добавление расхода с проверкой"""
        try:
            amount = float(self.amount_entry.get())
            if amount <= 0:
                raise ValueError("Сумма должна быть положительной")
        except ValueError as e:
            messagebox.showerror("Ошибка", f"Некорректная сумма: {e}")
            return

        category = self.category_var.get()
        if not category:
            messagebox.showerror("Ошибка", "Выберите категорию")
            return

        date_str = self.date_entry.get()
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Ошибка", "Неверный формат даты. Используйте ГГГГ-ММ-ДД")
            return

        new_id = max([e["id"] for e in self.expenses], default=0) + 1
        self.expenses.append({
            "id": new_id,
            "amount": amount,
            "category": category,
            "date": date_str
        })
        self.save_data()
        self.refresh_table()
        self.update_stats()
        self.amount_entry.delete(0, tk.END)
        messagebox.showinfo("Успех", "Расход добавлен")

    def delete_expense(self):
        """Удаление выбранного расхода"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Внимание", "Выберите запись для удаления")
            return

        item = self.tree.item(selected[0])
        expense_id = int(item["values"][0])
        self.expenses = [e for e in self.expenses if e["id"] != expense_id]
        self.save_data()
        self.refresh_table()
        self.update_stats()

    def apply_filters(self):
        """Применение фильтров"""
        self.refresh_table()

    def reset_filters(self):
        """Сброс фильтров"""
        self.filter_category_var.set("Все")
        self.date_from_entry.delete(0, tk.END)
        self.date_to_entry.delete(0, tk.END)
        self.refresh_table()

    def get_filtered_expenses(self):
        """Возвращает расходы с учётом фильтров"""
        filtered = self.expenses[:]

        # Фильтр по категории
        category_filter = self.filter_category_var.get()
        if category_filter != "Все":
            filtered = [e for e in filtered if e["category"] == category_filter]

        # Фильтр по дате
        date_from = self.date_from_entry.get()
        date_to = self.date_to_entry.get()

        if date_from:
            try:
                from_date = datetime.strptime(date_from, "%Y-%m-%d")
                filtered = [e for e in filtered if datetime.strptime(e["date"], "%Y-%m-%d") >= from_date]
            except ValueError:
                pass

        if date_to:
            try:
                to_date = datetime.strptime(date_to, "%Y-%m-%d")
                filtered = [e for e in filtered if datetime.strptime(e["date"], "%Y-%m-%d") <= to_date]
            except ValueError:
                pass

        return filtered

    def refresh_table(self):
        """Обновление таблицы"""
        for row in self.tree.get_children():
            self.tree.delete(row)

        filtered = self.get_filtered_expenses()
        for exp in filtered:
            self.tree.insert("", "end", values=(exp["id"], f"{exp['amount']:.2f}", exp["category"], exp["date"]))

    def update_stats(self):
        """Обновление суммы за отображаемый период"""
        filtered = self.get_filtered_expenses()
        total = sum(e["amount"] for e in filtered)
        self.total_label.config(text=f"{total:.2f} ₽")

    def calc_period_sum(self):
        """Ручной подсчёт суммы за указанный период"""
        date_from = self.date_from_entry.get()
        date_to = self.date_to_entry.get()

        if not date_from or not date_to:
            messagebox.showwarning("Внимание", "Укажите обе даты (от и до)")
            return

        try:
            from_date = datetime.strptime(date_from, "%Y-%m-%d")
            to_date = datetime.strptime(date_to, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Ошибка", "Неверный формат даты. Используйте ГГГГ-ММ-ДД")
            return

        total = sum(e["amount"] for e in self.expenses if from_date <= datetime.strptime(e["date"], "%Y-%m-%d") <= to_date)
        messagebox.showinfo("Сумма за период", f"Расходы с {date_from} по {date_to}:\n{total:.2f} ₽")

    def load_data(self):
        """Загрузка из JSON"""
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    self.expenses = json.load(f)
            except:
                self.expenses = []

    def save_data(self):
        """Сохранение в JSON"""
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(self.expenses, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    root = tk.Tk()
    app = ExpenseTracker(root)
    root.mainloop()