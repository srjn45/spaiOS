import ollama

_PROMPT_TEMPLATE = (
    "Summarize the following work session in 2-3 sentences. "
    "Describe what the user worked on, what was accomplished, "
    "and any important context for next time. Be concise and factual.\n\n"
    "Conversation:\n{history}\n\nSummary:"
)
_MAX_HISTORY_CHARS = 3000


def summarize_session(history: list[dict]) -> str:
    turns = [
        f"{msg['role'].upper()}: {msg['content']}"
        for msg in history
        if msg.get("role") in ("user", "assistant")
    ]
    if not turns:
        return ""
    history_text = "\n".join(turns)[:_MAX_HISTORY_CHARS]
    prompt = _PROMPT_TEMPLATE.format(history=history_text)
    response = ollama.generate(model="llama3.2:3b", prompt=prompt)
    return response["response"].strip()
