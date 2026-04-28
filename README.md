# apibase-py

Python SDK for [APIBASE](https://apibase.work) — persistent, human-readable memory for AI agents.

---

## The problem with AI agent memory

Today, AI agents forget everything between sessions. The workarounds are painful:

- **Vector stores** — embeddings that humans can't read or correct
- **JSON files** — flat, no structure, no querying
- **Nothing** — the most common solution

When an agent makes a wrong assumption, you can't fix it. You can't even see it.

---

## APIBASE as agent memory

APIBASE is a structured data platform with a REST API. Each user has their own base — a set of typed tables with named columns, accessible via predictable URLs.

This SDK turns APIBASE into **persistent memory for AI agents**:

```python
from apibase import ApibaseClient, Memory

client = ApibaseClient("https://apibase.work", "your-token")
mem    = Memory(client, table_id=30)

mem.remember("username", "Pierre")
mem.recall("username")    # → "Pierre"
mem.forget("username")
mem.search("Pierre")      # → matching records
```

Every memory is a row in a real table. A human can open the APIBASE interface, read it, correct it, add to it — without touching code.

**The agent and the human work on the same data.**

---

## Why AI agents love TLC addressing

APIBASE uses a deterministic address format for every piece of data:

```
T{table} / L{line} / C{column}
```

Examples:
```
T30/L1/C2        → cell: memorys, line 1, column "memory"
T30/L            → all records in memorys
T30/L/C2/O1?V=x  → records where memory = x
```

No ambiguity. No hallucination. An LLM can construct a valid APIBASE query without guessing — the address space is fully enumerable and self-consistent.

---

## HIVE — multi-agent memory with a boss

APIBASE includes a HIVE system for multi-agent architectures.

Each agent has its own base. A **boss agent** owns the master base and grants worker agents access to specific tables via ACL — per table, per operation (`read / add / edit / delete`).

```
Boss agent (full token)
    └── owns the master base
    └── controls HIVE ACL
    └── reads all agent outputs

Worker agent A (hive token, ACL: add on T30)
    └── writes findings into boss's memorys table

Worker agent B (hive token, ACL: read on T30)
    └── reads directives from boss
```

The SDK handles both:

```python
from apibase import ApibaseClient, HiveClient, Memory

# Boss — full access to own base
boss   = ApibaseClient("https://apibase.work", full_token)
mem    = Memory(boss, table_id=30, agent="boss")

# Worker — hive access, writes into boss's base
worker = HiveClient("https://apibase.work", hive_token)
mem_w  = Memory(worker, table_id=30, basekey="acme", agent="worker-1")

worker_mem.remember("finding", "Revenue spike on 2026-04-15")
boss_mem.search("spike")    # → found
```

Every write is visible to humans in real time through the APIBASE interface. You know which agent wrote what, when, and why.

---

## Human-in-the-loop by design

This is not an observability feature bolted on after the fact. It is the architecture.

Agent memory lives in a table. Humans read tables. You can:

- **Correct** a wrong belief the agent stored
- **Inject** a fact the agent needs to know
- **Delete** a toxic memory before it propagates
- **Audit** the full reasoning trail of a multi-agent run

No special tooling. No vector database dashboards. Just a table.

---

## Installation

```bash
pip install apibase
```

Or from source:

```bash
git clone https://github.com/PierreDragon/apibase-py
cd apibase-py
pip install -e .
```

---

## Quick start

1. Create an account at [apibase.work](https://apibase.work)
2. Create a table `memorys` with columns: `id_memory | memory | value | agent`
3. Generate a token (scope: `full`)
4. Run:

```python
from apibase import ApibaseClient, Memory

client = ApibaseClient("https://apibase.work", "your-token")
mem    = Memory(client, table_id=YOUR_TABLE_ID)

mem.remember("goal", "Summarize the quarterly report")
print(mem.recall("goal"))
```

---

## API reference

### `ApibaseClient(base_url, token)`
Direct access to your own base. Token scope: `full`.

### `HiveClient(base_url, token)`
Access to another user's base via a shared `basekey`. Token scope: `hive`.

### `Memory(client, table_id, basekey=None, agent=None)`

| Method | Description |
|---|---|
| `remember(key, value)` | Store or update a memory |
| `recall(key)` | Retrieve a value by key |
| `forget(key)` | Delete a memory |
| `search(text)` | Full-text search across keys and values |
| `all()` | Return all memories (filtered by agent if set) |

### `HiveClient` workflow methods

| Method | Description |
|---|---|
| `request(basekey, table_id)` | Request access to a table |
| `approve(basekey, id_hive)` | Approve a pending request |
| `publish(basekey, id_hive)` | Push a data snapshot to the requester |

---

## License

MIT — see [apibase.work](https://apibase.work)
