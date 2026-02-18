# Building an AI Chatbot with Memory

Give your chatbot persistent memory that works across conversations.

## Setup

```bash
pip install stellar-memory[ai]
```

## Basic Integration

```python
from stellar_memory import StellarMemory, StellarConfig, EmotionConfig

config = StellarConfig(
    db_path="chatbot_memory.db",
    emotion=EmotionConfig(enabled=True),
)
memory = StellarMemory(config)
```

## Store User Messages

After each conversation turn, store relevant information:

```python
def process_message(user_input: str, bot_response: str):
    # Store important user information
    memory.store(
        f"User said: {user_input}",
        importance=0.5,
        metadata={"type": "user_message"},
    )

    # Store key facts with higher importance
    if "my name is" in user_input.lower():
        memory.store(
            user_input,
            importance=0.9,
            metadata={"type": "user_fact"},
        )
```

## Build Context from Memory

Before generating a response, recall relevant memories:

```python
def build_context(user_input: str) -> str:
    results = memory.recall(user_input, limit=5)
    if not results:
        return ""

    context_lines = ["Relevant memories:"]
    for item in results:
        context_lines.append(f"- {item.content}")
    return "\n".join(context_lines)
```

## LangChain Integration

```python
from stellar_memory.adapters import StellarLangChainMemory

lc_memory = StellarLangChainMemory(memory)

# Use with any LangChain chain
# from langchain.chains import ConversationChain
# chain = ConversationChain(llm=llm, memory=lc_memory)
```

## Emotional Awareness

With emotion analysis enabled, your chatbot can respond empathetically:

```python
item = memory.store("I'm feeling stressed about the deadline")
if item.emotion and item.emotion.dominant in ("sadness", "fear", "anger"):
    # Respond with empathy
    pass
```

## Cleanup

```python
memory.stop()
```
