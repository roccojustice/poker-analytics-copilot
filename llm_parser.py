import json
from dotenv import load_dotenv
from openai import OpenAI
from queries import AVAILABLE_QUERIES
from datetime import datetime, date
from dateutil.relativedelta import relativedelta

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

Today is {datetime.now().strftime("%Y-%m-%d")}

Available tools:
{tool_descriptions}

Return ONLY valid JSON.

This is the basic JSON format for all tools:
{{"query_name": "tool_name"}}

If the tool requires a group_by dimension, include a "group_by" key with that dimension:
{{"query_name": "tool_name", "group_by": "dimension"}}

If the tool retrieves individual hands and the user asks for a specific number of hands
(e.g. "top 10", "first 20"), include a "limit" key with that integer:
{{"query_name": "tool_name", "limit": 10}}

If the user asks for hands since a specific date, include a "since_date" key with an object
describing the date relative to today. Only include the fields that apply:
- "month": target month as an integer 1-12 (absolute), if a specific month is named
- "years": number of years back from today (negative integer, relative)
- "months": number of months back from today (negative integer, relative)
- "days": number of days back from today (negative integer, relative)

Examples:
"since march" -> {{"since_date": {{"month": 3}}}}
"since yesterday" -> {{"since_date": {{"days": -1}}}}
"since november last year" -> {{"since_date": {{"month": 11, "years": -1}}}}
"day" is optional and can be included if the user specifies a day of the month.

If no specific number is requested, omit "limit" entirely.

If the question does not match any available tool, return:
{{
  "query_name": "unknown"
}}
"""
    print(system_prompt)
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
        parsed = json.loads(content)
        if parsed.get("since_date") is None:
            return parsed
        if "month" in parsed["since_date"]:
            if "day" not in parsed["since_date"]:
                parsed["since_date"]["day"] = 1
        parsed["since_date"] = (date.today() + relativedelta(**parsed["since_date"])).strftime("%Y-%m-%d")
        return parsed
    except json.JSONDecodeError:
        return {"query_name": "unknown"}