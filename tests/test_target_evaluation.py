import pytest
import json
import pytest

from scenario_engine.target_evaluation import (
    AgentFinding,
    FindingEvaluation,
    EvaluationSummary,
    evaluate_finding,
    evaluate_findings,
    evaluate_agent_findings_file,
    finding_matches_ground_truth,
    load_agent_findings,
    load_evaluation_ground_truth,
)
from scenario_engine.target_provider import (
    EvaluationMode,
    TargetDefinition,
    TargetOrigin,
    TargetSource,
)

from scenario_engine.target_ground_truth import (
    GroundTruthSource,
    TargetGroundTruth,
    TargetGroundTruthFinding,
)

from scenario_engine.validation_report import (
    save_validation_report,
)

from pathlib import Path

from types import SimpleNamespace

def test_load_evaluation_ground_truth_for_dvwa():
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

    ground_truth = load_evaluation_ground_truth(target)

    assert ground_truth.target_name == "dvwa"
    assert ground_truth.ref == target.ref
    assert len(ground_truth.findings) == 2


def test_load_evaluation_ground_truth_requires_loaded_ground_truth():
    target = TargetDefinition(
        name="webgoat",
        source=TargetSource.CONTAINER,
        evaluation_mode=EvaluationMode.UNKNOWN_GROUND_TRUTH,
        image="webgoat/webgoat:test",
        origin=TargetOrigin.DOCKER_HUB,
        repository="webgoat/webgoat",
        ref="v1.0.0",
        ground_truth_key="webgoat",
        ground_truth_loaded=False,
        port=8080,
        ground_truth_available=False,
        manual_validation=True,
    )

    with pytest.raises(
        ValueError,
        match="target does not have loaded ground truth",
    ):
        load_evaluation_ground_truth(target)

def test_agent_finding_accepts_valid_data():
    finding = AgentFinding(
        finding_id="test-finding-001",
        title="Test finding",
        category="other",
        severity="low",
        affected_component="test-component",
        endpoint="/test",
        evidence="test evidence",
    )

    assert finding.finding_id == "test-finding-001"
    assert finding.category.value == "other"
    assert finding.severity.value == "low"
    assert finding.endpoint == "/test"

def test_agent_finding_rejects_invalid_finding_id():
    with pytest.raises(ValueError):
        AgentFinding(
            finding_id="Invalid Finding ID",
            title="Test finding",
            category="other",
            severity="low",
        )

def test_finding_matches_ground_truth_returns_true_for_matching_id():
    ground_truth = load_evaluation_ground_truth(
        TargetDefinition(
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
    )

    finding = AgentFinding(
        finding_id="dvwa-sqli-001",
        title="SQL Injection",
        category="injection",
        severity="high",
    )

    assert finding_matches_ground_truth(
        finding,
        ground_truth,
    ) is True

def test_finding_matches_ground_truth_returns_false_for_unknown_id():
    ground_truth = load_evaluation_ground_truth(
        TargetDefinition(
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
    )

    finding = AgentFinding(
        finding_id="unknown-finding-001",
        title="Unknown finding",
        category="other",
        severity="low",
    )

    assert finding_matches_ground_truth(
        finding,
        ground_truth,
    ) is False


def test_evaluate_finding_returns_matched_result():
    ground_truth = load_evaluation_ground_truth(
        TargetDefinition(
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
    )

    finding = AgentFinding(
        finding_id="dvwa-sqli-001",
        title="SQL Injection",
        category="injection",
        severity="high",
    )

    result = evaluate_finding(
        finding,
        ground_truth,
    )

    assert isinstance(result, FindingEvaluation)
    assert result.finding_id == "dvwa-sqli-001"
    assert result.matched is True

def test_evaluate_finding_returns_unmatched_result():
    ground_truth = load_evaluation_ground_truth(
        TargetDefinition(
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
    )

    finding = AgentFinding(
        finding_id="unknown-finding-001",
        title="Unknown finding",
        category="other",
        severity="low",
    )

    result = evaluate_finding(
        finding,
        ground_truth,
    )

    assert isinstance(result, FindingEvaluation)
    assert result.finding_id == "unknown-finding-001"
    assert result.matched is False

def test_evaluate_findings_returns_results_for_all_findings():
    ground_truth = load_evaluation_ground_truth(
        TargetDefinition(
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
    )

    findings = [
        AgentFinding(
            finding_id="dvwa-sqli-001",
            title="SQL Injection",
            category="injection",
            severity="high",
        ),
        AgentFinding(
            finding_id="unknown-finding-001",
            title="Unknown finding",
            category="other",
            severity="low",
        ),
    ]

    result = evaluate_findings(
        findings,
        ground_truth,
    )

    assert isinstance(result, EvaluationSummary)
    assert len(result.results) == 2
    assert result.total_count == 2
    assert result.matched_count == 1
    assert result.unmatched_count == 1
    assert result.precision == 0.5
    assert result.recall is None
    assert result.false_negative_count is None
    assert result.f1_score is None

    assert result.results[0].finding_id == "dvwa-sqli-001"
    assert result.results[0].matched is True

    assert result.results[1].finding_id == "unknown-finding-001"
    assert result.results[1].matched is False

def test_evaluate_findings_handles_empty_findings():
    ground_truth = load_evaluation_ground_truth(
        TargetDefinition(
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
    )

    result = evaluate_findings(
        [],
        ground_truth,
    )

    assert result.total_count == 0
    assert result.matched_count == 0
    assert result.unmatched_count == 0
    assert result.precision == 0.0
    assert result.results == []

def test_evaluate_findings_calculates_recall_for_complete_ground_truth():
    ground_truth = TargetGroundTruth(
        target_name="test-target",
        repository="example/test-target",
        ref="v1.0.0",
        scope="complete test scope",
        image_digest=(
            "sha256:"
            "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
            "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
        ),
        complete=True,
        findings=[
            TargetGroundTruthFinding(
                finding_id="finding-001",
                title="First finding",
                category="injection",
                severity="high",
                source=GroundTruthSource.MANUAL_VERIFICATION,
            ),
            TargetGroundTruthFinding(
                finding_id="finding-002",
                title="Second finding",
                category="xss",
                severity="medium",
                source=GroundTruthSource.MANUAL_VERIFICATION,
            ),
        ],
    )

    findings = [
        AgentFinding(
            finding_id="finding-001",
            title="First finding",
            category="injection",
            severity="high",
        ),
    ]

    result = evaluate_findings(
        findings,
        ground_truth,
    )

    assert result.total_count == 1
    assert result.matched_count == 1
    assert result.unmatched_count == 0
    assert result.precision == 1.0
    assert result.recall == 0.5
    assert result.false_negative_count == 1
    assert result.f1_score == pytest.approx(2 / 3)

def test_evaluate_findings_handles_zero_matches_for_complete_ground_truth():
    ground_truth = TargetGroundTruth(
        target_name="test-target",
        repository="example/test-target",
        ref="v1.0.0",
        scope="complete test scope",
        image_digest=(
            "sha256:"
            "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
            "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
        ),
        complete=True,
        findings=[
            TargetGroundTruthFinding(
                finding_id="finding-001",
                title="First finding",
                category="injection",
                severity="high",
                source=GroundTruthSource.MANUAL_VERIFICATION,
            ),
            TargetGroundTruthFinding(
                finding_id="finding-002",
                title="Second finding",
                category="xss",
                severity="medium",
                source=GroundTruthSource.MANUAL_VERIFICATION,
            ),
        ],
    )

    findings = [
        AgentFinding(
            finding_id="unknown-finding-001",
            title="Unknown finding",
            category="other",
            severity="low",
        ),
    ]

    result = evaluate_findings(
        findings,
        ground_truth,
    )

    assert result.total_count == 1
    assert result.matched_count == 0
    assert result.unmatched_count == 1
    assert result.precision == 0.0
    assert result.recall == 0.0
    assert result.false_negative_count == 2
    assert result.f1_score == 0.0

def test_load_agent_findings_loads_valid_json(tmp_path):
    findings_path = tmp_path / "agent_findings.json"

    findings_path.write_text(
        json.dumps(
            [
                {
                    "finding_id": "dvwa-sqli-001",
                    "title": "SQL Injection",
                    "category": "injection",
                    "severity": "high",
                    "affected_component": "sqli",
                    "endpoint": "/vulnerabilities/sqli/",
                    "evidence": "Observed SQL injection behavior",
                }
            ]
        ),
        encoding="utf-8",
    )

    findings = load_agent_findings(
        str(findings_path)
    )

    assert len(findings) == 1
    assert isinstance(findings[0], AgentFinding)
    assert findings[0].finding_id == "dvwa-sqli-001"
    assert findings[0].category.value == "injection"
    assert findings[0].severity.value == "high"

def test_load_agent_findings_requires_existing_file(tmp_path):
    missing_path = tmp_path / "missing.json"

    with pytest.raises(
        FileNotFoundError,
        match="agent findings not found",
    ):
        load_agent_findings(
            str(missing_path)
        )

def test_load_agent_findings_requires_json_list(tmp_path):
    findings_path = tmp_path / "agent_findings.json"

    findings_path.write_text(
        json.dumps(
            {
                "finding_id": "dvwa-sqli-001",
                "title": "SQL Injection",
                "category": "injection",
                "severity": "high",
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="agent findings file must contain a JSON list",
    ):
        load_agent_findings(
            str(findings_path)
        )


def test_load_agent_findings_rejects_invalid_finding(tmp_path):
    findings_path = tmp_path / "agent_findings.json"

    findings_path.write_text(
        json.dumps(
            [
                {
                    "finding_id": "Invalid Finding ID",
                    "title": "Invalid finding",
                    "category": "other",
                    "severity": "low",
                }
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError):
        load_agent_findings(
            str(findings_path)
        )

def test_evaluate_agent_findings_file_returns_summary(tmp_path):
    findings_path = tmp_path / "agent_findings.json"

    findings_path.write_text(
        json.dumps(
            [
                {
                    "finding_id": "dvwa-sqli-001",
                    "title": "SQL Injection",
                    "category": "injection",
                    "severity": "high",
                },
                {
                    "finding_id": "unknown-finding-001",
                    "title": "Unknown finding",
                    "category": "other",
                    "severity": "low",
                },
            ]
        ),
        encoding="utf-8",
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

    result = evaluate_agent_findings_file(
        target,
        str(findings_path),
    )

    assert isinstance(result, EvaluationSummary)
    assert result.total_count == 2
    assert result.matched_count == 1
    assert result.unmatched_count == 1
    assert result.precision == 0.5
    assert result.recall is None

def test_validation_report_without_evaluation_keeps_null(tmp_path):
    scenario = SimpleNamespace(
        name="test-scenario",
        seed=1,
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
        evaluation=None,
    )

    report = json.loads(
        Path(report_path).read_text(
            encoding="utf-8"
        )
    )

    assert report["evaluation"] is None


def test_evaluate_findings_does_not_double_count_duplicate_matches():
    ground_truth = TargetGroundTruth(
        target_name="test-target",
        repository="example/test-target",
        ref="v1.0.0",
        scope="complete test scope",
        image_digest=(
            "sha256:"
            "cccccccccccccccccccccccccccccccc"
            "cccccccccccccccccccccccccccccccc"
        ),
        complete=True,
        findings=[
            TargetGroundTruthFinding(
                finding_id="finding-001",
                title="First finding",
                category="injection",
                severity="high",
                source=GroundTruthSource.MANUAL_VERIFICATION,
            ),
            TargetGroundTruthFinding(
                finding_id="finding-002",
                title="Second finding",
                category="xss",
                severity="medium",
                source=GroundTruthSource.MANUAL_VERIFICATION,
            ),
        ],
    )

    findings = [
        AgentFinding(
            finding_id="finding-001",
            title="First finding",
            category="injection",
            severity="high",
        ),
        AgentFinding(
            finding_id="finding-001",
            title="Duplicate first finding",
            category="injection",
            severity="high",
        ),
    ]

    result = evaluate_findings(
        findings,
        ground_truth,
    )

    assert result.matched_count == 1
    assert result.unmatched_count == 0
    assert result.false_negative_count == 1
    assert result.recall == 0.5
