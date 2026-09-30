import json
from pathlib import Path


def save_ground_truth(
    scenario,
    selected_vulnerabilities,
    output_dir: str = "generated",
):
    output_path = Path(output_dir)
    output_path.mkdir(
        parents=True,
        exist_ok=True,
    )

    ground_truth = {
            "scenario": scenario.name,
            "seed": scenario.seed,
            "vulnerabilities": selected_vulnerabilities,
    }

    file_path = output_path / "ground_truth.json"

    with file_path.open("w") as file:
        json.dump(
            ground_truth,
            file,
            indent=2,
        )

    return file_path
