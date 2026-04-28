from __future__ import annotations
from .client import ApibaseClient, HiveClient


class Memory:
    """
    High-level agent memory backed by an APIBASE table.

    Works with both ApibaseClient (own base) and HiveClient (shared base).

    Expected table schema (columns in order):
        id_memory  |  key  |  value  |  agent  (optional)

    Examples:

        # Own base
        client = ApibaseClient("https://apibase.work", token)
        mem = Memory(client, table_id=3)

        # Shared hive base
        hive = HiveClient("https://apibase.work", hive_token)
        mem  = Memory(hive, table_id=3, basekey="acme")

        mem.remember("user_name", "Pierre")
        mem.recall("user_name")       # → "Pierre"
        mem.forget("user_name")
        mem.search("Pierre")          # → list of matching records
        mem.all()                     # → all records
    """

    def __init__(
        self,
        client: ApibaseClient | HiveClient,
        table_id: int,
        basekey: str = None,
        key_col: str = 'memory',
        value_col: str = 'value',
        agent_col: str = 'agent',
        agent: str = None,
    ):
        self._client    = client
        self._table     = table_id
        self._basekey   = basekey
        self._key_col   = key_col
        self._val_col   = value_col
        self._agent_col = agent_col
        self._agent     = agent
        self._pk_col    = None

        if isinstance(client, HiveClient) and basekey is None:
            raise ValueError('basekey is required when using HiveClient')

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def remember(self, key: str, value: str, **extra) -> dict:
        record = {self._key_col: key, self._val_col: str(value)}
        if self._agent:
            record[self._agent_col] = self._agent
        record.update(extra)

        existing = self._find(key)
        if existing:
            pk = self._pk(existing)
            return self._put(pk, record)
        return self._post(record)

    def recall(self, key: str) -> str | None:
        row = self._find(key)
        return row.get(self._val_col) if row else None

    def forget(self, key: str) -> bool:
        row = self._find(key)
        if row is None:
            return False
        self._delete(self._pk(row))
        return True

    def all(self) -> list[dict]:
        rows = self._get()
        if not isinstance(rows, list):
            rows = [rows] if rows else []
        if self._agent:
            rows = [r for r in rows if r.get(self._agent_col) == self._agent]
        return rows

    def search(self, text: str) -> list[dict]:
        text = text.lower()
        return [
            r for r in self.all()
            if text in str(r.get(self._val_col, '')).lower()
            or text in str(r.get(self._key_col, '')).lower()
        ]

    # ------------------------------------------------------------------
    # Routing — dispatches to ApibaseClient or HiveClient
    # ------------------------------------------------------------------

    def _get(self):
        if isinstance(self._client, HiveClient):
            return self._client.get(self._basekey, self._table)
        return self._client.get(self._table)

    def _post(self, record: dict) -> dict:
        if isinstance(self._client, HiveClient):
            return self._client.post(self._basekey, self._table, record)
        return self._client.post(self._table, record)

    def _put(self, primary, record: dict) -> dict:
        if isinstance(self._client, HiveClient):
            return self._client.put(self._basekey, self._table, primary, record)
        return self._client.put(self._table, primary, record)

    def _delete(self, primary) -> dict:
        if isinstance(self._client, HiveClient):
            return self._client.delete(self._basekey, self._table, primary)
        return self._client.delete(self._table, primary)

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _find(self, key: str) -> dict | None:
        for row in self.all():
            if row.get(self._key_col) == key:
                return row
        return None

    def _pk(self, row: dict) -> str:
        if self._pk_col is None:
            self._pk_col = next(iter(row))
        return row[self._pk_col]
