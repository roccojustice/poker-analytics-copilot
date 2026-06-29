import json
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI()


AVAILABLE_QUERIES = {
    "winrate_position": {
        "description": "Calculate Hero's BB/100 grouped by playing position.",
        "examples": [
            "Calcula mi winrate por posición",
            "¿Qué posición gana más?",
            "¿Cuál es mi winrate en BB?",
        ],
    },
    "winrate_site": {
        "description": "Calculate Hero's BB/100 grouped by poker site.",
        "examples": [
            "Calcula mi winrate por site",
            "¿En qué sitio gano más?",
            "Muéstrame mi winrate por plataforma",
        ],
    },
    "threebet_position": {
        "description": (
            "Calculate Hero's 3Bet percentage grouped by position. "
            "Use this when the user asks about 3Bet, re-raising preflop, "
            "raising after another player opened the pot, or raise frequency versus an open."
        ),
        "examples": [
            "Dame mi 3bet por posición",
            "¿Qué tanto resubo preflop por posición?",
            "Calcula mi porcentaje de raise cuando alguien ya abrió el bote antes que yo",
            "¿Con qué frecuencia hago raise vs open raise?",
        ],
    },
}


def build_tool_descriptions() -> str:
    tool_descriptions = ""

    for name, info in AVAILABLE_QUERIES.items():
        tool_descriptions += f"\nTool name: {name}\n"
        tool_descriptions += f"Description: {info['description']}\n"
        tool_descriptions += "Examples:\n"

        for example in info["examples"]:
            tool_descriptions += f"- {example}\n"

    return tool_descriptions


def parse_user_query(user_question: str) -> dict:
    tool_descriptions = build_tool_descriptions()

    system_prompt = f"""
You are a query planner for a poker analytics application.

Your job is to map the user's natural language question to exactly one available tool.

Available tools:
{tool_descriptions}

Return ONLY valid JSON.

JSON format:
{{
  "query_name": "tool_name"
}}

If the question does not match any available tool, return:
{{
  "query_name": "unknown"
}}
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_question},
        ],
        temperature=0,
    )

    content = response.choices[0].message.content

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        return {"query_name": "unknown"}