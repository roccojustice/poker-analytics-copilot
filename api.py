from datetime import date
import traceback
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict
from llm_parser import parse_user_query
from query_router import run_query, is_filter_query, has_distribution
from line_parser import SpotInputError
from spotlight import run_spot

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

    if query_name == "ask_clarifying_question":
        return {"clarifying_question": parsed_query["question"]}

    if is_filter_query(query_name):
        result = run_query(query_name, limit=parsed_query.get("limit"))
    else:
        result = run_query(query_name, group_by=parsed_query.get("group_by"))

    if has_distribution(query_name):
        return {
            "result": {
                "interpreted_filter": result["interpreted_filter"],
                "distribution": result["distribution"],
                "hands": result["hands"].to_dict(orient="records"),
            }
        }

    return {"result": result.reset_index().to_dict(orient="records")}


class SpotRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    pot: str
    position: str
    role: str
    line: str
    formations: list[str] = []
    date_from: date | None = None
    date_to: date | None = None
    flop_types: list[str] = []
    turn_types: list[str] = []
    river_types: list[str] = []


@app.post("/spot")
def spot(request: SpotRequest):
    try:
        result = run_spot(
            request.pot, request.position, request.role, request.line, request.formations,
            date_from=request.date_from, date_to=request.date_to, flop_types=request.flop_types,
            turn_types=request.turn_types, river_types=request.river_types,
        )
    except SpotInputError as exc:
        return JSONResponse(status_code=400, content={"error": str(exc)})
    return {
        "interpreted_filter": result["interpreted_filter"],
        "distribution": result["distribution"],
        "hands": result["hands"].to_dict(orient="records"),
        "split": result["split"],
    }


app.mount("/", StaticFiles(directory="static", html=True), name="static")
