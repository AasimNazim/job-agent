from unittest.mock import MagicMock

from job_agent.__main__ import evaluate_jobs_with_limits, generate_drafts_with_limit
from job_agent.models.job import Job


class FakeLLM:
    def __init__(self, success_count=0, retry_429_count=0, failure_count=0):
        self.success_count = success_count
        self.retry_429_count = retry_429_count
        self.failure_count = failure_count


def test_evaluation_limit_caps_gemini_calls():
    jobs = [
        Job(company_name="A", source="x", title=f"Junior Dev {i}", description="entry level", url=f"u{i}", content_hash=f"h{i}", status="NEW")
        for i in range(25)
    ]

    evaluator = MagicMock()
    evaluator.passes_entry_level_prefilter.return_value = True
    evaluator.evaluate_job.return_value = True
    llm = FakeLLM(success_count=20, retry_429_count=0, failure_count=0)

    stats = evaluate_jobs_with_limits(jobs, evaluator, llm, max_evaluations=20)

    assert stats["jobs_after_prefilter"] == 25
    assert stats["sent_to_gemini"] == 20
    assert stats["matched_jobs"] == 20
    assert evaluator.evaluate_job.call_count == 20


def test_generation_limit_caps_drafts():
    jobs = [
        Job(company_name="A", source="x", title=f"Junior Dev {i}", description="entry level", url=f"u{i}", content_hash=f"g{i}", status="MATCHED")
        for i in range(10)
    ]

    generator = MagicMock()
    generator.generate_draft.return_value = object()

    drafts_generated = generate_drafts_with_limit(jobs, generator, max_generations=5)

    assert drafts_generated == 5
    assert generator.generate_draft.call_count == 5
