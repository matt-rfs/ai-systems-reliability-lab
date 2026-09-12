from __future__ import annotations

from .models import AttemptTrace, Metric, MetricApplicability, MetricEpistemicState


def aggregate_metric(metrics: list[Metric], unit: str) -> Metric:
    if not metrics:
        return Metric(value=None, unit=unit, epistemic_state=MetricEpistemicState.UNKNOWN,
                      applicability=MetricApplicability.APPLICABLE, source="aggregate",
                      collection_method="deterministic aggregation", coverage=0.0)
    applicable = [metric for metric in metrics if metric.applicability is MetricApplicability.APPLICABLE]
    if not applicable:
        return Metric(value=None, unit=unit, epistemic_state=MetricEpistemicState.UNPRICED,
                      applicability=MetricApplicability.NOT_APPLICABLE, source="aggregate",
                      collection_method="deterministic aggregation", coverage=1.0)
    if any(metric.unit != unit for metric in applicable):
        raise ValueError("applicable metrics must use the requested unit")
    coverage = sum(metric.coverage for metric in applicable) / len(applicable)
    if any(metric.epistemic_state in {MetricEpistemicState.UNKNOWN, MetricEpistemicState.UNPRICED} for metric in applicable):
        return Metric(value=None, unit=unit, epistemic_state=MetricEpistemicState.UNKNOWN,
                      applicability=MetricApplicability.APPLICABLE, source="aggregate",
                      collection_method="deterministic aggregation", coverage=coverage)
    state = (MetricEpistemicState.ACTUAL if all(metric.epistemic_state is MetricEpistemicState.ACTUAL for metric in applicable)
             else MetricEpistemicState.ESTIMATED)
    return Metric(value=sum(metric.value for metric in applicable if metric.value is not None), unit=unit,
                  epistemic_state=state,
                  applicability=MetricApplicability.APPLICABLE, source="aggregate",
                  collection_method="deterministic aggregation", coverage=coverage)


def derive_total_tokens(trace: AttemptTrace) -> Metric:
    """Derive total tokens only from both applicable input and output components."""
    components = [trace.input_tokens, trace.output_tokens]
    if any(metric.applicability is not MetricApplicability.APPLICABLE for metric in components):
        return Metric(value=None, unit="tokens", epistemic_state=MetricEpistemicState.UNPRICED,
                      applicability=MetricApplicability.NOT_APPLICABLE, source="trace token derivation",
                      collection_method="deterministic aggregation", coverage=1.0)
    return aggregate_metric(components, "tokens").model_copy(update={
        "source": "trace token derivation",
        "collection_method": "deterministic aggregation",
    })
