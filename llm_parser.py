import json
from dotenv import load_dotenv
from openai import OpenAI
from queries import AVAILABLE_QUERIES

load_dotenv()

client = OpenAI()

def build_tool_descriptions() -> str:
    tool_descriptions = ""

    for name, info in AVAILABLE_QUERIES.items():
        tool_descriptions += f"\nTool name: {name}\n"
        if "group_by_options" in info:
            tool_descriptions += f"\nGroup by options: {', '.join(info['group_by_options'])}\n"
        
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

JSON format when tool requires group_by:
{{"query_name": "tool_name", "group_by": "dimension"}}

JSON format when tool does not require group_by:
{{"query_name": "tool_name"}}

If the tool retrieves individual hands and the user asks for a specific number of hands
(e.g. "top 10", "first 20"), include a "limit" key with that integer:
{{"query_name": "tool_name", "limit": 10}}

If no specific number is requested, omit "limit" entirely.

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