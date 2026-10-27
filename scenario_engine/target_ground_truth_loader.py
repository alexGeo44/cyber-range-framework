from pathlib import Path

import yaml

from scenario_engine.target_ground_truth import TargetGroundTruth


def load_target_ground_truth(
    path: str,
) -> TargetGroundTruth:
    ground_truth_path = Path(path)

    if not ground_truth_path.exists():
        raise FileNotFoundError(
            f"target ground truth not found: {path}"
        )

    with ground_truth_path.open(
        "r",
        encoding="utf-8",
    ) as file:
        data = yaml.safe_load(file)

    return TargetGroundTruth.model_validate(data)


def get_target_ground_truth_path(
    ground_truth_key: str,
    ref: str,
) -> Path:
    return Path(
        "targets",
        "ground_truth",
        ground_truth_key,
        f"{ref}.yaml",
    )

def load_target_ground_truth_for_ref(
    ground_truth_key: str,
    ref: str,
) -> TargetGroundTruth:
    path = get_target_ground_truth_path(
        ground_truth_key,
        ref,
    )

    return load_target_ground_truth(
        str(path)
    )

def target_ground_truth_exists(
    ground_truth_key: str,
    ref: str,
) -> bool:
    path = get_target_ground_truth_path(
        ground_truth_key,
        ref,
    )

    return path.exists()
