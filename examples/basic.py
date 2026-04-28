"""
Basic usage — no AI framework required.
"""
from apibase import ApibaseClient, Memory

client = ApibaseClient("https://apibase.work", "your-token-here")
mem    = Memory(client, table_id=3)

mem.remember("user_name", "Pierre")
mem.remember("user_lang", "French")

print(mem.recall("user_name"))   # Pierre
print(mem.all())                 # all stored memories
print(mem.search("Pierre"))      # records containing "Pierre"

mem.forget("user_lang")
