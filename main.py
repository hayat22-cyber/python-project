

import csv
import json
import os
import shutil
import time
from collections import defaultdict
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import List


# Configuration & Helpers

DATA_FILENAME = os.path.join(os.path.dirname(os.path.abspath(__file__)), "expenses.csv")
BACKUP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backups")
CSV_HEADER = ["Date", "Category", "Amount", "Description"]
CATEGORIES = ["Food", "Transport", "Entertainment", "Shopping", "Bills", "Health", "Education", "Other"]


def ensure_data_file():
    os.makedirs(os.path.dirname(DATA_FILENAME), exist_ok=True)
    if not os.path.exists(DATA_FILENAME):
        with open(DATA_FILENAME, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(CSV_HEADER)


def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def pause():
    input("\nPress Enter to continue...")



# Data Model

@dataclass
class Expense:
    amount: float
    category: str
    date: str  # YYYY-MM-DD
    description: str = ""

    def to_row(self) -> List[str]:
        return [self.date, self.category, f"{self.amount:.2f}", self.description]

    @classmethod
    def from_row(cls, row: List[str]):
        # row: [date, category, amount, description]
        date = row[0]
        category = row[1]
        amount = float(row[2])
        description = row[3] if len(row) > 3 else ""
        return cls(amount=amount, category=category, date=date, description=description)

    def __str__(self):
        return f"{self.date} | {self.category}: ₹{self.amount:.2f} - {self.description}"



# File Operations

def load_expenses() -> List[Expense]:
    ensure_data_file()
    expenses = []
    try:
        with open(DATA_FILENAME, "r", newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            for i, row in enumerate(reader):
                if i == 0:
                    continue  # skip header
                if not row or len(row) < 3:
                    continue
                try:
                    expenses.append(Expense.from_row(row))
                except Exception:
                    continue
    except Exception as e:
        print("Error loading data:", e)
    return expenses


def save_expenses(expenses: List[Expense]):
    ensure_data_file()
    try:
        with open(DATA_FILENAME, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(CSV_HEADER)
            for e in expenses:
                writer.writerow(e.to_row())
    except Exception as e:
        print("Error saving data:", e)


def append_expense(expense: Expense):
    ensure_data_file()
    try:
        with open(DATA_FILENAME, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(expense.to_row())
    except Exception as e:
        print("Error appending expense:", e)


def export_json(path=None):
    if path is None:
        path = DATA_FILENAME.replace(".csv", ".json")
    exps = load_expenses()
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump([asdict(e) for e in exps], f, indent=2, ensure_ascii=False)
        print(f"Exported JSON to: {path}")
    except Exception as e:
        print("Export JSON failed:", e)



# Backup & Restore

def create_backup():
    ensure_data_file()
    os.makedirs(BACKUP_DIR, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    dst = os.path.join(BACKUP_DIR, f"expenses_backup_{ts}.csv")
    try:
        shutil.copy(DATA_FILENAME, dst)
        print(f"Backup created: {dst}")
    except Exception as e:
        print("Backup failed:", e)


def list_backups() -> List[str]:
    if not os.path.exists(BACKUP_DIR):
        return []
    files = sorted([f for f in os.listdir(BACKUP_DIR) if f.endswith(".csv")])
    return files


def restore_backup():
    backups = list_backups()
    if not backups:
        print("No backups available.")
        return
    print("Available backups:")
    for i, b in enumerate(backups, 1):
        print(f"{i}. {b}")
    choice = input("Enter backup number to restore (or press Enter to cancel): ").strip()
    if not choice:
        print("Restore cancelled.")
        return
    try:
        idx = int(choice) - 1
        if idx < 0 or idx >= len(backups):
            print("Invalid selection.")
            return
        src = os.path.join(BACKUP_DIR, backups[idx])
        shutil.copy(src, DATA_FILENAME)
        print("Restore completed.")
    except Exception as e:
        print("Restore failed:", e)



# Validation

def valid_date(s: str) -> bool:
    try:
        datetime.strptime(s, "%Y-%m-%d")
        return True
    except Exception:
        return False


def valid_amount(s: str) -> bool:
    try:
        v = float(s)
        return v >= 0
    except Exception:
        return False



# Reporting

def total_expense(expenses: List[Expense]) -> float:
    return sum(e.amount for e in expenses)


def average_expense(expenses: List[Expense]) -> float:
    if not expenses:
        return 0.0
    return total_expense(expenses) / len(expenses)


def category_summary(expenses: List[Expense]) -> dict:
    d = defaultdict(float)
    for e in expenses:
        d[e.category] += e.amount
    return dict(d)


def monthly_summary(expenses: List[Expense]) -> dict:
    d = defaultdict(float)
    for e in expenses:
        key = e.date[:7]  # YYYY-MM
        d[key] += e.amount
    return dict(d)



# CLI Menu & Flows

def add_expense_flow():
    print("\nADD NEW EXPENSE")
    while True:
        amt = input("Enter amount: ").strip()
        if valid_amount(amt):
            break
        print("Invalid amount. Enter a non-negative number (e.g., 1500 or 99.50).")
    print("Categories:", ", ".join(CATEGORIES))
    cat = input("Enter category (or press Enter for Other): ").strip() or "Other"
    if cat not in CATEGORIES:
        print("Category not recognized; using 'Other'.")
        cat = "Other"
    while True:
        date = input("Enter date (YYYY-MM-DD) or press Enter for today: ").strip()
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")
            break
        if valid_date(date):
            break
        print("Invalid date format. Use YYYY-MM-DD.")
    desc = input("Enter description (optional): ").strip()
    e = Expense(amount=float(amt), category=cat, date=date, description=desc)
    append_expense(e)
    print("✅ Expense added.")


def view_all_expenses(expenses: List[Expense]):
    if not expenses:
        print("\nNo expenses found.")
        return
    print("\nALL EXPENSES:")
    for i, e in enumerate(expenses, 1):
        print(f"{i}. {e}")


def search_expenses_flow(expenses: List[Expense]):
    q = input("Search by category, description, or date (text): ").strip().lower()
    if not q:
        print("Empty query.")
        return
    results = [e for e in expenses if q in e.category.lower() or q in e.description.lower() or q in e.date]
    if not results:
        print("No matches found.")
        return
    print(f"\nFound {len(results)} result(s):")
    for i, e in enumerate(results, 1):
        print(f"{i}. {e}")


def edit_expense_flow(expenses: List[Expense]):
    view_all_expenses(expenses)
    if not expenses:
        return
    idx = input("Enter expense number to edit (or press Enter to cancel): ").strip()
    if not idx:
        print("Cancelled.")
        return
    try:
        i = int(idx) - 1
        if i < 0 or i >= len(expenses):
            print("Invalid number.")
            return
    except Exception:
        print("Invalid input.")
        return
    e = expenses[i]
    print("Leave blank to keep current value.")
    new_amt = input(f"Amount [{e.amount}]: ").strip()
    new_cat = input(f"Category [{e.category}]: ").strip()
    new_date = input(f"Date [{e.date}]: ").strip()
    new_desc = input(f"Description [{e.description}]: ").strip()
    if new_amt:
        if valid_amount(new_amt):
            e.amount = float(new_amt)
        else:
            print("Invalid amount; unchanged.")
    if new_cat:
        e.category = new_cat if new_cat in CATEGORIES else "Other"
    if new_date:
        if valid_date(new_date):
            e.date = new_date
        else:
            print("Invalid date; unchanged.")
    if new_desc:
        e.description = new_desc
    save_expenses(expenses)
    print("Expense updated.")


def delete_expense_flow(expenses: List[Expense]):
    view_all_expenses(expenses)
    if not expenses:
        return
    idx = input("Enter expense number to delete (or press Enter to cancel): ").strip()
    if not idx:
        print("Cancelled.")
        return
    try:
        i = int(idx) - 1
        if i < 0 or i >= len(expenses):
            print("Invalid number.")
            return
    except Exception:
        print("Invalid input.")
        return
    confirm = input("Type YES to confirm deletion: ").strip()
    if confirm == "YES":
        removed = expenses.pop(i)
        save_expenses(expenses)
        print(f"Deleted: {removed}")
    else:
        print("Deletion cancelled.")


def show_reports_flow(expenses: List[Expense]):
    print("\nREPORTS")
    print(f"Total expense: ₹{total_expense(expenses):.2f}")
    print(f"Average expense: ₹{average_expense(expenses):.2f}")
    print("\nCategory-wise:")
    for k, v in sorted(category_summary(expenses).items(), key=lambda x: -x[1]):
        print(f" - {k}: ₹{v:.2f}")
    print("\nMonthly summary:")
    for k, v in sorted(monthly_summary(expenses).items()):
        print(f" - {k}: ₹{v:.2f}")


def export_options_flow():
    print("\nExport Options:")
    print("1. Export to JSON")
    print("2. Create Backup (CSV copy)")
    print("3. Cancel")
    choice = input("Enter choice (1-3): ").strip()
    if choice == "1":
        export_json()
    elif choice == "2":
        create_backup()
    else:
        print("Cancelled.")


def backup_and_restore_flow():
    print("\nBackup & Restore:")
    print("1. Create Backup")
    print("2. Restore from Backup")
    print("3. List backups")
    print("4. Cancel")
    choice = input("Enter choice (1-4): ").strip()
    if choice == "1":
        create_backup()
    elif choice == "2":
        restore_backup()
    elif choice == "3":
        backups = list_backups()
        if not backups:
            print("No backups.")
        else:
            for i, b in enumerate(backups, 1):
                print(f"{i}. {b}")
    else:
        print("Cancelled.")



# Main Menu

def main_menu():
    ensure_data_file()
    while True:
        clear_screen()
        print("=" * 60)
        print("        PERSONAL FINANCE MANAGER - SINGLE FILE")
        print("=" * 60)
        print("1. Add New Expense")
        print("2. View All Expenses")
        print("3. Edit Expense")
        print("4. Delete Expense")
        print("5. Search Expenses")
        print("6. Reports (total/average/category/month)")
        print("7. Export / Backup")
        print("8. Restore / List Backups")
        print("9. Export to JSON")
        print("10. Exit")
        choice = input("\nEnter your choice (1-10): ").strip()
        if choice == "1":
            add_expense_flow()
            pause()
        elif choice == "2":
            exps = load_expenses()
            view_all_expenses(exps)
            pause()
        elif choice == "3":
            exps = load_expenses()
            edit_expense_flow(exps)
            pause()
        elif choice == "4":
            exps = load_expenses()
            delete_expense_flow(exps)
            pause()
        elif choice == "5":
            exps = load_expenses()
            search_expenses_flow(exps)
            pause()
        elif choice == "6":
            exps = load_expenses()
            show_reports_flow(exps)
            pause()
        elif choice == "7":
            export_options_flow()
            pause()
        elif choice == "8":
            backup_and_restore_flow()
            pause()
        elif choice == "9":
            export_json()
            pause()
        elif choice == "10":
            print("\nGoodbye!")
            break
        else:
            print("Invalid choice. Try again.")
            pause()



# Run

if __name__ == "__main__":
    try:
        main_menu()
    except KeyboardInterrupt:
        print("\nExiting. Goodbye!")
