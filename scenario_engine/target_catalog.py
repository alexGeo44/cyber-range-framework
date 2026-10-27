from scenario_engine.target_provider import (
    EvaluationMode,
    TargetDefinition,
    TargetSource,
)

TARGET_CATALOG = {
    "vulnerable-web": TargetDefinition(
        name="vulnerable-web",
        source=TargetSource.CONTAINER,
        evaluation_mode=EvaluationMode.KNOWN_GROUND_TRUTH,
        image="bkimminich/juice-shop:v17.3.0",
        port=3000,
        ground_truth_available=True,

    ),
}


def get_target(name: str) -> TargetDefinition:
    if name not in TARGET_CATALOG:
        raise ValueError(f"unknown target: {name}")

    return TARGET_CATALOG[name]
