from __future__ import annotations

import calendar as pycalendar
import datetime as dt
from dataclasses import dataclass
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.message import Message
from textual.reactive import var
from textual.widget import Widget
from textual.widgets import (
    DataTable,
    Footer,
    Header,
    Input,
    Label,
    ListItem,
    ListView,
    Static,
)
from textual.events import Key


# ----------------------------
# Calendar Table
# ----------------------------
class CalendarTable(DataTable):
    """A simple month calendar built on DataTable.

    Emits CalendarTable.DateSelected when a valid day cell is selected.
    """

    class DateSelected(Message):
        def __init__(self, date: dt.date) -> None:
            self.date = date
            super().__init__()

    class MonthChanged(Message):
        def __init__(self, year: int, month: int) -> None:
            self.year = year
            self.month = month
            super().__init__()

    BINDINGS = [
        Binding("j", "prev_month", "Prev"),
        Binding("k", "next_month", "Next"),
        Binding("t", "today", "Today"),
        Binding("s", "swap_focus", show=False),
    ]

    year = var(int(dt.date.today().year))
    month = var(int(dt.date.today().month))

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._cell_to_date: Dict[Tuple[int, int], Optional[dt.date]] = {}
        self.cursor_type = "cell"
        self.show_header = True
        self.zebra_stripes = False
        self.fixed_rows = 0
        self.fixed_columns = 0

    def on_mount(self) -> None:
        self.reload_month()
        self.focus()

    def reload_month(self) -> None:
        """Build or rebuild the month grid."""
        # Prepare headers (Mon..Sun)
        self.clear(columns=True)
        firstweekday = pycalendar.MONDAY
        pycalendar.setfirstweekday(firstweekday)
        headers = [pycalendar.day_abbr[(firstweekday + i) % 7] for i in range(7)]
        for name in headers:
            self.add_column(str(name))

        # Build rows from monthcalendar
        month_matrix = pycalendar.monthcalendar(self.year, self.month)
        self._cell_to_date.clear()
        for r, week in enumerate(month_matrix):
            row_cells: List[str] = []
            for c, day in enumerate(week):
                if day == 0:
                    row_cells.append("")
                    self._cell_to_date[(r, c)] = None
                else:
                    row_cells.append(str(day))
                    self._cell_to_date[(r, c)] = dt.date(self.year, self.month, day)
            self.add_row(*row_cells)

        # Try to move cursor to today if in this month, else top-left valid
        today = dt.date.today()
        if today.year == self.year and today.month == self.month:
            self._move_cursor_to_day(today.day)
        else:
            # Find first non-empty cell
            for (r, c), d in self._cell_to_date.items():
                if d is not None:
                    self.move_cursor(row=r, column=c)
                    break

        # Set table title as Month Year
        month_name = pycalendar.month_name[self.month]
        self.title = f"{month_name} {self.year}"
        # Notify listeners to update any external title labels
        self.post_message(self.MonthChanged(self.year, self.month))

    def _move_cursor_to_day(self, day: int) -> None:
        for (r, c), d in self._cell_to_date.items():
            if d and d.day == day:
                self.move_cursor(row=r, column=c)
                break

    def action_prev_month(self) -> None:
        if self.month == 1:
            self.month = 12
            self.year -= 1
        else:
            self.month -= 1
        self.reload_month()

    def action_next_month(self) -> None:
        if self.month == 12:
            self.month = 1
            self.year += 1
        else:
            self.month += 1
        self.reload_month()

    def action_today(self) -> None:
        today = dt.date.today()
        self.year, self.month = today.year, today.month
        self.reload_month()
        # Ensure listeners (e.g., TodoPanel) update to today's tasks
        self.post_message(self.DateSelected(today))

    def action_swap_focus(self) -> None:
        # Delegate to app to centralize logic
        try:
            self.app.action_swap_focus()
        except Exception:
            pass

    def on_data_table_cell_selected(self, event: DataTable.CellSelected) -> None:  # type: ignore[attr-defined]
        # Be tolerant of Textual API differences across versions
        row = None
        col = None
        coord = getattr(event, "coordinate", None)
        if coord is not None:
            row = getattr(coord, "row", None)
            col = getattr(coord, "column", None)
            if row is None or col is None:
                if isinstance(coord, tuple) and len(coord) >= 2:
                    row, col = coord[0], coord[1]
        if row is None:
            row = getattr(event, "row", None)
        if col is None:
            col = getattr(event, "column", None)

        if isinstance(row, int) and isinstance(col, int):
            date = self._cell_to_date.get((row, col))
            if date is not None:
                self.post_message(self.DateSelected(date))


# ----------------------------
# Todo Panel
# ----------------------------
@dataclass
class Task:
    text: str
    done: bool = False


class TodoPanel(Widget):
    """Right-hand panel showing tasks for the selected date."""

    BINDINGS = [
        Binding("enter", "toggle_task", "Toggle"),
        Binding("x", "toggle_task", show=False),
        Binding("delete", "delete_task", "Delete"),
        Binding("escape", "focus_list", show=False),
        Binding("s", "swap_focus", show=False),
    ]

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.current_date: dt.date = dt.date.today()
        self._highlight_index: int = 0

    def compose(self) -> ComposeResult:
        yield Label(self._date_label_text(), id="todo-date")
        yield ListView(id="todo-list")
        yield Input(placeholder="Add task… (Enter to add)", id="todo-input")

    def on_mount(self) -> None:
        self.refresh_list()
        self.query_one(Input).focus()

    def _date_label_text(self) -> str:
        return self.current_date.strftime("%A, %d %B %Y")

    def set_date(self, date: dt.date) -> None:
        self.current_date = date
        self.query_one("#todo-date", Label).update(self._date_label_text())
        self.refresh_list()

    # Events
    def on_input_submitted(self, event: Input.Submitted) -> None:  # type: ignore[attr-defined]
        text = event.value.strip()
        if text:
            self.app_add_task(text)
            event.input.value = ""
            self.refresh_list()
            event.input.focus()
        else:
            # Empty submit: move focus to tasks list
            try:
                self.query_one(ListView).focus()
            except Exception:
                pass

    def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:  # type: ignore[attr-defined]
        idx = getattr(event, "index", None)
        if not isinstance(idx, int):
            idx = getattr(event.list_view, "index", None)
        if isinstance(idx, int):
            self._highlight_index = idx

    def on_list_view_selected(self, event: ListView.Selected) -> None:  # type: ignore[attr-defined]
        # Enter key on ListView triggers this in Textual 5.x
        self.action_toggle_task()

    # Actions
    def action_toggle_task(self) -> None:
        tasks = self.app_get_tasks()
        if not tasks:
            return
        idx = max(0, min(self._highlight_index, len(tasks) - 1))
        tasks[idx].done = not tasks[idx].done
        self.refresh_list(preserve_highlight=True)
        # Persist change
        try:
            self.app.save_all_tasks()
        except Exception:
            pass

    def action_delete_task(self) -> None:
        tasks = self.app_get_tasks()
        if not tasks:
            return
        idx = max(0, min(self._highlight_index, len(tasks) - 1))
        tasks.pop(idx)
        self._highlight_index = max(0, min(self._highlight_index, len(tasks) - 1))
        self.refresh_list(preserve_highlight=True)
        # Persist change
        try:
            self.app.save_all_tasks()
        except Exception:
            pass

    def on_key(self, event: Key) -> None:
        # Support Delete/Backspace when list has focus
        lv = self.query_one(ListView)
        if getattr(lv, "has_focus", False) and event.key in ("delete", "backspace"):
            self.action_delete_task()
            event.stop()

    def action_focus_list(self) -> None:
        self.query_one(ListView).focus()

    def action_swap_focus(self) -> None:
        # Delegate to app to centralize logic
        try:
            self.app.action_swap_focus()
        except Exception:
            pass

    # Helpers
    def refresh_list(self, preserve_highlight: bool = False) -> None:
        lv = self.query_one(ListView)
        lv.clear()
        tasks = self.app_get_tasks()
        for t in tasks:
            prefix = "✓ " if t.done else "• "
            text = f"{prefix}{t.text}"
            lv.append(ListItem(Label(text)))
        if preserve_highlight and tasks:
            try:
                lv.index = max(0, min(self._highlight_index, len(tasks) - 1))  # type: ignore[attr-defined]
            except Exception:
                pass

    def app_get_tasks(self) -> List[Task]:
        return self.app.get_tasks_for_date(self.current_date)

    def app_add_task(self, text: str) -> None:
        self.app.add_task_for_date(self.current_date, text)


# ----------------------------
# Main App
# ----------------------------
class CalTodoApp(App):
    CSS_PATH = "styles.tcss"
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("t", "today", "Today"),
        Binding("ctrl+t", "today", show=False),
        Binding("ctrl+s", "swap_focus", show=False),
    ]

    def __init__(self) -> None:
        super().__init__()
        self._tasks_by_date: Dict[str, List[Task]] = {}
        # Persist to a JSON file in project directory
        self._persist_path: Path = Path("tasks.json")
        self._load_all_tasks()
        # Track last known date for rollover
        self._last_date: dt.date = dt.date.today()

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal(id="main"):
            with Vertical(id="calendar-pane"):
                with Horizontal(id="calendar-header"):
                    yield Label("", id="calendar-title")
                yield CalendarTable(id="calendar")
            yield Static("", id="divider")
            yield TodoPanel(id="todo")
        yield Footer()

    # Task storage API
    @staticmethod
    def _key_for_date(d: dt.date) -> str:
        return d.isoformat()

    def get_tasks_for_date(self, d: dt.date) -> List[Task]:
        return self._tasks_by_date.setdefault(self._key_for_date(d), [])

    def add_task_for_date(self, d: dt.date, text: str) -> None:
        self.get_tasks_for_date(d).append(Task(text=text, done=False))
        self.save_all_tasks()

    # Wiring calendar -> todo
    def on_calendar_table_date_selected(self, event: CalendarTable.DateSelected) -> None:
        panel = self.query_one("#todo", TodoPanel)
        panel.set_date(event.date)

    def on_calendar_table_month_changed(self, event: CalendarTable.MonthChanged) -> None:
        label = self.query_one("#calendar-title", Label)
        month_name = pycalendar.month_name[event.month]
        label.update(f"{month_name} {event.year}")

    def action_today(self) -> None:
        """Jump calendar and todos to today's date."""
        try:
            cal = self.query_one("#calendar", CalendarTable)
            cal.action_today()
        except Exception:
            pass
        try:
            panel = self.query_one("#todo", TodoPanel)
            panel.set_date(dt.date.today())
        except Exception:
            pass

    def action_swap_focus(self) -> None:
        """Focus the todo input field from anywhere."""
        try:
            todo = self.query_one("#todo", TodoPanel)
            todo.query_one(Input).focus()
        except Exception:
            pass

    def on_mount(self) -> None:
        # Ensure the calendar title is initialized on startup
        try:
            cal = self.query_one("#calendar", CalendarTable)
            label = self.query_one("#calendar-title", Label)
            month_name = pycalendar.month_name[cal.month]
            label.update(f"{month_name} {cal.year}")
        except Exception:
            pass
        # Set interval to check for date change every 60 seconds
        self.set_interval(60, self._tick_day_change)

    def _tick_day_change(self) -> None:
        today = dt.date.today()
        if today != self._last_date:
            self._last_date = today
            # Jump calendar and todo panel to today
            try:
                cal = self.query_one("#calendar", CalendarTable)
                cal.action_today()
            except Exception:
                pass
            try:
                panel = self.query_one("#todo", TodoPanel)
                panel.set_date(today)
            except Exception:
                pass

    # Persistence helpers
    def _load_all_tasks(self) -> None:
        try:
            if self._persist_path.exists():
                data = json.loads(self._persist_path.read_text())
                loaded: Dict[str, List[Task]] = {}
                for k, items in data.items():
                    loaded[k] = [Task(text=i.get("text", ""), done=bool(i.get("done", False))) for i in items]
                self._tasks_by_date = loaded
        except Exception:
            # Ignore malformed files
            self._tasks_by_date = self._tasks_by_date or {}

    def save_all_tasks(self) -> None:
        try:
            serializable = {
                k: [{"text": t.text, "done": t.done} for t in v]
                for k, v in self._tasks_by_date.items()
                if v
            }
            self._persist_path.write_text(json.dumps(serializable, indent=2))
        except Exception:
            pass


if __name__ == "__main__":
    CalTodoApp().run()
