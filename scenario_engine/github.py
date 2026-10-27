from pathlib import Path
import shutil
import subprocess

def build_github_target(
    repository: str,
    ref: str,
    dockerfile: str,
    image_name: str,
    work_dir: str = "generated/github-targets",

) -> tuple[str, str]:
    base_path = Path(work_dir)
    base_path.mkdir(
        parents=True,
        exist_ok=True,
    )

    repo_name = repository.split("/")[-1]

    target_path = base_path / repo_name

    if target_path.exists():
        shutil.rmtree(target_path)

    repository_url = (
        f"https://github.com/{repository}.git"
    )

    subprocess.run(
        [
            "git",
            "clone",
            repository_url,
            str(target_path),
        ],
        check=True
    )

    subprocess.run(
        [
            "git",
            "-C",
            str(target_path),
            "checkout",
            ref,
        ],
        check=True,
    )

    result = subprocess.run(
        [
            "git",
            "-C",
            str(target_path),
            "rev-parse",
            "HEAD",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    commit_sha = result.stdout.strip()
    short_commit = commit_sha[:12]
    
    print(f"Resolved Git commit: {commit_sha}")

    dockerfile_path = (
        target_path / dockerfile
    )

    if not dockerfile_path.exists():
        raise FileNotFoundError(
            f"Dockerfile not found: {dockerfile_path}"
        )
    
    resolved_image_name = f"{image_name.split(':')[0]}:{short_commit}"

    subprocess.run(
        [
            "docker",
            "build",
            "-f",
            str(dockerfile_path),
            "-t",
            resolved_image_name,
            str(target_path),
        ],
        check=True,
    )

    subprocess.run(
        [
            "minikube",
            "image",
            "load",
            resolved_image_name,
            "-p",
            "cyber-range",
        ],
        check=True,
    )


    return resolved_image_name, commit_sha
