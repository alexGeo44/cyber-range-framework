import requests
import subprocess

DOCKER_HUB_API = "https://hub.docker.com/v2/repositories"


def list_repository_tags(
    repository: str,
    page_size: int = 25,
) -> list[str]:
    url = (
        f"{DOCKER_HUB_API}/{repository}/tags/"
        f"?page_size={page_size}"
    )

    response = requests.get(
        url,
        timeout=10,
    )
    response.raise_for_status()

    data = response.json()
    
    return [
        item["name"]
        for item in data.get("results", [])
    ]

def resolve_image_digest(image: str) -> str:
    result = subprocess.run(
        [
            "docker",
            "image",
            "inspect",
            image,
            "--format",
            "{{index .RepoDigests 0}}",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    repo_digest = result.stdout.strip()

    if "@" not in repo_digest:
        raise ValueError(
            f"could not resolve digest for image: {image}"
        )

    return repo_digest.split("@", 1)[1]

def pull_image(image: str) -> None:
    subprocess.run(
        [
            "docker",
            "pull",
            image,
        ],
        check=True,
    )
