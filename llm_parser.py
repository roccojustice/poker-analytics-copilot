import json
from dotenv import load_dotenv
from openai import OpenAI
from queries import AVAILABLE_QUERIES
from datetime import datetime, date
from dateutil.relativedelta import relativedelta

load_dotenv()

client = OpenAI()

def build_tool_schemas():
    tool_schemas = []

    for name, info in AVAILABLE_QUERIES.items():
        schema = {
            "type": "function",
            "function": {
                "name": name,
                "description": info["description"] + ", ".join(info["examples"]),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "since_date": {
                            "type": "object",
                            "properties": {
                                "month": {"type": "integer", "minimum": 1, "maximum": 12, "description": "Target calendar month as an integer 1-12 (e.g. 11 for November), if the user names a specific month. This is absolute, not a relative offset."},
                                "years": {"type": "integer", "description": "Number of years to go back from today, as a negative integer (e.g. -1 for one year ago). This is a relative offset, not an absolute year."},
                                "months": {"type": "integer", "description": "Number of months to go back from today, as a negative integer (e.g. -2 for two months ago). This is a relative offset, not an absolute month."},
                                "days": {"type": "integer", "description": "Number of days to go back from today, as a negative integer (e.g. -1 for yesterday). This is a relative offset, not an absolute day count."},
                                "day": {"type": "integer", "minimum": 1, "maximum": 31, "description": "Target day of the month as an integer 1-31, if the user names a specific day. This is absolute, not a relative offset."}
                            },
                            "description": "Filter results to only include data since this date (YYYY-MM-DD).",
                        },
                    },
                }
            }
        }

        if "group_by_options" in info:
            schema["function"]["parameters"]["properties"]["group_by"] = {
                "type": "string",
                "enum": info["group_by_options"],
            }
            schema["function"]["parameters"]["required"] = ["group_by"]

        if "group_by_options" not in info:
            schema["function"]["parameters"]["properties"]["limit"] = {
                "type": "integer",
                "description": "Number of hands to return, only when the user gives an explicit count (e.g. 'top 10', '5 hands'). If the user says something vague like 'a few' or 'some hands' with no number, omit this field entirely instead of guessing.",
            }

        tool_schemas.append(schema)

    return tool_schemas

def parse_user_query(user_question: str) -> dict:
    tool_schemas = build_tool_schemas()

    system_prompt = f"""
You are a query planner for a poker analytics application.

Your job is to map the user's natural language question to exactly one available tool.

Today is {datetime.now().strftime("%Y-%m-%d")}

Available tools:
{tool_schemas}

"""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_question},
        ],
        tools=build_tool_schemas(),
        tool_choice="auto",
        temperature=0,
    )

    content = response.choices[0].message.tool_calls

    if content is None:
        return {"query_name": "unknown"}

    tool_call = content[0]
    query_name = tool_call.function.name
    args = json.loads(tool_call.function.arguments)
    parsed = {"query_name": query_name, **args}

    if parsed.get("since_date") is None:
        return parsed
    if "month" in parsed["since_date"]:
        if "day" not in parsed["since_date"]:
            parsed["since_date"]["day"] = 1
    parsed["since_date"] = (date.today() + relativedelta(**parsed["since_date"])).strftime("%Y-%m-%d")
    return parsed


