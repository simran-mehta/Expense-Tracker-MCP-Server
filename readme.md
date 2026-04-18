# Expense Tracker MCP Server

An MCP (Model Context Protocol) server that lets AI assistants like Claude manage personal expenses — add, categorize, summarize, and budget — using a local SQLite database.

---

## Overview

This server exposes a set of MCP tools that Claude (or any MCP-compatible client) can call to track your spending. All data is stored locally in a SQLite file — no cloud, no account required.

---

## Features

- Add and manage expenses with categories, amounts, dates, and descriptions
- Filter and list expenses by date range or category
- Summarize spending by category or month
- Set per-category budgets and check remaining balances
- Export expenses to CSV
- Fully local — data stays on your machine

---

## MCP Tools

| Tool | Description | Key Parameters |
|---|---|---|
| `add_expense` | Record a new expense | `amount`, `category`, `description`, `date`, `currency` |
| `list_expenses` | List expenses with optional filters | `category?`, `start_date?`, `end_date?`, `limit?` |
| `get_expense_summary` | Aggregated totals grouped by category or month | `group_by` (`category` or `month`), `start_date?`, `end_date?` |
| `update_expense` | Edit an existing expense by ID | `id`, `amount?`, `category?`, `description?`, `date?` |
| `delete_expense` | Remove an expense by ID | `id` |
| `set_budget` | Set a monthly budget limit for a category | `category`, `monthly_limit`, `currency?` |
| `get_budget_status` | Compare budget limits vs actual spend | `month?` (defaults to current month) |
| `export_expenses` | Export expenses as a CSV string | `start_date?`, `end_date?`, `category?` |

---

## Project Structure

```
expense-tracker-mcp-server/
├── main.py             # MCP server entry point (all tools)
├── expenses.db         # SQLite database (auto-created on first run)
├── pyproject.toml      # Project metadata and dependencies
├── .venv/              # Virtual environment (created by uv)
└── readme.md
```

---

## Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (recommended) or `pip`
- Claude Desktop (to connect the MCP server)

---

## Installation

```bash
# Clone the repo
git clone https://github.com/your-username/expense-tracker-mcp-server.git
cd expense-tracker-mcp-server

# Initialize the project and install dependencies
uv init
uv add fastmcp
```

This creates a `.venv` folder automatically inside the project directory.

---

## Running the Server

```bash
fastmcp run main.py
```

The server starts and listens for MCP connections via stdio. The SQLite database (`expenses.db`) is created automatically on first run.

---

## Connecting to Claude Desktop

Add the following to your Claude Desktop config file:

**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "expense-tracker": {
      "command": "uv",
      "args": [
        "--directory",
        "C:\\Learning\\Expense-Tracker-MCP-Server",
        "run",
        "fastmcp",
        "run",
        "main.py"
      ]
    }
  }
}
```

Fully quit Claude Desktop (system tray → Quit) and reopen it. You should see the expense tracker tools available in the tools panel.

---

## Example Prompts

Once connected to Claude, you can say:

- _"Add a $45 expense for groceries at Whole Foods today"_
- _"Show me all food expenses from this month"_
- _"What did I spend the most on last month?"_
- _"Set a $300 monthly budget for dining out"_
- _"How much of my entertainment budget is left?"_
- _"Export all my expenses from March as CSV"_

---

## Development

```bash
# Run with MCP inspector for debugging
fastmcp dev inspector main.py
```

---

## License

MIT
