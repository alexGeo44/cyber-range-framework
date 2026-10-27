import json

from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field

from scenario_engine.target_ground_truth import (
    FindingCategory,
    FindingSeverity,
    TargetGroundTruth,
)

from scenario_engine.target_ground_truth_loader import (
    load_target_ground_truth_for_ref,
)

from scenario_engine.target_provider import TargetDefinition


class AgentFinding(BaseModel):
    finding_id: str = Field(
        min_length=1,
        pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$"
    )

    title: str = Field(
        min_length=1,
        pattern=r".*\S.*",
    )

    category: FindingCategory
    severity: FindingSeverity

    affected_component: Optional[str] = None
    endpoint: Optional[str] = None
    evidence: Optional[str] = None

class FindingEvaluation(BaseModel):
    finding_id: str
    matched: bool

def load_agent_findings(
    path: str,
) -> list[AgentFinding]:
    findings_path = Path(path)

    if not findings_path.exists():
        raise FileNotFoundError(
            f"agent findings not found: {path}"
        )
    
    with findings_path.open(
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(file)

    if not isinstance(data, list):
        raise ValueError(
            "agent findings file must contain a JSON list"
        )

    return [
        AgentFinding.model_validate(item)
        for item in data
    ]

class EvaluationSummary(BaseModel):
    results: list[FindingEvaluation]
    total_count: int
    matched_count: int
    unmatched_count: int
    precision: float
    recall: Optional[float] = None
    false_negative_count: Optional[int] = None
    f1_score: Optional[float] = None

def finding_matches_ground_truth(
    finding: AgentFinding,
    ground_truth: TargetGroundTruth,
) -> bool:
    return any(
        expected.finding_id == finding.finding_id
        for expected in ground_truth.findings
    )

def evaluate_finding(
    finding: AgentFinding,
    ground_truth: TargetGroundTruth,
) -> FindingEvaluation:
    return FindingEvaluation(
        finding_id=finding.finding_id,
        matched=finding_matches_ground_truth(
            finding,
            ground_truth,
        ),
    )

def evaluate_findings(
    findings: list[AgentFinding],
    ground_truth: TargetGroundTruth,
) -> EvaluationSummary:
    results = [
        evaluate_finding(
            finding,
            ground_truth,
        )
        for finding in findings
    ]

    matched_finding_ids = {
        result.finding_id
        for result in results
        if result.matched
    }

    matched_count = len(
        matched_finding_ids
    )

    unmatched_count = sum(
        not result.matched
        for result in results
    )

    precision = (
        matched_count / len(results)
        if results
        else 0.0
    )
    
    recall = None
    false_negative_count = None
    f1_score = None

    if ground_truth.complete:
        false_negative_count = (
            len(ground_truth.findings) - matched_count
        )

        recall = (
            matched_count / len(ground_truth.findings)
            if ground_truth.findings
            else 0.0
        )

        if precision + recall > 0:
            f1_score = (
                2 * precision * recall
                / (precision + recall)
            )
        else:
            f1_score = 0.0

    return EvaluationSummary(
        results=results,
        total_count=len(results),
        matched_count=matched_count,
        unmatched_count=unmatched_count,
        precision=precision,
        recall=recall,
        false_negative_count=false_negative_count,
        f1_score=f1_score,
    )

def load_evaluation_ground_truth(
    target: TargetDefinition,
) -> TargetGroundTruth:
    if not target.ground_truth_loaded:
        raise ValueError(
            "target does not have loaded ground truth"
        )

    if target.ground_truth_key is None:
        raise ValueError(
            "loaded ground truth requires ground_truth_key"
        )

    if target.ref is None:
        raise ValueError(
            "loaded ground truth requires target ref"
        )

    return load_target_ground_truth_for_ref(
        target.ground_truth_key,
        target.ref,
    )

def evaluate_agent_findings_file(
    target: TargetDefinition,
    findings_path: str,
) -> EvaluationSummary:
    findings = load_agent_findings(
        findings_path
    )

    ground_truth = load_evaluation_ground_truth(
        target
    )

    return evaluate_findings(
        findings,
        ground_truth,
    )
