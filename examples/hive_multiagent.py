"""
Multi-agent memory with HIVE.

Scenario:
    - Boss agent owns the base (basekey="acme")
    - Worker agent has a hive token with ACL on the memory table
    - Both read/write the same shared memory space
    - The human can open the APIBASE UI and see everything

Setup:
    - Create a hive token (scope=hive) for the worker in APIBASE
    - Grant ACL: read + add on table_id=3 for that token + basekey "acme"
"""
import os
from apibase import ApibaseClient, HiveClient, Memory

BASE  = os.environ['APIBASE_BASE']   # https://apibase.work
BOSS_TOKEN   = os.environ['APIBASE_FULL_TOKEN']   # scope=full
WORKER_TOKEN = os.environ['APIBASE_HIVE_TOKEN']   # scope=hive
BASEKEY      = os.environ['APIBASE_BASEKEY']      # e.g. "acme"
TABLE_ID     = int(os.environ['APIBASE_MEMORY_TABLE'])  # e.g. 3

# Boss agent — full access to own base
boss_client = ApibaseClient(BASE, BOSS_TOKEN)
boss_mem    = Memory(boss_client, table_id=TABLE_ID, agent='boss')

# Worker agent — hive access, writes into boss's base
worker_client = HiveClient(BASE, WORKER_TOKEN)
worker_mem    = Memory(worker_client, table_id=TABLE_ID, basekey=BASEKEY, agent='worker-1')

# Worker stores a finding
worker_mem.remember('analysis_result', 'Revenue increased 12% in Q1')
worker_mem.remember('anomaly_detected', 'Spike on 2026-04-15')

# Boss reads everything (all agents)
boss_all = boss_mem.all()
print('All memories in base:', boss_all)

# Boss searches across agents
hits = boss_mem.search('spike')
print('Anomalies found:', hits)

# Boss writes a directive
boss_mem.remember('directive', 'Focus on April anomaly next')

# Worker reads boss directive
print('Directive:', worker_mem.recall('directive'))
