"""Anthropic + CelestialMemory middleware example.

Usage:
    pip install stellar-memory[llm]
    export ANTHROPIC_API_KEY=sk-ant-...
    python examples/middleware_anthropic.py
"""

import anthropic

from celestial_engine import CelestialMemory, MemoryMiddleware, MemoryPresets

# 1. Initialize memory with factual preset
memory = CelestialMemory(
    memory_fn_config=MemoryPresets.FACTUAL,
)

# 2. Create middleware
middleware = MemoryMiddleware(memory)

# 3. Wrap Anthropic client - just 3 lines!
client = anthropic.Anthropic()
wrapped = middleware.wrap_anthropic(client)

# 4. Use exactly like the regular Anthropic SDK
response = wrapped.messages.create(
    model="claude-sonnet-4-5-20250514",
    max_tokens=1024,
    messages=[{"role": "user", "content": "My favorite language is Python and I work at Anthropic."}],
)
print("Claude:", response.content[0].text)

# 5. Memory is automatically saved. Now ask about it:
response = wrapped.messages.create(
    model="claude-sonnet-4-5-20250514",
    max_tokens=1024,
    messages=[{"role": "user", "content": "What do I work on?"}],
)
print("Claude:", response.content[0].text)

# 6. Check memory stats
print("\nMemory stats:", memory.stats())

memory.close()
