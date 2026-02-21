# Personal Assistant with Memory

Build an AI assistant that learns and remembers user preferences over time.

## Setup

```python
from stellar_memory import StellarBuilder, Preset

memory = StellarBuilder(Preset.CHAT).with_sqlite("assistant_memory.db").build()
```

The `CHAT` preset enables emotion analysis and session support, ideal for personal assistants.

## Learning Preferences

Store user preferences with high importance so they stay in the Core zone:

```python
def learn_preference(category: str, preference: str):
    memory.store(
        f"User preference [{category}]: {preference}",
        importance=0.85,
        metadata={"type": "preference", "category": category},
    )

learn_preference("theme", "dark mode")
learn_preference("language", "Python")
learn_preference("communication", "brief and direct")
```

## Recalling Preferences

```python
def get_preferences(topic: str) -> list[str]:
    results = memory.recall(f"preference {topic}", limit=10)
    return [item.content for item in results]

prefs = get_preferences("theme")
# ["User preference [theme]: dark mode"]
```

## Daily Briefing

Use the timeline to generate a daily summary:

```python
import time

def daily_briefing():
    # Get today's memories
    today_start = str(int(time.time()) - 86400)
    entries = memory.timeline(start=today_start, limit=50)

    print(f"Today's activity: {len(entries)} memories recorded")
    for entry in entries[:5]:
        print(f"  - {entry.content[:80]}")
```

## Cleanup

```python
memory.stop()
```
