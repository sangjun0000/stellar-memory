"""OpenAI + CelestialMemory middleware example.

Usage:
    pip install stellar-memory[openai]
    export OPENAI_API_KEY=sk-...
    python examples/middleware_openai.py
"""

from openai import OpenAI

from celestial_engine import CelestialMemory, MemoryMiddleware, MemoryPresets

# 1. Initialize memory with conversational preset
memory = CelestialMemory(
    memory_fn_config=MemoryPresets.CONVERSATIONAL,
)

# 2. Create middleware
middleware = MemoryMiddleware(memory)

# 3. Wrap OpenAI client - just 3 lines!
client = OpenAI()
wrapped = middleware.wrap_openai(client)

# 4. Use exactly like the regular OpenAI SDK
response = wrapped.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "My name is Alice and I love Python."}],
)
print("AI:", response.choices[0].message.content)

# 5. Memory is automatically saved. Now ask about it:
response = wrapped.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "What's my name?"}],
)
print("AI:", response.choices[0].message.content)

# 6. Check memory stats
print("\nMemory stats:", memory.stats())

memory.close()
