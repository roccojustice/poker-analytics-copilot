import pandas as pd
from query_router import run_query
from llm_parser import parse_user_query

df = pd.read_csv("poker_analytics_data.csv")

while True:
    user_question = input("Enter your poker analytics question (or type 'exit' to quit): ")
    if user_question.lower() == "exit":
        break

    parsed_query = parse_user_query(user_question)
    if parsed_query["query_name"] == "unknown":
        print("Sorry, I couldn't understand your question. Please try again.")
        continue
    query_name = parsed_query["query_name"]

    result = run_query(query_name, df, group_by=parsed_query.get("group_by"))

    print(result)
