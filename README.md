# apibase-py

**AI agents forget everything. APIBASE gives them memory that humans can read.**

Every session, your agent starts from zero. It doesn't remember the user's name, last week's findings, or the decision it made yesterday. You build workarounds — prompt stuffing, vector stores, JSON files — and none of them let you see what the agent actually knows.

APIBASE is different. Every memory is a row in a real table. You open it, read it, fix it, add to it. No special tools. No embeddings. Just a table.

---

## Use with Claude — no code required

The fastest way to give Claude persistent memory is the MCP server. No code. One config value.

### 1. Create an account at [apibase.work](https://apibase.work)

### 2. Create a table named `memorys` with these columns in order:

| # | Column | Role |
|---|--------|------|
| 1 | `id_memory` | Primary key |
| 2 | `memory` | The memory key |
| 3 | `username` | Which agent stored it |
| 4 | `value` | The stored value |

> `memorys` is globally registered as table GID.30 on apibase.work. Every user who creates this table gets `table_id=30` automatically.

### 3. Enable HIVE on your base

In your base settings, activate HIVE mode.

### 4. Grant Claude access to your table

In your base's ACL settings, add:

- Token: **id 17 — "Claude for HIVE"**
- Permission: **read + write** on `memorys`

This is the shared Claude HIVE token. It can only access tables you explicitly grant it to. Your base stays fully isolated.

### 5. Install the server

```bash
git clone https://github.com/PierreDragon/apibase-py
cd apibase-py
pip install -r requirements.txt
```

### 6. Add to your Claude config

**Claude Desktop** (`claude_desktop_config.json`) or **Claude Code** (`.claude/settings.json`):

```json
{
  "mcpServers": {
    "apibase": {
      "command": "python",
      "args": ["/path/to/apibase-py/server.py"],
      "env": {
        "APIBASE_BASE": "your-basekey"
      }
    }
  }
}
```

`APIBASE_BASE` is the name you chose for your base when creating your account. The Claude HIVE token is bundled in the server — no token to copy or manage.

### 7. Start a conversation

Claude now has direct access to your `memorys` table. It resolves the schema once, then reads and writes autonomously:

```
apibase_schema(table="memorys")
→ T=30, C2="memory", C3="username", C4="value"

apibase_query(T=30, C=2, operator=1, value="goal")
→ checks if the key already exists

New   → apibase_post(T=30, record='{"memory":"goal","value":"...","username":"claude"}')
Update → apibase_put_cell(T=30, id=5, C=4, value="updated value")
Forget → apibase_delete(T=30, id=5)
```

You can open your APIBASE table at any moment — see every memory, correct a wrong value, inject a new fact before the next session.

---

## Why this matters

Today, AI agent memory is either opaque or nonexistent.

**Vector stores** hold embeddings — mathematical representations no human can read or correct. When the agent builds a wrong belief, you can't fix it because you can't see it.

**JSON files** are flat. No structure, no querying, no history.

**Nothing** — the most common solution. Every session is a blank slate.

APIBASE stores agent memory in structured tables with named columns. A human can open the interface, see every memory, correct a wrong assumption, inject a new fact, or trace exactly what the agent knew at any point in time.

**The agent and the human work on the same data.**

---

## Human-in-the-loop by design

This is not an observability layer bolted on after the fact. It is the architecture.

Agent memory lives in a table. Humans read tables. At any moment you can:

- **Correct** a wrong belief before it propagates
- **Inject** a fact the agent needs to know right now
- **Delete** a toxic memory before it influences decisions
- **Audit** the full reasoning trail of an entire multi-agent run

No dashboards. No vector database tooling. Just a table you can open in a browser.

---

## MCP tools reference

| Tool | Description |
|---|---|
| `apibase_schema` | Resolve table id and column ids by name |
| `apibase_query` | Search rows by column value and operator |
| `apibase_get_record` | Get one full record by primary id |
| `apibase_get_cell` | Get one cell by TLC coordinate |
| `apibase_post` | Insert a new record |
| `apibase_put_cell` | Update one cell (preferred for agents) |
| `apibase_put_line` | Replace a full record |
| `apibase_delete` | Delete a record |
| `apibase_debug` | Verify token and env configuration |

---

## Python SDK

For developers who want to build agents in code rather than through Claude.

```bash
pip install -e .
```

### Own base (full token)

```python
from apibase import ApibaseClient, Memory

client = ApibaseClient("https://apibase.work", "your-full-token")
mem    = Memory(client, table_id=30, agent_col="username", agent="myagent")

mem.remember("goal", "Summarize the quarterly report")
mem.recall("goal")    # → "Summarize the quarterly report"
mem.forget("goal")
mem.search("quarterly")  # → matching records
mem.all()                # → all memories for this agent
```

### HIVE — access another user's base

```python
from apibase import HiveClient, Memory

hive = HiveClient("https://apibase.work", "hive-token")
mem  = Memory(hive, table_id=30, basekey="their-basekey", agent_col="username", agent="worker")

mem.remember("finding01", "Revenue spike detected on 2026-04-15")
```

### Memory API

| Method | Description |
|---|---|
| `remember(key, value)` | Store or update a memory |
| `recall(key)` | Retrieve a value by key |
| `forget(key)` | Delete a memory |
| `search(text)` | Search across keys and values |
| `all()` | All memories (filtered by agent if set) |

---

## HIVE — a fleet of agents with a shared memory

APIBASE includes a HIVE system for multi-agent architectures.

A **boss agent** owns the master base. Worker agents connect to it via a shared `basekey` and write their findings directly into the boss's memory. The boss reads everything. The human sees everything.

```
Boss agent (full token)
    └── owns the master base
    └── controls who can read, write, edit

Worker agent "research" (hive token, ACL: read + write)
    └── writes findings into boss memory

Worker agent "analyst" (hive token, ACL: read only)
    └── reads directives from boss
```

Every write is visible in real time through the APIBASE interface. You know which agent wrote what, when, and why.

---

## Why AI agents love TLC addressing

APIBASE uses a deterministic address for every piece of data:

```
T{table} / L{line} / C{column}
```

Examples:
```
T30/L1/C2          → one cell: memorys, line 1, column "memory"
T30/L              → all records in memorys
T30/L/C2/O1?V=x   → records where memory = x
```

No ambiguity. No hallucination. An LLM can construct a valid APIBASE query without guessing — the address space is fully enumerable and self-consistent. This is why agents navigate it naturally.

---

## Naming conventions

APIBASE enforces strict naming rules for field names and memory keys:

- No underscores — reserved for `id_x` (primary key) and `x_id` (foreign key)
- Use `username` not `user_name`, `userlang` not `user_lang`
- Dot notation for composed meaning: `created.at`, `total.amount`

---

*MIT License — [apibase.work](https://apibase.work)*
