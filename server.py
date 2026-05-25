import os
import json
import httpx

from mcp.server.fastmcp import FastMCP


mcp = FastMCP("APIBASE")

API = os.environ.get("APIBASE_URL", "https://apibase.work").rstrip("/")
TOKEN = os.environ.get("APIBASE_TOKEN", "")
HIVE_TOKEN = os.environ.get("APIBASE_HIVE_TOKEN", "")
BASE = os.environ.get("APIBASE_BASE", "")

TIMEOUT = 20.0


def headers(hive: bool = False) -> dict:
    token = HIVE_TOKEN if hive and HIVE_TOKEN else TOKEN
    if not token:
        raise RuntimeError("Missing APIBASE_TOKEN environment variable.")

    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def url(base: str, verb: str, path: str = "") -> str:
    suffix = f"/{path}" if path else ""
    if not base or base == BASE:
        return f"{API}/api/{verb}{suffix}"
    return f"{API}/hive/{verb}/{base}{suffix}"


def is_hive(base: str) -> bool:
    return bool(base) and base != BASE


def parse_record(record: str) -> dict:
    try:
        data = json.loads(record)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON record: {e.msg}") from e

    if not isinstance(data, dict):
        raise ValueError("Record must be a JSON object.")

    return data


@mcp.tool()
def apibase_debug() -> dict:
    return {"token_prefix": TOKEN[:8] + "...", "hive_token_prefix": (HIVE_TOKEN[:8] + "...") if HIVE_TOKEN else "not set", "base": BASE, "api": API}


@mcp.tool()
def apibase_schema(base: str = BASE, table: str = "") -> dict:
    """
    Get the APIBASE schema for a table.

    Use this first to resolve:
      - T = table id
      - C = column ids

    Example:
      apibase_schema(base="acme", table="customers")

    Returns:
      {
        "T": 2,
        "columns": {
          "1": "id_customer",
          "2": "customer",
          "3": "email"
        }
      }

    To resolve column ids by name, swap the columns mapping:
      { "customer": "2", "email": "3" }
    """
    if not base:
        raise ValueError("Base key is required.")

    if not table:
        raise ValueError("Table name is required.")

    r = httpx.get(
        url(base, "schema", table),
        headers=headers(is_hive(base)),
        timeout=TIMEOUT,
    )
    r.raise_for_status()
    return r.json()


@mcp.tool()
def apibase_query(
    base: str = BASE,
    T: int = 0,
    C: int = 0,
    operator: int = 1,
    value: str = "",
) -> dict:
    """
    Query a table and return matching rows as associative arrays.

    T and C must be resolved with apibase_schema first.

    Common APIBASE operators:
      1  = equals
      3  = not equals
      6  = less than
      7  = greater than
      8  = less than or equal
      9  = greater than or equal
      28 = contains
      32 = between
      33 = in list

    Notes:
      - Operator 33 expects values separated by underscore.
      - Operator 32 expects the range format supported by APIBASE.

    Example:
      apibase_query(base="acme", T=2, C=3, operator=28, value="example")

    Returns:
      {
        "data": [
          { "id_customer": 14, "customer": "Acme Industries", ... }
        ]
      }
    """
    if not base:
        raise ValueError("Base key is required.")

    if T <= 0:
        raise ValueError("Valid table id T is required.")

    if C <= 0:
        raise ValueError("Valid column id C is required.")

    r = httpx.get(
        url(base, "get", f"T{T}/L/C{C}/O{operator}"),
        params={
            "V": value,
            "format": "assoc",
        },
        headers=headers(is_hive(base)),
        timeout=TIMEOUT,
    )
    r.raise_for_status()
    return r.json()


@mcp.tool()
def apibase_get_cell(
    base: str = BASE,
    T: int = 0,
    id: int = 0,
    C: int = 0,
) -> str:
    """
    Get one cell value by exact TLC coordinate.

    The id parameter is the logical primary value used in L{id}.
    It is not a raw physical file line.

    Example:
      apibase_get_cell(base="acme", T=2, id=14, C=3)

    This calls:
      /hive/get/acme/T2/L14/C3

    Returns:
      Raw cell value as a string.
    """
    if not base:
        raise ValueError("Base key is required.")

    if T <= 0:
        raise ValueError("Valid table id T is required.")

    if id <= 0:
        raise ValueError("Valid primary id is required.")

    if C <= 0:
        raise ValueError("Valid column id C is required.")

    r = httpx.get(
        url(base, "get", f"T{T}/L{id}/C{C}"),
        params={"format": "raw"},
        headers=headers(is_hive(base)),
        timeout=TIMEOUT,
    )
    r.raise_for_status()

    data = r.json()
    return str(data.get("data", ""))


@mcp.tool()
def apibase_get_record(
    base: str = BASE,
    T: int = 0,
    id: int = 0,
) -> dict:
    """
    Get one full record by table id and logical primary value.

    The id parameter is the primary key value used in L{id}.

    Example:
      apibase_get_record(base="acme", T=2, id=14)

    This calls:
      /hive/get/acme/T2/L14?format=assoc

    Returns:
      {
        "data": {
          "id_customer": 14,
          "customer": "Acme Industries",
          ...
        }
      }
    """
    if not base:
        raise ValueError("Base key is required.")

    if T <= 0:
        raise ValueError("Valid table id T is required.")

    if id <= 0:
        raise ValueError("Valid primary id is required.")

    r = httpx.get(
        url(base, "get", f"T{T}/L{id}"),
        params={"format": "assoc"},
        headers=headers(is_hive(base)),
        timeout=TIMEOUT,
    )
    r.raise_for_status()
    return r.json()


@mcp.tool()
def apibase_post(
    base: str = BASE,
    T: int = 0,
    record: str = "{}",
) -> dict:
    """
    Insert a new record into a table.

    T must be resolved with apibase_schema first.

    The record parameter must be a JSON string containing APIBASE-valid field names.

    Valid example:
      {
        "customer": "Acme Industries",
        "email": "billing@acme.example",
        "phone": "+1-555-0100",
        "crm.id": "",
        "synced.at": "",
        "crm.status": "pending"
      }

    Invalid APIBASE business fields:
      full_name
      deal_name
      syncedAt
      crm.synced.at

    This calls:
      POST /hive/post/{base}/T{T}
      { "record": { ... } }

    Returns:
      {
        "status": "success",
        "message": "Record added.",
        "line": 14,
        "hive_base": "acme",
        "id_customer": 14
      }
    """
    if not base:
        raise ValueError("Base key is required.")

    if T <= 0:
        raise ValueError("Valid table id T is required.")

    payload = parse_record(record)

    r = httpx.post(
        url(base, "post", f"T{T}"),
        json={"record": payload},
        headers=headers(is_hive(base)),
        timeout=TIMEOUT,
    )
    r.raise_for_status()
    return r.json()


@mcp.tool()
def apibase_put_cell(
    base: str = BASE,
    T: int = 0,
    id: int = 0,
    C: int = 0,
    value: str = "",
) -> dict:
    """
    Update one exact cell by TLC coordinate.

    This is the preferred write pattern for AI agents when only one value must change.

    The URL identifies the cell.
    The JSON body carries the new value.

    Example:
      apibase_put_cell(base="acme", T=2, id=14, C=5, value="crm7890")

    This calls:
      PUT /hive/put/acme/T2/L14/C5
      { "value": "crm7890" }

    Returns:
      {
        "status": "success",
        "mode": "cell",
        "message": "Cell updated.",
        "hive_base": "acme"
      }
    """
    if not base:
        raise ValueError("Base key is required.")

    if T <= 0:
        raise ValueError("Valid table id T is required.")

    if id <= 0:
        raise ValueError("Valid primary id is required.")

    if C <= 0:
        raise ValueError("Valid column id C is required.")

    r = httpx.put(
        url(base, "put", f"T{T}/L{id}/C{C}"),
        json={"value": value},
        headers=headers(is_hive(base)),
        timeout=TIMEOUT,
    )
    r.raise_for_status()
    return r.json()


@mcp.tool()
def apibase_put_line(
    base: str = BASE,
    T: int = 0,
    id: int = 0,
    record: str = "{}",
) -> dict:
    """
    Replace or update a full record by logical primary value.

    T must be resolved with apibase_schema first.
    The id parameter is the primary key value used in L{id}.

    Use apibase_put_cell when updating only one value.
    Use apibase_put_line only when you intentionally want to send a record object.

    Example:
      apibase_put_line(
        base="acme",
        T=2,
        id=14,
        record='{"customer":"Acme Industries","crm.id":"crm7890","synced.at":"2026-05-10T14:30","crm.status":"synced"}'
      )

    This calls:
      PUT /hive/put/{base}/T{T}/L{id}
      { "record": { ... } }

    Returns:
      {
        "status": "success",
        "mode": "line",
        "message": "Line replaced.",
        "hive_base": "acme"
      }
    """
    if not base:
        raise ValueError("Base key is required.")

    if T <= 0:
        raise ValueError("Valid table id T is required.")

    if id <= 0:
        raise ValueError("Valid primary id is required.")

    payload = parse_record(record)

    r = httpx.put(
        url(base, "put", f"T{T}/L{id}"),
        json={"record": payload},
        headers=headers(is_hive(base)),
        timeout=TIMEOUT,
    )
    r.raise_for_status()
    return r.json()


@mcp.tool()
def apibase_delete(
    base: str = BASE,
    T: int = 0,
    id: int = 0,
) -> dict:
    """
    Delete a record by logical primary value.

    Requires delete ACL on the target table.

    Warning:
      Deleting through an AI tool should be restricted carefully.
      Prefer read-only tools and exact cell updates first.

    Example:
      apibase_delete(base="acme", T=2, id=14)

    This calls:
      DELETE /hive/delete/acme/T2/L14

    Returns:
      {
        "status": "success"
      }
    """
    if not base:
        raise ValueError("Base key is required.")

    if T <= 0:
        raise ValueError("Valid table id T is required.")

    if id <= 0:
        raise ValueError("Valid primary id is required.")

    r = httpx.delete(
        url(base, "delete", f"T{T}/L{id}"),
        headers=headers(is_hive(base)),
        timeout=TIMEOUT,
    )
    r.raise_for_status()
    return r.json()


if __name__ == "__main__":
    mcp.run(transport="stdio")