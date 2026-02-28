# Learnings

---

# PyQt5 Optional Dependency Patterns Research

## Date: 2026-02-27

## Research Goal
Find best practices for making a Python engine module optional with respect to PyQt5, using adapter interfaces (no import-time Qt dependency).

## Key Coupling Points Identified
1. QSettings in engine run
2. QMessageBox modal in period check  
3. QMetaObject.invokeMethod for result window

---

## Pattern 1: Try/Except ImportError with Lazy Loading

### Implementation
```python
# engine.py - Core engine without Qt imports
class TradingEngine:
    def __init__(self):
        self._gui_adapter = None
    
    def set_gui_adapter(self, adapter):
        """Inject GUI adapter for user interaction"""
        self._gui_adapter = adapter
    
    def run(self):
        # Instead of QMessageBox.warning
        if self._gui_adapter:
            self._gui_adapter.confirm_warn("Period check", "Continue?")
        else:
            # CLI mode - just proceed or use logging
            pass
```

### Pros
- Simple to implement
- Clear separation between GUI and core logic
- Easy to test without Qt

### Cons
- Must remember to inject adapter
- Runtime errors if adapter not set

### Evidence
Similar to pandas' `import_optional_dependency`:
- **Source**: https://raw.githubusercontent.com/pandas-dev/pandas/main/pandas/compat/_optional.py
- Pattern: Use try/except ImportError, return None if missing

---

## Pattern 2: Abstract Base Class (Adapter Interface)

### Implementation
```python
from abc import ABC, abstractmethod

class GUIAdapter(ABC):
    """Abstract interface for GUI interactions"""
    
    @abstractmethod
    def confirm_warn(self, title: str, message: str) -> bool:
        """Show warning and get user confirmation"""
        pass
    
    @abstractmethod
    def show_results(self, data: dict):
        """Display results window"""
        pass
    
    @abstractmethod
    def save_settings(self, key: str, value):
        """Persist settings (replaces QSettings)"""
        pass

# CLI implementation
class CLIGUIAdapter(GUIAdapter):
    def confirm_warn(self, title: str, message: str) -> bool:
        response = input(f"{title}: {message} (y/n): ")
        return response.lower() == 'y'
    
    def show_results(self, data: dict):
        print(f"Results: {data}")
    
    def save_settings(self, key: str, value):
        # Use configparser or plain file
        pass

# Qt implementation  
class QtGUIAdapter(GUIAdapter):
    def __init__(self, main_window):
        self._window = main_window
    
    def confirm_warn(self, title: str, message: str) -> bool:
        from PyQt5.QtWidgets import QMessageBox
        reply = QMessageBox.question(
            self._window, title, message,
            QMessageBox.Yes | QMessageBox.No
        )
        return reply == QMessageBox.Yes
    
    def show_results(self, data: dict):
        from PyQt5.QtWidgets import QMetaObject
        # Invoke on main thread
        QMetaObject.invokeMethod(
            self._window, "displayResults",
            Qt.QueuedConnection,
            Q_ARG(dict, data)
        )
    
    def save_settings(self, key: str, value):
        from PyQt5.QtCore import QSettings
        settings = QSettings("khQuant", "engine")
        settings.setValue(key, value)
```

### Pros
- Type-safe interface
- Easy to swap implementations
- Clear contract between modules

### Cons
- More boilerplate code
- Need to maintain interface

### Evidence
- pytest-qt uses similar pattern for Qt binding detection
- **Source**: https://raw.githubusercontent.com/pytest-dev/pytest-qt/master/src/pytestqt/qt_compat.py

---

## Pattern 3: Split GUI Modules (Plugin Architecture)

### Implementation
```
project/
├── engine/           # No Qt dependency
│   ├── __init__.py
│   └── trading_engine.py
├── gui/              # Qt-dependent
│   ├── __init__.py
│   └── qt_adapter.py
└── cli/              # CLI adapter
    ├── __init__.py
    └── adapter.py
```

### Usage
```python
# main.py
try:
    from gui import QtGUIAdapter
    adapter = QtGUIAdapter(main_window)
except ImportError:
    from cli import CLIGUIAdapter  
    adapter = CLIGUIAdapter()

engine = TradingEngine()
engine.set_gui_adapter(adapter)
```

### Pros
- Cleanest separation
- No Qt code in engine
- Multiple GUI backends possible

### Cons
- Requires code organization
- More files to manage

---

## Pattern 4: QMetaObject.invokeMethod Replacement

### Problem
Current code uses QMetaObject.invokeMethod to display results from worker thread.

### Solution: Signal/Slot Pattern
```python
from PyQt5.QtCore import QObject, pyqtSignal

class ResultsEmitter(QObject):
    """Bridge for worker thread results"""
    results_ready = pyqtSignal(dict)

# In main window:
self._results_emitter = ResultsEmitter()
self._results_emitter.results_ready.connect(self._on_results)

# In worker:
self._results_emitter.results_ready.emit(results_data)

# In engine (without Qt):
def on_results_ready(self, callback):
    """Register callback for results"""
    self._results_callback = callback

# GUI adapter registers callback
adapter = QtGUIAdapter()
adapter.register_results_callback(window.display_results)
```

### Alternative: Queue-Based Communication
```python
import queue
from threading import Thread

class WorkerThread:
    def __init__(self):
        self._result_queue = queue.Queue()
    
    def run(self):
        # Do work...
        self._result_queue.put(results)
    
    def get_results(self, timeout=1):
        try:
            return self._result_queue.get(timeout=timeout)
        except queue.Empty:
            return None

# In GUI loop:
def check_results(self):
    result = worker.get_results()
    if result:
        self.display_results(result)
```

### Pros
- Thread-safe
- No Qt dependency in worker
- Flexible

### Cons
- More complex setup
- Need to handle queue polling

### Evidence
- Stack Overflow discussion on PyQt threading: https://stackoverflow.com/questions/73313829/pyqt5-calling-widget-slots-safely-from-a-worker-thread
- Qt invokeMethod alternatives: https://runebook.dev/en/docs/qt/qmetaobject/invokeMethod

---

## Pattern 5: QSettings Replacement

### Problem
Engine uses QSettings for configuration.

### Solution: Abstract Settings Interface
```python
class SettingsAdapter(ABC):
    @abstractmethod
    def get(self, key: str, default=None):
        pass
    
    @abstractmethod  
    def set(self, key: str, value):
        pass

# File-based implementation (no Qt)
class FileSettingsAdapter(SettingsAdapter):
    def __init__(self, config_path="config.json"):
        self._path = config_path
        self._data = self._load()
    
    def _load(self):
        if os.path.exists(self._path):
            with open(self._path) as f:
                return json.load(f)
        return {}
    
    def get(self, key: str, default=None):
        return self._data.get(key, default)
    
    def set(self, key: str, value):
        self._data[key] = value
        with open(self._path, 'w') as f:
            json.dump(self._data, f)
```

### Evidence
- Standard Python practice for cross-platform settings
- Similar to how pandas handles optional dependencies

---

## Pattern 6: Message Box (QMessageBox) Replacement

### Problem
Engine shows modal dialogs for user confirmation.

### Solution: Callback-Based Confirmation
```python
# In engine
def check_period(self):
    if self._gui_adapter:
        # Non-blocking check
        self._gui_adapter.request_confirmation(
            title="Period Check",
            message="Continue with current period?",
            on_confirm=self._continue_run,
            on_cancel=self._cancel_run
        )
    else:
        # Auto-confirm in CLI mode
        self._continue_run()

# In GUI adapter
class QtGUIAdapter:
    def request_confirmation(self, title, message, on_confirm, on_cancel):
        reply = QMessageBox.question(
            self._window, title, message,
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            on_confirm()
        else:
            on_cancel()
```

### Pros
- Works with any UI frame
---APPEND_LEARNINGS_MARKER---

- 2026-02-27: Added RuntimeInteraction boundary in  with  (default) and  (selected when  exists). Qt imports are now optional at module import-time via try/except, and engine UI-touchpoints for progress, period mismatch confirmation, finish callback, result opening, and init-data setting read are routed through the runtime adapter.

- 2026-02-27: Added RuntimeInteraction boundary in khFrame.py with HeadlessRuntimeInteraction (default) and GuiRuntimeInteraction (selected when trader_callback.gui exists). Qt imports are now optional at module import-time via try/except, and engine UI-touchpoints for progress, period mismatch confirmation, finish callback, result opening, and init-data setting read are routed through the runtime adapter.
- Note: Previous line with missing identifiers was a shell-escaping artifact; use the fully qualified entry above for accurate wording.

- 2026-02-27: Added `allow_period_mismatch` runtime flag on `KhQuantFramework.__init__`; default is fail-fast for headless runs.
- 2026-02-27: Added deterministic `PeriodMismatchError` in `_check_period_consistency()` when mismatch occurs without GUI/trader_callback and override is disabled.
- 2026-02-27: Mismatch override path now logs a warning and continues; GUI path still uses `runtime_interaction.confirm_period_mismatch(...)` for user decision.
- 2026-02-27: Backtest artifact contract hardened in `khFrame.py` save block to always emit `summary.csv`, `benchmark.csv`, and `config.csv`.
- 2026-02-27: `summary.csv` now writes a default one-row schema-compatible record when daily stats are missing/insufficient.
- 2026-02-27: `benchmark.csv` now always writes `date,close` header even when benchmark fetch/date extraction fails.
- 2026-02-27: `config.csv` now uses safe nested reads and writes one row with empty-string fallbacks for missing config fields.


## Repo Notes (2026-02-27 23:07:41)
- `requirements.txt` is UTF-16 LE (BOM). Some tooling may treat it as binary unless decoded with `encoding='utf-16'`.

- 2026-02-28: Fixed headless API hang where `KhQuantFramework.run()` never returned after `_run_backtest()`; root cause was `_run_backtest()` only cleared `self.is_running` inside the GUI (`trader_callback`) completion block. Now the flag is cleared unconditionally when backtest completes.
