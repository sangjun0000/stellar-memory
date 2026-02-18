"""Basic Stellar Memory usage in 10 lines."""
from stellar_memory import StellarMemory

memory = StellarMemory()

# Store memories with different importance
memory.store("Python was created by Guido van Rossum", importance=0.7)
memory.store("The weather is nice today", importance=0.2)
memory.store("Project deadline is March 1st", importance=0.9)

# Recall relevant memories
results = memory.recall("project deadline")
for item in results:
    print(f"[Zone {item.zone}] {item.content}")

# Check stats
stats = memory.stats()
print(f"\nTotal: {stats.total_memories} memories across 5 zones")

memory.stop()
