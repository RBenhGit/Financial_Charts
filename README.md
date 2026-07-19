# Financial Charts

A Python tool that fetches a company's fundamentals — for **US and Tel Aviv Stock Exchange
(TASE)** listings — and renders a fixed, pre-determined grid of charts *all at once*, so an
investor can evaluate the company at a glance (in the spirit of a Qualtrim-style dashboard).

> **Status: early development.** The project's conventions and architecture are documented in
> [CLAUDE.md](CLAUDE.md); there is no application code yet. See the checklist below.

## Planned architecture

Data flows one way — **env-configured data source → per-source adapter → canonical template →
display** — and the display layer reads *only* the template, never a data source directly.

- **Pluggable data sources, chosen by environment config.** `yfinance` is the free tier; a
  paid-tier source can be swapped in without touching the display layer. Credentials come from
  env / `.env`, never committed.
- **One adapter ("converter") per source** maps that source's endpoints onto the canonical
  template. Each source also declares a **capability set** (which metrics, how much history —
  e.g. paid = 10y, free = 4y — supported markets/periods) as config-as-code. Adding a source =
  an `adapter.py` + a declared `capability.py` + a `registry` entry, then confirmed with the
  explicit `verify-source` command (which reconciles the declaration against the live API); its
  limits are surfaced to the user. Renders never probe live.
- **Canonical template = the single display data model** (Pydantic). Every monetary series is
  a `Money`-style `(value, currency, scale)` value tagged with its currency and unit.
- **Markets: US + TASE, native currency only** (₪ / $, no FX conversion). TASE has a unit
  trap — prices are in agorot (1/100 ₪) while reports are in millions of shekels — reconciled
  at the adapter boundary.
- **Caching:** adapters cache the template to disk (keyed by ticker + source + date); the
  display reads cache-first, so metered paid APIs aren't hit needlessly.

The full build plan — chart inventory, per-source capability matrix, tasks, edge cases — is
in [SPEC.md](SPEC.md). Decided there: **static** output (a snapshot page, not a live web app),
free source **yfinance** + paid source **Twelve Data**, US-vs-TASE routing by **`.TA` suffix**,
and period/range **configurable per render**.

## Roadmap

- [x] Project conventions & architecture documented ([CLAUDE.md](CLAUDE.md))
- [x] Full spec — chart inventory, capability matrix, tasks, edge cases ([SPEC.md](SPEC.md))
- [ ] Toolchain & project scaffold (`pyproject.toml`, package layout, hooks wired)
- [ ] Canonical template + `Money` model
- [ ] Data-source adapters (`yfinance` + `twelvedata`) + capability validation
- [ ] Charts + dashboard assembly (static grid)

## Development

Requires **Python 3.12+** and [uv](https://docs.astral.sh/uv/). Once the project is
scaffolded:

```sh
uv sync            # install/lock dependencies
pytest -q          # run tests
ruff check         # lint
ruff format        # format
```

Conventions (simplicity, modularity, verification policy, workflow) live in
[CLAUDE.md](CLAUDE.md). This repo is built on the **CodeFundation starter kit** — see
`.claude/` for its hooks, agents, and skills (`/spec`, `/new-module`).
