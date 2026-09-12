import pytest

from cost_quality_router.metrics import aggregate_metric, derive_total_tokens
from cost_quality_router.models import AttemptTrace, Metric, MetricApplicability, MetricEpistemicState


def metric(value, state, applicability=MetricApplicability.APPLICABLE, coverage=1.0):
    return Metric(value=value, unit="tokens", epistemic_state=state, applicability=applicability,
                  source="fixture", collection_method="fixture", coverage=coverage)


def test_actual_estimated_mixed_and_zero_semantics():
    assert aggregate_metric([metric(0, MetricEpistemicState.ACTUAL)], "tokens").model_dump(include={"value", "epistemic_state"}) == {"value": 0, "epistemic_state": MetricEpistemicState.ACTUAL}
    assert aggregate_metric([metric(2, MetricEpistemicState.ESTIMATED)], "tokens").epistemic_state is MetricEpistemicState.ESTIMATED
    assert aggregate_metric([metric(2, MetricEpistemicState.ACTUAL), metric(3, MetricEpistemicState.ESTIMATED)], "tokens").epistemic_state is MetricEpistemicState.ESTIMATED


def test_unknown_empty_and_coverage_remain_explicit():
    aggregate = aggregate_metric([metric(2, MetricEpistemicState.ACTUAL, coverage=.5), metric(None, MetricEpistemicState.UNKNOWN, coverage=0)], "tokens")
    assert aggregate.value is None and aggregate.epistemic_state is MetricEpistemicState.UNKNOWN and aggregate.coverage == .25
    empty = aggregate_metric([], "tokens")
    assert empty.applicability is MetricApplicability.APPLICABLE and empty.epistemic_state is MetricEpistemicState.UNKNOWN and empty.coverage == 0


def test_not_applicable_is_distinct_and_invalid_combinations_fail():
    not_applicable = metric(None, MetricEpistemicState.UNPRICED, MetricApplicability.NOT_APPLICABLE)
    assert aggregate_metric([not_applicable], "tokens").applicability is MetricApplicability.NOT_APPLICABLE
    with pytest.raises(ValueError):
        metric(0, MetricEpistemicState.ACTUAL, MetricApplicability.NOT_APPLICABLE)
    with pytest.raises(ValueError):
        metric(None, MetricEpistemicState.UNKNOWN, MetricApplicability.NOT_APPLICABLE)


def test_applicable_metric_units_must_match_and_not_applicable_does_not_conflict():
    milliseconds = Metric(value=500, unit="ms", epistemic_state=MetricEpistemicState.ACTUAL,
                          applicability=MetricApplicability.APPLICABLE, source="fixture", collection_method="fixture", coverage=1)
    not_applicable_ms = Metric(value=None, unit="ms", epistemic_state=MetricEpistemicState.UNPRICED,
                               applicability=MetricApplicability.NOT_APPLICABLE, source="fixture", collection_method="fixture", coverage=1)
    with pytest.raises(ValueError, match="unit"):
        aggregate_metric([metric(10, MetricEpistemicState.ACTUAL), milliseconds], "tokens")
    assert aggregate_metric([metric(10, MetricEpistemicState.ACTUAL), not_applicable_ms], "tokens").value == 10


def trace(input_metric, output_metric):
    known = metric(1, MetricEpistemicState.ACTUAL)
    return AttemptTrace(experiment_id="experiment", run_id="run", case_id="case", route_id="R1", route_version="v001",
                        attempt_index=1, runtime="local", provider="local", model=None, model_digest=None,
                        input_tokens=input_metric, output_tokens=output_metric, latency_ms=known, model_calls=known,
                        human_interventions=known, verifier_result=None, status="completed")


def test_total_tokens_is_a_single_deterministic_epistemic_derivation():
    actual = derive_total_tokens(trace(metric(2, MetricEpistemicState.ACTUAL), metric(3, MetricEpistemicState.ACTUAL)))
    estimated = derive_total_tokens(trace(metric(2, MetricEpistemicState.ACTUAL), metric(3, MetricEpistemicState.ESTIMATED)))
    unknown = derive_total_tokens(trace(metric(None, MetricEpistemicState.UNKNOWN), metric(3, MetricEpistemicState.ACTUAL)))
    unavailable = derive_total_tokens(trace(
        metric(None, MetricEpistemicState.UNPRICED, MetricApplicability.NOT_APPLICABLE), metric(3, MetricEpistemicState.ACTUAL)))
    assert actual.value == 5 and actual.epistemic_state is MetricEpistemicState.ACTUAL
    assert estimated.value == 5 and estimated.epistemic_state is MetricEpistemicState.ESTIMATED
    assert unknown.value is None and unknown.epistemic_state is MetricEpistemicState.UNKNOWN
    assert unavailable.applicability is MetricApplicability.NOT_APPLICABLE
