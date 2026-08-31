import json
from pathlib import Path

def save_validation_report(
    scenario,
    namespace: str,
    cluster_valid: bool,
    taints_valid: bool,
    workload_tolerations_valid: bool,
    resources_valid: bool,
    aggregate_resources_valid: bool,
    workload_resources_valid: bool,
    scenario_valid: bool,
    network_valid: bool,
    vulnerabilities_valid: bool,
    validated_vulnerabilities,
    output_dir: str,
):
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)


    report = {
        "scenario": scenario.name,
        "seed": scenario.seed,
        "namespace": namespace,
        "cluster_valid": cluster_valid,
        "taints_valid": taints_valid,
        "workload_tolerations_valid": workload_tolerations_valid,
        "resources_valid": resources_valid,
        "aggregate_resources_valid": aggregate_resources_valid,
        "workload_resources_valid": workload_resources_valid,
        "scenario_valid": scenario_valid,
        "network_valid": network_valid,
        "vulnerabilities_valid": vulnerabilities_valid,
        "validated_vulnerabilities": validated_vulnerabilities,
    }

    file_path = output_path / "validation.json"

    with file_path.open("w") as file:
        json.dump(
            report,
            file,
            indent=2,
        )

    return file_path
