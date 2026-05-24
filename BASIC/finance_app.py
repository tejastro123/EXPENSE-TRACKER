
# ============================================================
# AI POWERED SMART FINANCE MANAGEMENT SYSTEM
# Single File Advanced Python Application
# ============================================================
#
# INSTALL REQUIRED PACKAGES:
#
# pip install rich pandas matplotlib openpyxl
#
# RUN:
#
# python finance_app.py
#
# ============================================================

import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt
from rich.progress import track
from rich import box

from datetime import datetime
from statistics import mean
import hashlib
import uuid
import csv
import os

console = Console()

DB_NAME = "finance.db"

# ============================================================
# DATABASE
# ============================================================

class DatabaseManager:

    def __init__(self):
        self.conn = sqlite3.connect(DB_NAME)
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS users(
            username TEXT PRIMARY KEY,
            password TEXT
        )
        """)

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS expenses(
            id TEXT PRIMARY KEY,
            name TEXT,
            amount REAL,
            category TEXT,
            payment_method TEXT,
            date TEXT
        )
        """)

        self.conn.commit()

    def execute(self, query, values=()):
        self.cursor.execute(query, values)
        self.conn.commit()

    def fetchall(self, query, values=()):
        self.cursor.execute(query, values)
        return self.cursor.fetchall()

db = DatabaseManager()

# ============================================================
# AUTH SYSTEM
# ============================================================

class AuthSystem:

    @staticmethod
    def hash_password(password):
        return hashlib.sha256(password.encode()).hexdigest()

    def register(self):

        console.print("\n[bold cyan]REGISTER[/bold cyan]")

        username = Prompt.ask("Username")
        password = Prompt.ask("Password", password=True)

        hashed = self.hash_password(password)

        try:
            db.execute(
                "INSERT INTO users VALUES (?, ?)",
                (username, hashed)
            )

            console.print("[green]Registration Successful![/green]")

        except:
            console.print("[red]User already exists[/red]")

    def login(self):

        console.print("\n[bold cyan]LOGIN[/bold cyan]")

        username = Prompt.ask("Username")
        password = Prompt.ask("Password", password=True)

        hashed = self.hash_password(password)

        user = db.fetchall(
            "SELECT * FROM users WHERE username=? AND password=?",
            (username, hashed)
        )

        if user:
            console.print("[green]Login Successful[/green]")
            return True
        else:
            console.print("[red]Invalid Credentials[/red]")
            return False

# ============================================================
# EXPENSE TRACKER
# ============================================================

class ExpenseTracker:

    def add_expense(self):

        console.print("\n[bold green]ADD EXPENSE[/bold green]")

        name = Prompt.ask("Expense Name")
        amount = float(Prompt.ask("Amount"))
        category = Prompt.ask("Category")
        payment = Prompt.ask("Payment Method")

        expense_id = str(uuid.uuid4())[:8]

        date = datetime.now().strftime("%Y-%m-%d")

        db.execute("""
        INSERT INTO expenses VALUES (?, ?, ?, ?, ?, ?)
        """, (
            expense_id,
            name,
            amount,
            category,
            payment,
            date
        ))

        console.print("[green]Expense Added Successfully[/green]")

    def view_expenses(self):

        data = db.fetchall("SELECT * FROM expenses")

        if not data:
            console.print("[red]No Expenses Found[/red]")
            return

        table = Table(
            title="Expense Records",
            box=box.ROUNDED
        )

        table.add_column("ID", style="cyan")
        table.add_column("Name", style="green")
        table.add_column("Amount", style="yellow")
        table.add_column("Category", style="magenta")
        table.add_column("Payment", style="blue")
        table.add_column("Date", style="white")

        for row in data:
            table.add_row(
                row[0],
                row[1],
                f"₹{row[2]}",
                row[3],
                row[4],
                row[5]
            )

        console.print(table)

    def delete_expense(self):

        expense_id = Prompt.ask("Enter Expense ID")

        db.execute(
            "DELETE FROM expenses WHERE id=?",
            (expense_id,)
        )

        console.print("[red]Expense Deleted[/red]")

# ============================================================
# ANALYTICS ENGINE
# ============================================================

class AnalyticsEngine:

    def total_spending(self):

        data = db.fetchall("SELECT amount FROM expenses")

        total = sum(x[0] for x in data)

        console.print(
            Panel(
                f"[bold yellow]Total Spending: ₹{total}[/bold yellow]"
            )
        )

    def category_analysis(self):

        df = pd.read_sql_query(
            "SELECT category, amount FROM expenses",
            db.conn
        )

        if df.empty:
            console.print("[red]No Data[/red]")
            return

        result = df.groupby("category").sum()

        table = Table(title="Category Analysis")

        table.add_column("Category")
        table.add_column("Total")

        for category, row in result.iterrows():
            table.add_row(
                category,
                f"₹{row['amount']}"
            )

        console.print(table)

    def smart_insights(self):

        df = pd.read_sql_query(
            "SELECT * FROM expenses",
            db.conn
        )

        if df.empty:
            console.print("[red]No Data Available[/red]")
            return

        total = df["amount"].sum()

        category_sum = (
            df.groupby("category")["amount"]
            .sum()
            .sort_values(ascending=False)
        )

        top_category = category_sum.index[0]
        top_amount = category_sum.iloc[0]

        avg = mean(df["amount"])

        console.print("\n[bold cyan]AI FINANCIAL INSIGHTS[/bold cyan]\n")

        console.print(
            f"Top Spending Category: [yellow]{top_category}[/yellow]"
        )

        console.print(
            f"Average Expense: [green]₹{round(avg,2)}[/green]"
        )

        if top_amount > total * 0.4:
            console.print(
                "[red]Warning: Heavy spending detected in one category[/red]"
            )

        if avg > 5000:
            console.print(
                "[yellow]Your average expense is high[/yellow]"
            )

        console.print(
            f"Total Monthly Spending: [bold]₹{total}[/bold]"
        )

# ============================================================
# CHART ENGINE
# ============================================================

class ChartEngine:

    def pie_chart(self):

        df = pd.read_sql_query(
            "SELECT category, amount FROM expenses",
            db.conn
        )

        if df.empty:
            console.print("[red]No Data[/red]")
            return

        grouped = df.groupby("category").sum()

        plt.figure(figsize=(8, 8))

        plt.pie(
            grouped["amount"],
            labels=grouped.index,
            autopct="%1.1f%%"
        )

        plt.title("Expense Distribution")

        plt.show()

    def monthly_chart(self):

        df = pd.read_sql_query(
            "SELECT date, amount FROM expenses",
            db.conn
        )

        if df.empty:
            console.print("[red]No Data[/red]")
            return

        df["date"] = pd.to_datetime(df["date"])

        monthly = (
            df.groupby(df["date"].dt.month)["amount"]
            .sum()
        )

        plt.figure(figsize=(10, 5))

        plt.plot(
            monthly.index,
            monthly.values,
            marker="o"
        )

        plt.xlabel("Month")
        plt.ylabel("Spending")
        plt.title("Monthly Spending Trend")

        plt.show()

# ============================================================
# EXPORT SYSTEM
# ============================================================

class ExportSystem:

    def export_csv(self):

        data = db.fetchall("SELECT * FROM expenses")

        with open(
            "expenses_export.csv",
            "w",
            newline=""
        ) as file:

            writer = csv.writer(file)

            writer.writerow([
                "ID",
                "Name",
                "Amount",
                "Category",
                "Payment",
                "Date"
            ])

            writer.writerows(data)

        console.print(
            "[green]Exported to expenses_export.csv[/green]"
        )

    def export_excel(self):

        df = pd.read_sql_query(
            "SELECT * FROM expenses",
            db.conn
        )

        df.to_excel(
            "expenses_report.xlsx",
            index=False
        )

        console.print(
            "[green]Exported to expenses_report.xlsx[/green]"
        )

# ============================================================
# BUDGET SYSTEM
# ============================================================

class BudgetManager:

    def set_budget(self):

        budget = float(
            Prompt.ask("Enter Monthly Budget")
        )

        data = db.fetchall(
            "SELECT amount FROM expenses"
        )

        total = sum(x[0] for x in data)

        remaining = budget - total

        console.print(
            f"\nTotal Spending: ₹{total}"
        )

        if remaining < 0:
            console.print(
                f"[red]Budget Exceeded by ₹{abs(remaining)}[/red]"
            )
        else:
            console.print(
                f"[green]Remaining Budget: ₹{remaining}[/green]"
            )

# ============================================================
# MAIN APPLICATION
# ============================================================

class FinanceApp:

    def __init__(self):

        self.auth = AuthSystem()
        self.expense = ExpenseTracker()
        self.analytics = AnalyticsEngine()
        self.chart = ChartEngine()
        self.exporter = ExportSystem()
        self.budget = BudgetManager()

    def menu(self):

        while True:

            console.print(
                Panel.fit(
                    """
[bold cyan]
1. Add Expense
2. View Expenses
3. Delete Expense
4. Total Spending
5. Category Analysis
6. Smart AI Insights
7. Pie Chart
8. Monthly Trend Chart
9. Set Budget
10. Export CSV
11. Export Excel
12. Exit
[/bold cyan]
                    """,
                    title="SMART FINANCE SYSTEM"
                )
            )

            choice = Prompt.ask("Enter Choice")

            if choice == "1":
                self.expense.add_expense()

            elif choice == "2":
                self.expense.view_expenses()

            elif choice == "3":
                self.expense.delete_expense()

            elif choice == "4":
                self.analytics.total_spending()

            elif choice == "5":
                self.analytics.category_analysis()

            elif choice == "6":
                self.analytics.smart_insights()

            elif choice == "7":
                self.chart.pie_chart()

            elif choice == "8":
                self.chart.monthly_chart()

            elif choice == "9":
                self.budget.set_budget()

            elif choice == "10":
                self.exporter.export_csv()

            elif choice == "11":
                self.exporter.export_excel()

            elif choice == "12":

                console.print(
                    "[bold red]Goodbye[/bold red]"
                )

                break

            else:
                console.print(
                    "[red]Invalid Choice[/red]"
                )

# ============================================================
# APP START
# ============================================================

def loading_screen():

    console.print(
        "\n[bold green]Initializing Finance System...[/bold green]"
    )

    for _ in track(range(100), description="Loading..."):
        pass

def start():

    loading_screen()

    app = FinanceApp()

    while True:

        console.print(
            Panel.fit(
                """
1. Register
2. Login
3. Exit
                """,
                title="WELCOME"
            )
        )

        choice = Prompt.ask("Select")

        if choice == "1":
            app.auth.register()

        elif choice == "2":

            if app.auth.login():
                app.menu()

        elif choice == "3":
            break

        else:
            console.print("[red]Invalid Option[/red]")

# ============================================================

if __name__ == "__main__":
    start()

# ============================================================
