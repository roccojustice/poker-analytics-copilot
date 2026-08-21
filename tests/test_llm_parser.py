from llm_parser import parse_user_query


class FakeFunction:
    def __init__(self, name, arguments):
        self.name = name
        self.arguments = arguments

class FakeToolCall:
    def __init__(self, name, arguments):
        self.function = FakeFunction(name, arguments)

class FakeMessage:
    def __init__(self, tool_calls):
        self.tool_calls = tool_calls

class FakeChoices:
    def __init__(self, tool_calls):
        self.message = FakeMessage(tool_calls)

class FakeResponse:
    def __init__(self, tool_calls):
        self.choices = [FakeChoices(tool_calls)]

def fake_create(**kwargs):
    tool_calls = [FakeToolCall("winrate", '{"group_by": "position", "since_date": {"month": 11, "years": -1}}')]
    return FakeResponse(tool_calls)

def fake_create_month_only(**kwargs):
    tool_calls = [FakeToolCall("winrate", '{"group_by": "position", "since_date": {"month": 3}}')]
    return FakeResponse(tool_calls)

def fake_create_no_tool_selected(**kwargs):
    return FakeResponse(None)

def fake_create_no_since_date(**kwargs):
    tool_calls = [FakeToolCall("winrate", '{"group_by": "position"}')]
    return FakeResponse(tool_calls)


def test_parse_user_query(monkeypatch):
    monkeypatch.setattr("llm_parser.client.chat.completions.create", fake_create)

    user_question = "What is my winrate by position since November last year?"
    parsed_query = parse_user_query(user_question)

    assert parsed_query["since_date"] == "2025-11-01", "The date should be 2025-11-01"

def test_parse_user_query_month_only(monkeypatch):
    monkeypatch.setattr("llm_parser.client.chat.completions.create", fake_create_month_only)

    user_question = "What is my winrate by position since March?"
    parsed_query = parse_user_query(user_question)

    assert parsed_query["since_date"] == "2026-03-01", "The date should be 2026-03-01"

def test_parse_user_query_unknown(monkeypatch):
    monkeypatch.setattr("llm_parser.client.chat.completions.create", fake_create_no_tool_selected)

    user_question = "What's the weather like today?"
    parsed_query = parse_user_query(user_question)

    assert parsed_query == {"query_name": "unknown"}, "The query name should be unknown when no tool is selected"

def test_parse_user_query_no_since_date(monkeypatch):
    monkeypatch.setattr("llm_parser.client.chat.completions.create", fake_create_no_since_date)

    user_question = "What is my winrate by position?"
    parsed_query = parse_user_query(user_question)

    assert parsed_query == {"query_name": "winrate", "group_by": "position"}, "The JSON should not contain a since_date key when the user does not specify a date"
