# Copilot / Agent instructions — odds-scraper ✅

Purpose: quick, actionable orientation so an AI-assistant can be immediately productive in this repo.

## Quick start (Windows) ⚡
- Activate venv: `Odds-scraper\Scripts\Activate.ps1` (PowerShell) or `Odds-scraper\Scripts\activate.bat` (cmd)
- Install deps: `pip install -r requirements.txt`
- Run the GUI: `python interface_pysimplegui.py`
- Run the example parser: `python sportsbetting/bookmakers/template_parser.py` or `python -c "from sportsbetting.bookmakers.template_parser import parse_template; print(parse_template())"`



## Big picture (what to read first) 🔎
- `interface_pysimplegui.py` — main GUI and orchestration for interactive parsing, uses queues to communicate with core logic.
- `sportsbetting/__init__.py` — global config and flags (e.g., `DB_MANAGEMENT`, `TEST`, `INTERFACE`), shared queues (`QUEUE_TO_GUI`, `QUEUE_FROM_GUI`), constants like `BOOKMAKERS` and `SPORTS`.
- `sportsbetting/user_functions.py` — high-level parsing orchestration (calls site parsers, merges results, triggers surebet/values search).
- `sportsbetting/interface_functions.py` — UI-facing wrappers called by the GUI.
- `sportsbetting/auxiliary_functions.py` — merging, formatting, validation helpers; contains the logic for combining odds.
- `sportsbetting/database_functions.py` — sqlite helpers and interactive DB management (adds team names, mappings).
- `sportsbetting/bookmakers/*` — site-specific parsers (each module has `parse_*` functions and often a `__main__` test block).
- `sportsbetting/resources/` — `data.json`, `sites.json`, `competitions.json`, and `test.db` (the local DB used by default).

## How the system works (data & control flow) 🔁
- Parsers (one per bookmaker) return match dictionaries which are merged by helpers in `auxiliary_functions.py`.
- Shared state lives on the `sportsbetting` module (e.g., `ODDS`, `SUREBETS`, `QUEUE_TO_GUI`). Avoid large refactors that change these globals without careful coordination.
- The GUI (`interface_pysimplegui.py`) communicates with parsing logic via `sb.QUEUE_TO_GUI` / `sb.QUEUE_FROM_GUI` and toggles flags such as `sb.IS_PARSING` / `sb.ABORT`.

## Dev & run workflow (Windows examples) ⚙️
- Python: repository uses a virtualenv under `Odds-scraper/` (Python ~3.13). On Windows:
  - PowerShell: `Odds-scraper\Scripts\Activate.ps1`
  - cmd: `Odds-scraper\Scripts\activate.bat`
- Install: `pip install -r requirements.txt` (if not using embedded venv)
- Run GUI: `python interface_pysimplegui.py` (this sets `sb.DB_MANAGEMENT = True` by default in the GUI file)
- Run a single bookmaker parser for testing: `python sportsbetting/bookmakers/onecasino.py` or import the parser in a REPL:
  - `python -c "from sportsbetting.bookmakers.onecasino import parse_onecasino; print(parse_onecasino(url))"`
- Selenium: `selenium==4.36.0` is in `requirements.txt`. Code prefers Selenium Manager (Selenium 4.6+); some modules include commented webdriver-manager fallbacks. If Chrome driver issues occur, add a `CHROMEDRIVER_PATH` in the test script or enable webdriver-manager.

## Important project-specific conventions & gotchas ⚠️
- Data schema expected from parsers (match entry):
  ```json
  "Team A - Team B": {
    "odds": { "bookmaker": [odd1, odd2, odd3] },
    "id": { "bookmaker": id },
    "date": "ISO or datetime object",
    "competition": "Competition name"
  }
  ```
  - When adding or changing parsers, ensure outputs match this structure (see `sportsbetting/resources/data.json` for real examples).
- DB management is interactive: many `database_functions` call `input()` or use GUI prompts when `sb.DB_MANAGEMENT` or `sb.INTERFACE` is enabled. For non-interactive runs set `sb.TEST = True` or toggle `DB_MANAGEMENT`.
- Parsers may rely on headless/non-headless modes (check function signatures like `parse_onecasino(url, headless=False)`). Use the `__main__` blocks in modules for local manual tests.
- Global state is leveraged extensively — changing module-level flags or queue behavior can affect GUI and parsing behavior broadly.

## Parser template & example 🧩
- Location: `sportsbetting/bookmakers/template_parser.py` (example included in repo).
- Minimal parser signature: `def parse_template(url: str | None = None, data: str | None = None, headless: bool=False) -> dict:`
- Quick copy-paste template (development-friendly):

```python
def parse_template(url=None, data=None, headless=False):
    """Return dict with keys as "Team A - Team B" with 'odds', 'id', 'date', 'competition'."""
    # For development return a static example to avoid network dependency:
    return {
        "Sample A - Sample B": {
            "odds": {"template": [2.0, 3.5, 3.0]},
            "id": {"template": "1234"},
            "date": "2025-12-31T15:00:00",
            "competition": "Example League"
        }
    }
```

(Keep parsers deterministic for unit tests by accepting `data` param and returning a dict when provided.)

## Troubleshooting & tips 💡
- If parsing fails for a site: inspect the corresponding `sportsbetting/bookmakers/<site>.py` for HTTP/API paths and date parsing; compare against `data.json` sample entries.
- DB locked errors: re-run with GUI (`sb.INTERFACE`) to allow the interactive retry prompt or avoid concurrent processes accessing `resources/test.db`.
- Clipboard and image features are Windows-specific (use `pywin32` and `PIL`), tests may behave differently on Linux/macOS.

## Recommended quick PR checklist for contributors ✅
- Add/modify a bookmaker parser → include a `__main__` snippet or small reproducible example that returns a dict in the exact schema.
- If touching DB code → note whether changes require toggling `sb.DB_MANAGEMENT` and add a comment describing interactive behavior.
- Keep changes local: prefer adding small helper functions to `auxiliary_functions.py` for shared logic rather than changing global state across modules.

## Open questions to clarify with maintainers (ask before large changes) ❓
- Preferred test strategy / CI runner for parsers (unit tests vs integration tests against live sites).
- Whether `DB_MANAGEMENT` should be controlled via command-line flag or environment variable rather than being set in `interface_pysimplegui.py`.

---
If you'd like, I can refine any section, add an explicit parser example or add a short “how to write a new parser” template. I added a minimal parser template (`sportsbetting/bookmakers/template_parser.py`), a unit test (`tests/parsers/test_template_parser.py`), and a minimal CI workflow (`.github/workflows/python-tests.yml`). Run the tests locally with `pytest -q tests/` and tell me if you'd like adjustments. 🔧