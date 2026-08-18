from llm_parser import parse_user_query


class FakeMessage:
    def __init__(self, content):
        self.content = content

class FakeChoices:
    def __init__(self, content):
        self.message = FakeMessage(content)

class FakeResponse:
    def __init__(self, content):
        self.choices = [FakeChoices(content)]

def fake_create(**kwargs):
    return FakeResponse('{"query_name": "winrate", "group_by": "position", "since_date": {"month": 11, "years": -1}}')

def test_parse_user_query(monkeypatch):
    monkeypatch.setattr("llm_parser.client.chat.completions.create", fake_create)

    user_question = "What is my winrate by position since November last year?"
    parsed_query = parse_user_query(user_question)

    assert parsed_query["since_date"] == "2025-11-01", "The date should be 2025-11-01"