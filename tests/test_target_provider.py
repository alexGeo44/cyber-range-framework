import pytest
from pydantic import ValidationError

from scenario_engine.target_provider import (
    EvaluationMode,
    TargetDefinition,
    TargetSource,
)


def test_known_ground_truth_requires_ground_truth_available():
    with pytest.raises(
        ValidationError,
        match="known-ground-truth targets must have ground_truth_available=True"
    ):
        TargetDefinition(
            name="test-target",
            source=TargetSource.CONTAINER,
            evaluation_mode=EvaluationMode.KNOWN_GROUND_TRUTH,
            image="example/test:1.0",
            port=8080,
            ground_truth_available=False,
        )

def test_unknown_ground_truth_rejects_ground_truth_available():
    with pytest.raises(
        ValidationError,
        match="unknown-ground-truth targets cannot have ground_truth_available=True",
    ):
        TargetDefinition(
            name="test-target",
            source=TargetSource.CONTAINER,
            evaluation_mode=EvaluationMode.UNKNOWN_GROUND_TRUTH,
            image="example/test:1.0",
            port=8080,
            ground_truth_available=True,
        )

def test_known_ground_truth_accepts_ground_truth_available():
    target = TargetDefinition(
        name="test-target",
        source=TargetSource.CONTAINER,
        evaluation_mode=EvaluationMode.KNOWN_GROUND_TRUTH,
        image="example:1.0",
        port=8080,
        ground_truth_available=True,
    )

    assert target.ground_truth_available is True

def test_complete_ground_truth_requires_loaded_ground_truth():
    with pytest.raises(
        ValidationError,
        match="complete ground truth requires ground_truth_loaded=True",
    ):
        TargetDefinition(
            name="test-target",
            source=TargetSource.CONTAINER,
            evaluation_mode=EvaluationMode.UNKNOWN_GROUND_TRUTH,
            image="example/test:1.0",
            port=8080,
            ground_truth_complete=True,
            ground_truth_loaded=False,
        )

def test_complete_ground_truth_accepts_loaded_ground_truth():
    target = TargetDefinition(
        name="test-target",
        source=TargetSource.CONTAINER,
        evaluation_mode=EvaluationMode.UNKNOWN_GROUND_TRUTH,
        image="example/test:1.0",
        port=8080,
        ground_truth_key="test-ground-truth",
        ground_truth_complete=True,
        ground_truth_loaded=True,
        ground_truth_finding_count=1,
    )

    assert target.ground_truth_complete is True
    assert target.ground_truth_loaded is True

def test_ground_truth_findings_require_loaded_ground_truth():
    with pytest.raises(
        ValidationError,
        match="ground truth findings require ground_truth_loaded=True",
    ):
        TargetDefinition(
            name="test-target",
            source=TargetSource.CONTAINER,
            evaluation_mode=EvaluationMode.UNKNOWN_GROUND_TRUTH,
            image="example/test:1.0",
            port=8080,
            ground_truth_loaded=False,
            ground_truth_finding_count=2,
        )

def test_ground_truth_findings_accepts_loaded_ground_truth():
    target = TargetDefinition(
        name="test-target",
        source=TargetSource.CONTAINER,
        evaluation_mode=EvaluationMode.UNKNOWN_GROUND_TRUTH,
        image="example/test:1.0",
        port=8080,
        ground_truth_key="test-ground-truth",
        ground_truth_loaded=True,
        ground_truth_finding_count=2,
    )

    assert target.ground_truth_loaded is True
    assert target.ground_truth_finding_count == 2

def test_complete_ground_truth_requires_findings():
    with pytest.raises(
        ValidationError,
        match="complete ground truth requires at least one finding",
    ):
        TargetDefinition(
            name="test-target",
            source=TargetSource.CONTAINER,
            evaluation_mode=EvaluationMode.UNKNOWN_GROUND_TRUTH,
            image="example/test:1.0",
            port=8080,
            ground_truth_loaded=True,
            ground_truth_complete=True,
            ground_truth_finding_count=0,
        )

def test_ground_truth_scope_requires_loaded_ground_truth():
    with pytest.raises(
        ValidationError,
        match="ground truth scope requires ground_truth_loaded=True",
    ):
        TargetDefinition(
            name="test-target",
            source=TargetSource.CONTAINER,
            evaluation_mode=EvaluationMode.UNKNOWN_GROUND_TRUTH,
            image="example/test:1.0",
            port=8080,
            ground_truth_loaded=False,
            ground_truth_scope="test scope"

        )

def test_ground_truth_scope_accepts_loaded_ground_truth():
    target = TargetDefinition(
        name="test-target",
        source=TargetSource.CONTAINER,
        evaluation_mode=EvaluationMode.UNKNOWN_GROUND_TRUTH,
        image="example/test:1.0",
        port=8080,
        ground_truth_key="test-ground-truth",
        ground_truth_loaded=True,
        ground_truth_scope="test scope",
    )

    assert target.ground_truth_loaded is True
    assert target.ground_truth_scope == "test scope"

def test_loaded_ground_truth_requires_ground_truth_key():
    with pytest.raises(
        ValidationError,
        match="loaded ground truth requires ground_truth_key"
    ):
        TargetDefinition(
            name="test-target",
            source=TargetSource.CONTAINER,
            evaluation_mode=EvaluationMode.UNKNOWN_GROUND_TRUTH,
            image="example/test:1.0",
            port=8080,
            ground_truth_loaded=True,
        )
