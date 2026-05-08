from __future__ import annotations

import json
from typing import Any

from phase3_themes.src.groq_client import GroqClient, GroqError


def generate_action_ideas(
    *,
    client: GroqClient | None,
    model: str,
    top_themes: list[dict[str, Any]],
    quotes: list[dict[str, Any]],
) -> list[dict[str, str]]:
    if client is None:
        return _fallback_actions(top_themes)

    prompt = (
        "Create 3 concrete action ideas for this week's product pulse.\n"
        "Return strict JSON object only with shape:\n"
        '{ "actions": [ {"owner":"Product|Eng|Support", "idea":"..." } ] }\n'
        "Keep each idea short and specific.\n\n"
        f"Top themes: {json.dumps(top_themes, ensure_ascii=True)}\n"
        f"Quotes: {json.dumps(quotes, ensure_ascii=True)}\n"
    )
    try:
        out = client.chat_json(
            model=model,
            system_prompt="You are a senior product ops analyst. Strict JSON only.",
            user_prompt=prompt,
            temperature=0.2,
        )
        actions = out.get("actions", [])
        parsed: list[dict[str, str]] = []
        for item in actions[:3]:
            owner = str(item.get("owner", "Product")).strip() or "Product"
            idea = str(item.get("idea", "")).strip()
            if idea:
                parsed.append({"owner": owner, "idea": idea})
        if len(parsed) == 3:
            return parsed
    except GroqError:
        pass
    return _fallback_actions(top_themes)


def _fallback_actions(top_themes: list[dict[str, Any]]) -> list[dict[str, str]]:
    ideas = []
    owners = ["Product", "Eng", "Support"]
    for i in range(3):
        theme_name = top_themes[i]["name"] if i < len(top_themes) else "Top issue cluster"
        ideas.append(
            {
                "owner": owners[i],
                "idea": f"Run a one-week fix sprint for '{theme_name}' and track week-over-week complaint drop.",
            }
        )
    return ideas

