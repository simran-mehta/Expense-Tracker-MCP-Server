import sqlite3
import csv
import io
from datetime import datetime
from typing import Optional
from fastmcp import FastMCP

DB_PATH = "expenses.db"

mcp = FastMCP("Expense Tracker")


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                description TEXT,
                date TEXT NOT NULL,
                currency TEXT DEFAULT 'USD'
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS budgets (
                category TEXT PRIMARY KEY,
                monthly_limit REAL NOT NULL,
                currency TEXT DEFAULT 'USD'
            )
        """)


init_db()


@mcp.tool
def add_expense(
    amount: float,
    category: str,
    description: str = "",
    date: str = "",
    currency: str = "USD",
) -> dict:
    """Add a new expense. Date format: YYYY-MM-DD (defaults to today)."""
    expense_date = date if date else datetime.today().strftime("%Y-%m-%d")
    with get_db() as conn:
        cursor = conn.execute(
            "INSERT INTO expenses (amount, category, description, date, currency) VALUES (?, ?, ?, ?, ?)",
            (amount, category, description, expense_date, currency),
        )
        return {
            "id": cursor.lastrowid,
            "amount": amount,
            "category": category,
            "description": description,
            "date": expense_date,
            "currency": currency,
        }


@mcp.tool
def list_expenses(
    category: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 50,
) -> list[dict]:
    """List expenses with optional filters. Date format: YYYY-MM-DD."""
    query = "SELECT * FROM expenses WHERE 1=1"
    params: list = []
    if category:
        query += " AND LOWER(category) = LOWER(?)"
        params.append(category)
    if start_date:
        query += " AND date >= ?"
        params.append(start_date)
    if end_date:
        query += " AND date <= ?"
        params.append(end_date)
    query += " ORDER BY date DESC LIMIT ?"
    params.append(limit)
    with get_db() as conn:
        rows = conn.execute(query, params).fetchall()
    return [dict(r) for r in rows]


@mcp.tool
def get_expense_summary(
    group_by: str = "category",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> list[dict]:
    """Summarize total spending grouped by 'category' or 'month'."""
    if group_by == "month":
        group_expr = "strftime('%Y-%m', date)"
        label = "month"
    else:
        group_expr = "category"
        label = "category"

    query = f"SELECT {group_expr} as {label}, SUM(amount) as total, COUNT(*) as count FROM expenses WHERE 1=1"
    params: list = []
    if start_date:
        query += " AND date >= ?"
        params.append(start_date)
    if end_date:
        query += " AND date <= ?"
        params.append(end_date)
    query += f" GROUP BY {group_expr} ORDER BY total DESC"

    with get_db() as conn:
        rows = conn.execute(query, params).fetchall()
    return [dict(r) for r in rows]


@mcp.tool
def update_expense(
    id: int,
    amount: Optional[float] = None,
    category: Optional[str] = None,
    description: Optional[str] = None,
    date: Optional[str] = None,
) -> dict:
    """Update fields of an existing expense by ID."""
    fields, params = [], []
    if amount is not None:
        fields.append("amount = ?"); params.append(amount)
    if category is not None:
        fields.append("category = ?"); params.append(category)
    if description is not None:
        fields.append("description = ?"); params.append(description)
    if date is not None:
        fields.append("date = ?"); params.append(date)
    if not fields:
        return {"error": "No fields provided to update."}
    params.append(id)
    with get_db() as conn:
        conn.execute(f"UPDATE expenses SET {', '.join(fields)} WHERE id = ?", params)
        row = conn.execute("SELECT * FROM expenses WHERE id = ?", (id,)).fetchone()
    if row is None:
        return {"error": f"Expense with id {id} not found."}
    return dict(row)


@mcp.tool
def delete_expense(id: int) -> dict:
    """Delete an expense by ID."""
    with get_db() as conn:
        row = conn.execute("SELECT * FROM expenses WHERE id = ?", (id,)).fetchone()
        if row is None:
            return {"error": f"Expense with id {id} not found."}
        conn.execute("DELETE FROM expenses WHERE id = ?", (id,))
    return {"deleted": dict(row)}


@mcp.tool
def set_budget(category: str, monthly_limit: float, currency: str = "USD") -> dict:
    """Set or update the monthly budget limit for a category."""
    with get_db() as conn:
        conn.execute(
            "INSERT INTO budgets (category, monthly_limit, currency) VALUES (?, ?, ?) "
            "ON CONFLICT(category) DO UPDATE SET monthly_limit=excluded.monthly_limit, currency=excluded.currency",
            (category, monthly_limit, currency),
        )
    return {"category": category, "monthly_limit": monthly_limit, "currency": currency}


@mcp.tool
def get_budget_status(month: Optional[str] = None) -> list[dict]:
    """Compare budget limits vs actual spend. Month format: YYYY-MM (defaults to current month)."""
    target_month = month if month else datetime.today().strftime("%Y-%m")
    with get_db() as conn:
        budgets = conn.execute("SELECT * FROM budgets").fetchall()
        results = []
        for b in budgets:
            row = conn.execute(
                "SELECT COALESCE(SUM(amount), 0) as spent FROM expenses "
                "WHERE LOWER(category) = LOWER(?) AND strftime('%Y-%m', date) = ?",
                (b["category"], target_month),
            ).fetchone()
            spent = row["spent"]
            results.append({
                "category": b["category"],
                "monthly_limit": b["monthly_limit"],
                "currency": b["currency"],
                "spent": spent,
                "remaining": b["monthly_limit"] - spent,
                "over_budget": spent > b["monthly_limit"],
            })
    return results


@mcp.tool
def export_expenses(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    category: Optional[str] = None,
) -> str:
    """Export expenses as a CSV string."""
    rows = list_expenses(category=category, start_date=start_date, end_date=end_date, limit=10000)
    if not rows:
        return "No expenses found for the given filters."
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=["id", "date", "category", "amount", "currency", "description"])
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()


if __name__ == "__main__":
    mcp.run()
