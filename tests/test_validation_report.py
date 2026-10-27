import json
from types import SimpleNamespace

from scenario_engine.target_provider import (
    EvaluationMode,
    TargetDefinition,
    TargetOrigin,
    TargetSource,
)

from scenario_engine.target_evaluation import (
    EvaluationSummary,
    FindingEvaluation,
)

from scenario_engine.validation_report import save_validation_report


def test_validation_report_contains_target_ground_truth_metadata(tmp_path):
    scenario = SimpleNamespace(
        name="test-scenario",
        seed=43,
    )

    target = TargetDefinition(
        name="dvwa",
        source=TargetSource.CONTAINER,
        evaluation_mode=EvaluationMode.UNKNOWN_GROUND_TRUTH,
        image="cyber-range/dvwa:test",
        origin=TargetOrigin.GITHUB,
        repository="digininja/DVWA",
        ref="068d974487a297c155c48722f9fcf7180a83adc4",
        commit_sha="068d974487a297c155c48722f9fcf7180a83adc4",
        ground_truth_key="dvwa",
        ground_truth_loaded=True,
        ground_truth_complete=False,
        ground_truth_finding_count=2,
        ground_truth_scope="test scope",
        port=80,
        ground_truth_available=False,
        manual_validation=True,
    )

    report_path = save_validation_report(
        scenario=scenario,
        namespace="test-namespace",
        cluster_valid=True,
        taints_valid=True,
        workload_tolerations_valid=True,
        resources_valid=True,
        aggregate_resources_valid=True,
        workload_resources_valid=True,
        target_valid=True,
        scenario_valid=True,
        network_valid=True,
        vulnerabilities_valid=True,
        validated_vulnerabilities=[],
        output_dir=str(tmp_path),
        target=target,
    )

    with report_path.open("r", encoding="utf-8") as file:
        report = json.load(file)

    assert report["target"]["ground_truth_key"] == "dvwa"
    assert report["target"]["ground_truth_loaded"] is True
    assert report["target"]["ground_truth_complete"] is False
    assert report["target"]["ground_truth_finding_count"] == 2
    assert report["target"]["ground_truth_scope"] == "test scope"


def test_validation_report_allows_missing_target(tmp_path):
    scenario = SimpleNamespace(
        name="test-scenario",
        seed=43,
    )

    report_path = save_validation_report(
        scenario=scenario,
        namespace="test-namespace",
        cluster_valid=True,
        taints_valid=True,
        workload_tolerations_valid=True,
        resources_valid=True,
        aggregate_resources_valid=True,
        workload_resources_valid=True,
        target_valid=True,
        scenario_valid=True,
        network_valid=True,
        vulnerabilities_valid=True,
        validated_vulnerabilities=[],
        output_dir=str(tmp_path),
        target=None,
    )

    with report_path.open("r", encoding="utf-8") as file:
        report = json.load(file)

    assert report["target"] is None


def test_validation_report_contains_evaluation_summary(tmp_path):
    scenario = SimpleNamespace(
        name="test-scenario",
        seed=43,
    )

    evaluation = EvaluationSummary(
        results=[
            FindingEvaluation(
                finding_id="finding-001",
                matched=True,
            ),
            FindingEvaluation(
                finding_id="finding-002",
                matched=False,
            ),
        ],
        total_count=2,
        matched_count=1,
        unmatched_count=1,
        precision=0.5,
        recall=None,
        false_negative_count=None,
        f1_score=None,
    )

    report_path = save_validation_report(
        scenario=scenario,
        namespace="test-namespace",
        cluster_valid=True,
        taints_valid=True,
        workload_tolerations_valid=True,
        resources_valid=True,
        aggregate_resources_valid=True,
        workload_resources_valid=True,
        target_valid=True,
        scenario_valid=True,
        network_valid=True,
        vulnerabilities_valid=True,
        validated_vulnerabilities=[],
        output_dir=str(tmp_path),
        target=None,
        evaluation=evaluation,
    )

    with report_path.open("r", encoding="utf-8") as file:
        report = json.load(file)

    assert report["evaluation"]["total_count"] == 2
    assert report["evaluation"]["matched_count"] == 1
    assert report["evaluation"]["unmatched_count"] == 1
    assert report["evaluation"]["precision"] == 0.5
    assert report["evaluation"]["recall"] is None
    assert report["evaluation"]["false_negative_count"] is None
    assert report["evaluation"]["f1_score"] is None
