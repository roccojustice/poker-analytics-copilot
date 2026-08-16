from query_router import (
    run_query,
    is_filter_query
)
from llm_parser import parse_user_query

import pandas as pd
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)

while True:
    user_question = input("Enter your poker analytics question (or type 'exit' to quit): ")
    if user_question.lower() == "exit":
        break

    parsed_query = parse_user_query(user_question)
    print(parsed_query)
    if parsed_query["query_name"] == "unknown":
        print("Sorry, I couldn't understand your question. Please try again.")
        continue
    query_name = parsed_query["query_name"]

    if is_filter_query(query_name):
        result = run_query(query_name, limit=parsed_query.get("limit"), since_date=parsed_query.get("since_date"))
        print(f"Found {len(result)} hands matching '{query_name}'.")
    else:
        result = run_query(query_name, group_by=parsed_query.get("group_by"), since_date=parsed_query.get("since_date"))

    print(result)
    