# Claude Code Starter Kit

A minimal, opinionated foundation for starting a new project with [Claude Code](https://code.claude.com): a CLAUDE.md built on **simplicity** and **modularity**, deterministic quality gates as hooks, three specialized agents, and two workflow skills.

Compiled from Anthropic's official guidance and field-tested community practice — the full research wiki with sources and rationale lives in [RBenhGit/CodeFundation](https://github.com/RBenhGit/CodeFundation) (see `wiki/topics/efficient-coding-foundation.md` for the playbook this kit implements).

## Contents

```
├── CLAUDE.md                        # Project memory template ({{PLACEHOLDERS}} to fill)
└── .claude/
    ├── settings.json                # Hook wiring + a minimal permission allowlist
    ├── hooks/
    │   ├── protect-files.sh         # PreToolUse: blocks edits to .env, lockfiles, .git/
    │   ├── post-edit.sh             # PostToolUse: format + lint each edited file
    │   └── stop-test-gate.sh        # Stop: refuses to finish while tests fail
    ├── agents/
    │   ├── code-reviewer.md         # Read-only adversarial diff review, fresh context
    │   ├── test-writer.md           # Failing-tests-first; never touches implementation
    │   └── debugger.md              # Root cause only — never suppresses symptoms
    └── skills/
        ├── spec/SKILL.md            # /spec — interview → SPEC.md → implement fresh
        └── new-module/SKILL.md      # /new-module — scaffold a vertical slice
```

## Get started

1. Click **Use this template** → create your project repo (or copy `CLAUDE.md` and `.claude/` into an existing one).
2. Fill every `{{PLACEHOLDER}}` in `CLAUDE.md` — or run `/init` first and merge; keep the result under 200 lines.
3. Open `.claude/hooks/post-edit.sh` and `.claude/hooks/stop-test-gate.sh` and set `FORMAT_CMD` / `LINT_CMD` / `TEST_CMD` for your stack. **They are no-ops until you do** — the kit never breaks an unconfigured repo. Keep the scripts executable (`chmod +x .claude/hooks/*.sh`; requires `jq`).
4. Install the code-intelligence plugin for your language (`/plugin` → e.g. `typescript-lsp`, `pyright-lsp`, `rust-analyzer-lsp`) and, if you review PRs, `code-review` or `pr-review-toolkit`.
5. Commit all of it. The foundation only works if every session and teammate gets it.

## The two principles

1. **Simplicity** — a simple concept is less complicated to debug. No abstraction until variation is real; no speculative flags, layers, or config.
2. **Modularity** — clear separation makes issues locatable. Domain directories with vertical slices, explicit interfaces, no reaching into internals; a change touches one slice and its tests.

## Daily loop (short version)

Large feature → `/spec` → fresh session implements SPEC.md.
Any non-trivial change → plan mode first.
Bugs → `debugger` agent (or a failing test first).
Before commit → `code-reviewer` agent or `/code-review`.
The Stop gate keeps a session honest when you walk away.

## Deliberately NOT included

- **Explorer/planner agents** — Claude Code's built-in `Explore` and `Plan` agents already do this; duplicating them adds noise.
- **A generic review skill** — the bundled `/code-review` exists; the `code-reviewer` agent here adds only the project-specific rules (simplicity/modularity findings).
- **Dozens of role agents** — start minimal; add an agent only when you keep spawning the same worker with the same instructions.
- **MCP servers** — connect per need (`claude mcp add`); prefer CLIs (`gh`) where they exist.
