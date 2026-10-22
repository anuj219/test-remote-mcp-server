import random
from fastmcp import FastMCP

import os
import sqlite3


# create fastmcp server instance
mcp = FastMCP(name="Expense Tracker")

DB_PATH = os.path.join(os.path.dirname(__file__), "expenses.db")
CATEGORIES_PATH = os.path.join(os.path.dirname(__file__), "categories.json")

def init_db():
    with sqlite3.connect(DB_PATH) as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS expenses(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                subcategory TEXT DEFAULT '',
                note TEXT DEFAULT ''
            )
        """)

init_db()

@mcp.tool
def add_expense(date, amount, category, subcategory, note):
    """Add a new expense entry to DB"""
    with sqlite3.connect(DB_PATH) as c:
        curr = c.execute(
            "INSERT into expenses(date, amount, category, subcategory, note) VALUES(?,?,?,?,?)",
            (date, amount, category, subcategory, note)
        )
        return {"status":"ok", "id": curr.lastrowid}

@mcp.tool
def list_expenses(start_date, end_date):
    """List all expenses from DB"""
    with sqlite3.connect(DB_PATH) as c:
        curr = c.execute(
            """
            SELECT * from expenses
            where date between ? and ?
            ORDER BY id ASC
            """,
            (start_date, end_date)
        )
        cols = [d[0] for d in curr.description]
        return [dict(zip(cols,r)) for r in curr.fetchall()]


@mcp.tool
def summarize(start_date, end_date, category=None):
    """Summarize expenses by category within an inclusive date range"""
    with sqlite3.connect(DB_PATH) as c:
        query = (
            """
            SELECT category, sum(amount) as total_amount
            from expenses
            WHERE date between ? and ?
            """
        )
        params = [start_date, end_date]

        if category:
            query += "  ?"
            params.append(category)

        query += " GROUP BY category"

        curr = c.execute(query, params)
        cols = [d[0] for d in curr.description]
        return [dict(zip(cols,r)) for r in curr.fetchall()]

@mcp.resource("expense://categories", mime_type="application/json")
def categories():
    # Read fresh each time, so you can edit file without restarting 
    with open(CATEGORIES_PATH, "r", encoding="UTF-8") as f:
        return f.read()

if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", port=8000)
