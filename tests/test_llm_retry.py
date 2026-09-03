from pydantic import BaseModel
import pytest

from job_agent.core.llm import LLMService


class SimpleSchema(BaseModel):
    value: str


class FakeResponse:
    def __init__(self, text: str):
        self.text = text


class FakeModels:
    def __init__(self, calls):
        self._calls = calls
        self.call_count = 0

    def generate_content(self, **kwargs):
        action = self._calls[self.call_count]
        self.call_count += 1
        if isinstance(action, Exception):
            raise action
        return action


class FakeClient:
    def __init__(self, calls):
        self.models = FakeModels(calls)


def test_429_retry_then_success(monkeypatch):
    monkeypatch.setattr("job_agent.core.llm.time.sleep", lambda _s: None)

    service = LLMService(api_key="test-key")
    service.client = FakeClient(
        [
            Exception("429 RESOURCE_EXHAUSTED retryDelay: \"1s\""),
            FakeResponse('{"value":"ok"}'),
        ]
    )

    result = service.generate_structured_response("prompt", SimpleSchema)

    assert result.value == "ok"
    assert service.success_count == 1
    assert service.retry_429_count == 1
    assert service.failure_count == 0
    assert service.client.models.call_count == 2


def test_429_permanent_failure(monkeypatch):
    monkeypatch.setattr("job_agent.core.llm.time.sleep", lambda _s: None)

    service = LLMService(api_key="test-key")
    service.client = FakeClient(
        [
            Exception("429 RESOURCE_EXHAUSTED retryDelay: \"1s\""),
            Exception("429 RESOURCE_EXHAUSTED retryDelay: \"1s\""),
            Exception("429 RESOURCE_EXHAUSTED retryDelay: \"1s\""),
            Exception("429 RESOURCE_EXHAUSTED retryDelay: \"1s\""),
        ]
    )

    with pytest.raises(Exception, match="RESOURCE_EXHAUSTED"):
        service.generate_structured_response("prompt", SimpleSchema)

    assert service.success_count == 0
    assert service.retry_429_count == 3
    assert service.failure_count == 1
    assert service.client.models.call_count == 4


def test_503_retry_then_success(monkeypatch):
    monkeypatch.setattr("job_agent.core.llm.time.sleep", lambda _s: None)

    service = LLMService(api_key="test-key")
    service.client = FakeClient(
        [
            Exception("503 UNAVAILABLE. {'error': {'code': 503, 'message': 'This model is currently experiencing high demand.'}}"),
            FakeResponse('{"value":"recovered"}'),
        ]
    )

    result = service.generate_structured_response("prompt", SimpleSchema)

    assert result.value == "recovered"
    assert service.success_count == 1
    assert service.retry_429_count == 1
    assert service.failure_count == 0
    assert service.client.models.call_count == 2

