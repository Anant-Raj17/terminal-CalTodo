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
- Calendar (`CalendarTable`):
  - Left/Right: previous/next month
  - t: jump to current month
  - Click date: load that date's todos
- Todos (`TodoPanel`):
  - Type in input + Enter: add task
  - Up/Down: move highlight
  - Enter or x: toggle done/undone
  - Delete/Backspace: delete task
  - Esc: focus the list
- App:
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
