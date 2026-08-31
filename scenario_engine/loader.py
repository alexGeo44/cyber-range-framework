from pathlib import Path

import yaml

from scenario_engine.models import ScenarioConfig

def load_scenario(path: str) -> ScenarioConfig:
    scenario_path = Path(path)

    with scenario_path.open("r") as file:
        data = yaml.safe_load(file)


    return ScenarioConfig(**data)
