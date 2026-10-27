import pytest

from scenario_engine.target_ground_truth_loader import (
    load_target_ground_truth,
    load_target_ground_truth_for_ref,
    target_ground_truth_exists,
)

def test_load_juice_shop_ground_truth():
    ground_truth = load_target_ground_truth(
        "targets/ground_truth/juice-shop/v20.3.0.yaml"
    )

    assert ground_truth.target_name == "vulnerable-web"
    assert ground_truth.ref == "v20.3.0"
    assert ground_truth.complete is False
    assert len(ground_truth.findings) == 2

def test_missing_ground_truth_file_raises_file_not_found():
    with pytest.raises(
        FileNotFoundError,
        match="target ground truth not found",
    ):
        load_target_ground_truth(
            "targets/ground_truth/missing-target/missing-ref.yaml"
        )

def test_target_ground_truth_exists():
    assert target_ground_truth_exists(
        "juice-shop",
        "v20.3.0",
    ) is True

    assert target_ground_truth_exists(
        "missing-target",
        "missing-ref",
    ) is False

def test_load_target_ground_truth_for_ref():
    ground_truth = load_target_ground_truth_for_ref(
        "juice-shop",
        "v20.3.0",
    )

    assert ground_truth.target_name == "vulnerable-web"
    assert ground_truth.ref == "v20.3.0"
    assert len(ground_truth.findings) == 2 
