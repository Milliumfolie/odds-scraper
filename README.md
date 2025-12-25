# Odds Scraper
A small sports odds aggregator and utility suite focused on parsing bookmaker sites, merging odds, and computing bet distributions and surebets.

## Quick start ⚡
- Activate the repository's virtualenv (Windows):
  - PowerShell: `Odds-scraper\Scripts\Activate.ps1`
  - cmd: `Odds-scraper\Scripts\activate.bat`
- Install dependencies:
  - `pip install -r requirements.txt`
- Run the GUI (interactive):
  - `python interface_pysimplegui.py`
- Run the example template parser (deterministic, for development):
  - `python sportsbetting/bookmakers/template_parser.py`
  - or `python -c "from sportsbetting.bookmakers.template_parser import parse_template; print(parse_template())"`

## Project layout 🔎
- `interface_pysimplegui.py` — GUI and orchestration (uses queues and toggles flags in `sportsbetting`).
- `sportsbetting/` — core package
  - `__init__.py` — global flags and shared queues (`sb.DB_MANAGEMENT`, `sb.TEST`, `sb.INTERFACE`, `QUEUE_TO_GUI`).
  - `bookmakers/` — site parsers (`parse_*` functions). Add new parsers here.
  - `auxiliary_functions.py` — merging, normalization, and stake-distribution logic.
  - `database_functions.py` — sqlite helpers and interactive DB management.
  - `resources/` — `data.json`, `sites.json`, `competitions.json`, `test.db`.

## Writing a new parser 🧩
- Recommended signature: `def parse_site(url: str | None = None, data: str | None = None, headless: bool=False) -> dict`.
- Return schema for each match key (`"Team A - Team B"`):
```py
{
  "odds": {"bookmaker": [odd1, odd2, odd3]},
  "id": {"bookmaker": id},
  "date": "ISO datetime or datetime object",
  "competition": "Competition name"
}
```
- Keep parsers deterministic for tests: accept a `data` param and return a static dict when no network access is desired.
- Add a small `__main__` test block or a dedicated unit test in `tests/parsers/` that imports your parser and asserts the return structure.

## Tests & CI ✅
- Tests located under `tests/` (e.g., `tests/parsers/test_template_parser.py`).
- A `tests/conftest.py` ensures the repo root is on `sys.path` for imports during test runs.
- GitHub Actions workflow: `.github/workflows/python-tests.yml` (runs `pytest -q tests/`). Note: CI sets up complete `requirements.txt`; for faster CI consider `requirements-test.txt` or caching.

## Important notes & gotchas ⚠️
- DB interactions are often interactive when `sb.DB_MANAGEMENT` or `sb.INTERFACE` are True (prompts/input). For automated/non-interactive runs, set `sb.TEST = True` to suppress prompts.
- Selenium: some parsers use Selenium; project prefers Selenium Manager (Selenium >= 4.6). If needed, modify parsers to use `CHROMEDRIVER_PATH` or webdriver-manager fallback.
- Global mutable state is used widely — changing flags in `sportsbetting` can change behavior across the app.

## Contributing
- Add parser → include `__main__` test, a unit test in `tests/parsers/`, and a short note in the README or an issue describing any site-specific setup (cookies, drivers).

---
If you want, I can also add a short `CONTRIBUTING.md` with a step-by-step parser checklist and PR template. Which would you prefer next?