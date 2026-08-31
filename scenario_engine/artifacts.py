from pathlib import Path
import shutil

def prepare_experiment_directory(
    experiment_dir: str,
) -> Path:
    path = Path(experiment_dir)

    if path.exists():
        shutil.rmtree(path)


    path.mkdir(
        parents=True,
        exist_ok=True,
    )

    return path
