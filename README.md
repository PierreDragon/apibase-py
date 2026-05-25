# apibase-py

**AI agents forget everything. APIBASE gives them memory that humans can read.**

Every session, your agent starts from zero. It doesn't remember the user's name, last week's findings, or the decision it made yesterday. You build workarounds — prompt stuffing, vector stores, JSON files — and none of them let you see what the agent actually knows.

APIBASE is different. Every memory is a row in a real table. You open it, read it, fix it, add to it. No special tools. No embeddings. Just a table.

```python
from apibase import ApibaseClient, Memory

client = ApibaseClient("https://apibase.work", "your-token")
mem    = Memory(client, table_id=30)

mem.remember("username", "Pierre")
mem.recall("username")     # → "Pierre"
mem.forget("username")
mem.search("Pierre")       # → matching records
```

That's it. The agent remembers. You can see it.

---

## Why this matters

Today, AI agent memory is either opaque or nonexistent.

**Vector stores** hold embeddings — mathematical representations that no human can read or correct. When the agent builds a wrong belief, you can't fix it because you can't see it.

**JSON files** are flat. No structure, no querying, no history.

**Nothing** — the most common solution. Every session is a blank slate.

APIBASE stores agent memory in structured tables with named columns. A human can open the interface, see every memory, correct a wrong assumption, inject a new fact, or trace exactly what the agent knew at any point in time.

**The agent and the human work on the same data.**

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

## HIVE — a fleet of agents with a shared memory

APIBASE includes a HIVE system for multi-agent architectures.

A **boss agent** owns the master base. Worker agents connect to it via a shared `basekey` and write their findings directly into the boss's memory. The boss reads everything. The human sees everything.

```
Boss agent (full token)
    └── owns the master base
    └── controls who can read, write, edit

Worker agent "research" (hive token, ACL: read + add)
    └── writes findings into boss memory
    └── cannot edit or delete what the boss wrote

Worker agent "analyst" (hive token, ACL: read only)
    └── reads directives from boss
    └── cannot write
```

```python
from apibase import ApibaseClient, HiveClient, Memory

# Boss reads and writes its own base
boss   = ApibaseClient("https://apibase.work", full_token)
mem    = Memory(boss, table_id=30, agent_col="username", agent="boss")

# Worker writes into boss base via HIVE
worker = HiveClient("https://apibase.work", hive_token)
mem_w  = Memory(worker, table_id=30, basekey="claude", agent_col="username", agent="research")

mem_w.remember("finding01", "Revenue spike detected on 2026-04-15")
mem.search("spike")   # boss finds it immediately
```

Every write is visible in real time through the APIBASE interface. You know which agent wrote what, when, and why.

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

## Installation

```bash
pip install requests
```

Then clone and install locally:

```bash
git clone https://github.com/PierreDragon/apibase-py
cd apibase-py
pip install -e .
```

---

## Quick start

**1. Create an account at [apibase.work](https://apibase.work)**

**2. Create a table `memorys` with these columns in order:**

| # | Column | Role |
|---|--------|------|
| 1 | `id_memory` | Primary key |
| 2 | `memory` | The memory key |
| 3 | `username` | Which agent stored it |
| 4 | `value` | The stored value |

> `table_id=30` is fixed — `memorys` is globally registered as GID.30 on apibase.work. Every user who creates this table gets the same ID automatically.

**3. Enable HIVE on your base** in your base settings.

**4. Grant ACL on `memorys` to Claude:**

In your base's ACL settings, add access for token **id 17 — "Claude for HIVE"** with **read + write** permissions on the `memorys` table.

This is the shared Claude HIVE token. It can only access tables you explicitly grant it to.

**5. Run:**

```python
from apibase import HiveClient, Memory

hive = HiveClient("https://apibase.work", "<claude-hive-token>")
mem  = Memory(hive, table_id=30, basekey="your-basekey", agent_col="username", agent="claude")

mem.remember("goal", "Summarize the quarterly report")
print(mem.recall("goal"))   # → "Summarize the quarterly report"
print(mem.all())            # → all memories for this agent
```

---

## Use with Claude (MCP server)

No code required. The MCP server exposes every APIBASE operation as a tool Claude can call directly in conversation.

### How it works

Each user owns their own isolated base on apibase.work. Claude connects to it via the HIVE system using a single shared token — **id 17, "Claude for HIVE"** — that you explicitly grant access to. Your memories stay in your base. No one else can read or write them.

```
Your base (apibase.work)
  └── memorys table (T=30)
        └── ACL: Claude for HIVE → read + write
              └── Claude reads and writes only your memories
```

### Setup

**1. Complete the Quick start steps above** (create account, create `memorys` table, enable HIVE, grant ACL to id 17).

**2. Install dependencies:**

```bash
pip install -r requirements.txt
```

**3. Add to your Claude config** (`claude_desktop_config.json` for Claude Desktop, or `.claude/settings.json` for Claude Code):

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

`APIBASE_BASE` is your own base key — the name you chose when creating your base. The Claude HIVE token is bundled in the server and requires no configuration.

**4. Start a conversation.** Claude now has 8 tools and will read and write your `memorys` table automatically.

### How Claude uses the memory table

Claude resolves the schema once, then reads and writes autonomously:

```
1. apibase_schema(table="memorys")
   → T=30, C2="memory", C3="username", C4="value"

2. apibase_query(T=30, C=2, operator=1, value="goal")
   → checks if the memory key already exists

3a. New memory → apibase_post(T=30, record='{"memory":"goal","value":"...","username":"claude"}')
3b. Update     → apibase_put_cell(T=30, id=5, C=4, value="updated value")
3c. Forget     → apibase_delete(T=30, id=5)
```

You can open your APIBASE table at any moment and see exactly what Claude remembered, correct a wrong value, or inject a new fact before the next session.

### Available MCP tools

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

## API reference

### `ApibaseClient(base_url, token)`
Direct access to your own base. Token scope: `full`.

### `HiveClient(base_url, token)`
Access to another user's base via a shared `basekey`. Token scope: `hive`.

### `Memory(client, table_id, basekey=None, agent_col="agent", agent=None)`

| Method | Description |
|---|---|
| `remember(key, value)` | Store or update a memory |
| `recall(key)` | Retrieve a value by key |
| `forget(key)` | Delete a memory |
| `search(text)` | Search across keys and values |
| `all()` | All memories (filtered by agent if set) |

### HIVE naming conventions

APIBASE enforces strict naming rules. Memory keys must follow the same conventions:
- No underscores — underscore is reserved for `id_x` (primary key) and `x_id` (foreign key)
- Use `username` not `user_name`, `userlang` not `user_lang`
- Dot notation for composed meaning: `created.at`, `total.amount`

### `HiveClient` workflow

| Method | Description |
|---|---|
| `request(basekey, table_id)` | Request access to a table |
| `approve(basekey, id_hive)` | Approve a pending request |
| `publish(basekey, id_hive)` | Push a data snapshot to the requester |

---

## Built on APIBASE

[APIBASE](https://apibase.work) is a structured data platform with a REST API. File-based, schema-flexible, no database server required. Each user owns their data entirely.

This SDK turns any APIBASE base into persistent memory for AI agents — readable by humans, queryable by machines, shareable across a fleet via HIVE.

---

*MIT License — [apibase.work](https://apibase.work)*
