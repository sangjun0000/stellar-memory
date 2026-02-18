"""Chatbot with persistent memory using Stellar Memory."""
from stellar_memory import StellarMemory, StellarConfig, EmotionConfig

config = StellarConfig(
    db_path="chatbot_memory.db",
    emotion=EmotionConfig(enabled=True),
)
memory = StellarMemory(config)

# Simulate conversation - store user facts
memory.store("User's name is Alice", importance=0.9)
memory.store("User likes Python and dark mode", importance=0.7)
memory.store("Had a great conversation about AI", importance=0.5)

# Recall for context building
results = memory.recall("Tell me about the user")
print("Retrieved context for response generation:")
for item in results:
    emotion_str = ""
    if item.emotion:
        emotion_str = f" [{item.emotion.dominant}]"
    print(f"  - {item.content}{emotion_str}")

# Show stats
stats = memory.stats()
print(f"\nMemory stats: {stats.total_memories} memories stored")

memory.stop()
