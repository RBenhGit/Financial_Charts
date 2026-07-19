# Progress

SPEC.md tasks 1–15 are complete and committed (see git log). The tool is fully
functional end-to-end:

```sh
python -m financial_charts AAPL --source yfinance --range 10y --out out/AAPL.html
python -m financial_charts TEVA.TA --source twelvedata --range 10y --out out/TEVA.html
python -m financial_charts verify-source yfinance --ticker AAPL
```

69 tests passing, `ruff check` clean, `.claude` hooks wired to the uv toolchain.

## Remaining work

**Task 16** (SPEC.md): expand the chart inventory beyond the initial six
(Price, Revenue, Net Income, FCF, EPS, Margins) — EBITDA, Cash & Debt,
Dividends, Return of Capital (ROIC/ROCE), Shares Outstanding, Ratios,
Valuation (P/B), Expenses, Assets/Equity/Liabilities, Debt & Financial
Leverage, plus KPI cards. Each is its own vertical slice under
`charts/builtins/`, following the pattern in `revenue.py`/`revenue_test.py`.
Each new metric needs adding to both adapters' `capability.py` + `adapter.py`
(check what yfinance/Twelve Data actually expose first) and to
`sources/validation.py`'s test coverage stays generic so no changes needed
there.

No other known gaps. Nothing half-done — safe to stop or resume at any point.
