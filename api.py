import traceback
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from llm_parser import parse_user_query
from query_router import run_query, is_filter_query

app = FastAPI()


class QueryRequest(BaseModel):
    question: str


@app.exception_handler(Exception)
def handle_unexpected_exception(request: Request, exc: Exception):
    print(traceback.format_exc())
    return JSONResponse(
        status_code=500,
        content={"error": "Something went wrong processing your question. Please try again."},
    )


@app.post("/query")
def query(request: QueryRequest):
    parsed_query = parse_user_query(request.question)
    query_name = parsed_query["query_name"]

    if query_name == "unknown":
        return {"error": "Sorry, I couldn't understand your question."}

    if is_filter_query(query_name):
        result = run_query(query_name, limit=parsed_query.get("limit"))
    else:
        result = run_query(query_name, group_by=parsed_query.get("group_by"))

    return {"result": result.reset_index().to_dict(orient="records")}