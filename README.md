# Terminal Calendar + Todo (Textual)

A minimal terminal UI app built with Python and Textual. Navigate a calendar on the left; manage todos for the selected date on the right. Tasks persist to `tasks.json` so they survive restarts.

## Features
- Resizable split layout (calendar | todos)
- Month navigation (prev/next/today)
- Add, toggle (done/undone), and delete tasks
- Per‑day task lists
- JSON persistence (`tasks.json`)

## Requirements
- Python 3.9+
- macOS/Linux/Windows terminal

## Setup
```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```
(Windows PowerShell)
```powershell
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
```

## Run
```bash
.venv/bin/python app.py
```
(Windows)
```powershell
.venv\Scripts\python app.py
```

## Keybindings
- **Calendar (`CalendarTable`)**
  - Arrow keys: move between days
  - j / k: previous / next month
  - t: jump to today (also updates todo list)
  - s: toggle focus (calendar <-> todo input)
  - Click date: load that date's todos
- **Todos (`TodoPanel`)**
  - Type in input + Enter: add task
  - Enter on empty input: focus the task list
  - Up/Down: move highlight
  - Enter: toggle done/undone
  - x: cut selected task
  - p: paste task to the currently selected date
  - n: move selected task to next day
  - Delete/Backspace: delete task
  - Esc: focus the list
  - s: toggle focus (calendar <-> todo input)
- **App**
  - Ctrl+T: jump to today from anywhere
  - Ctrl+S: toggle focus (calendar <-> todo input)
  - q: quit

## Persistence
- Tasks are saved to `tasks.json` in the project root.
- To reset, delete `tasks.json`.

## Project Structure
```
app.py          # Textual app (CalendarTable, TodoPanel, CalTodoApp)
styles.tcss     # Textual CSS
requirements.txt# Dependencies (textual>=0.50)
tasks.json      # App data (auto-created), gitignored
```

## Notes
- Tested with Textual 0.5x series.
- If keys don’t respond, ensure the list (not the input) has focus.
