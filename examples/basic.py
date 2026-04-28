"""
Basic usage — no AI framework required.
"""
from apibase import ApibaseClient, Memory

client = ApibaseClient("https://apibase.work", "your-token-here")
mem    = Memory(client, table_id=30)  # memorys — GID.30

mem.remember("username", "Pierre")
mem.remember("userlang", "French")

print(mem.recall("username"))     # Pierre
print(mem.all())                  # all stored memories
print(mem.search("Pierre"))       # records containing "Pierre"

mem.forget("userlang")
