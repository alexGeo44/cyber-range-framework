import pytest
from pydantic import ValidationError

from scenario_engine.target_ground_truth import TargetGroundTruth

def test_complete_ground_truth_requires_findings():
    with pytest.raises(
        ValidationError,
        match="complete target ground truth must contain at least one finding",
    ):
        TargetGroundTruth(
            target_name="test-target",
            repository="example/repo",
            ref="v1.0.0",
            scope="test scope",
            image_digest="sha256:" + "a" * 64,
            complete=True,
            findings=[],
        )

def test_complete_ground_truth_requires_immutable_identity():
    with pytest.raises(
        ValidationError,
        match="complete target ground truth must define an immutable target identity",
    ):
        TargetGroundTruth(
            target_name="test-target",
            repository="example/repo",
            ref="v1.0.0",
            scope="test scope",
            complete=True,
            findings=[
                {
                    "finding_id": "test-finding-001",
                    "title": "Test finding",
                    "category": "other",
                    "severity": "low",
                    "source": "manual_verification",
                }
            ],
        )

def test_ground_truth_rejects_both_immutable_identities():
    with pytest.raises(
        ValidationError,
        match="target ground truth must define either image_digest or commit_sha, not both",
    ):
        TargetGroundTruth(
            target_name="test-target",
            repository="example/repo",
            ref="v1.0.0",
            scope="test scope",
            image_digest="sha256:" + "a" * 64,
            commit_sha="b" * 40,
            complete=False,
            findings=[],
        )

def test_ground_truth_rejects_both_duplicate_findings_ids():
    with pytest.raises(
        ValidationError,
        match="target ground truth contains duplicate finding_id values",
    ):
        TargetGroundTruth(
            target_name="test-target",
            repository="example/repo",
            ref="v1.0.0",
            scope="test scope",
            complete=False,
            findings=[
                {
                    "finding_id": "duplicate-finding",
                    "title": "First finding",
                    "category": "other",
                    "severity": "low",
                    "source": "manual_verification",
                },
                {
                    "finding_id": "duplicate-finding",
                    "title": "Second finding",
                    "category": "other",
                    "severity": "low",
                    "source": "manual_verification",
                },
            ],

        )

def test_repository_finding_requires_reference():
    with pytest.raises(
        ValidationError,
        match="repository and official documentation findings must define a reference",
    ):
        TargetGroundTruth(
            target_name="test-target",
            repository="example/repo",
            ref="v1.0.0",
            scope="test scope",
            complete=False,
            findings=[
                {
                    "finding_id": "test-finding-001",
                    "title": "Test finding",
                    "category": "other",
                    "severity": "low",
                    "source": "repository",
                }
            ],
        )

def test_manual_verification_finding_does_not_require_reference():
    ground_truth = TargetGroundTruth(
        target_name="test-target",
        repository="example/repo",
        ref="v1.0.0",
        scope="test scope",
        complete=False,
        findings=[
            {
                "finding_id": "test-finding-001",
                "title": "Test finding",
                "category": "other",
                "severity": "low",
                "source": "manual_verification",
            }
        ],
    )

    assert len(ground_truth.findings) == 1
    assert ground_truth.findings[0].reference is None

def test_finding_id_rejects_invalid_format():
    with pytest.raises(ValidationError):
        TargetGroundTruth(
            target_name="test-target",
            repository="example/repo",
            ref="v1.0.0",
            scope="test scope",
            complete=False,
            findings=[
                {
                    "finding_id": "Test Finding",
                    "title": "Test finding",
                    "category": "other",
                    "severity": "low",
                    "source": "manual_verification"
                }
            ],
        )

def test_finding_endpoint_requires_leading_slash():
    with pytest.raises(ValidationError):
        TargetGroundTruth(
            target_name="test-target",
            repository="example/repo",
            ref="v1.0.0",
            scope="test scope",
            complete=False,
            findings=[
                {
                    "finding_id": "test-finding-001",
                    "title": "Test finding",
                    "category": "other",
                    "severity": "low",
                    "endpoint": "rest/test",
                    "source": "manual_verification",
                }
            ],
        )

def test_ground_truth_rejects_invalid_image_digest():
    with pytest.raises(ValidationError):
        TargetGroundTruth(
            target_name="test-target",
            repository="example/repo",
            ref="v1.0.0",
            scope="test scope",
            image_digest="sha256:abc123",
            complete=False,
            findings=[],
        )

def test_ground_truth_rejects_invalid_commit_sha():
    with pytest.raises(ValidationError):
        TargetGroundTruth(
            target_name="test-target",
            repository="example/repo",
            ref="v1.0.0",
            scope="test scope",
            commit_sha="abc123",
            complete=False,
            findings=[],
            )

def test_ground_truth_rejects_blank_scope():
    with pytest.raises(ValidationError):
        TargetGroundTruth(
            target_name="test-target",
            repository="example/repo",
            ref="v1.0.0",
            scope=" ",
            complete=False,
            findings=[],
        )

def test_complete_ground_truth_accepts_valid_immutable_identity():
    ground_truth = TargetGroundTruth(
        target_name="test-target",
        repository="example/repo",
        ref="v1.0.0",
        scope="test scope",
        image_digest="sha256:" + "a" * 64,
        complete=True,
        findings=[
            {
                "finding_id": "test-finding-001",
                "title": "Test finding",
                "category": "other",
                "severity": "low",
                "source": "manual_verification",
            }
        ],
    )

    assert ground_truth.complete is True
    assert len(ground_truth.findings) == 1 
