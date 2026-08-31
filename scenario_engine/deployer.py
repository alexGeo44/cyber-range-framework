from pathlib import Path
import subprocess

import time

def ensure_namespace(namespace: str) -> None:
    result = subprocess.run(
        [
            "kubectl",
            "get",
            "namespace",
            namespace,
        ],
        text=True,
        capture_output=True,
    )

    if result.returncode == 0:
        return

    subprocess.run(
        [
            "kubectl",
            "create",
            "namespace",
            namespace,
        ],
        check=True,
        text=True,
        capture_output=True,
    )


def deploy_manifests(
    manifest_dir: str = "generated/manifests",
    namespace: str = "default",
) -> None:

    path = Path(manifest_dir)

    if not path.exists():
        raise FileNotFoundError(
            f"Manifest directory not found: {path}"
        )

    ensure_namespace(namespace)

    result = subprocess.run(
        [
            "kubectl",
            "apply",
            "-f",
            str(path),
            "-n",
            namespace,
        ],
        check=True,
        text=True,
        capture_output=True,
    )

    print(result.stdout)


def delete_namespace(namespace: str) -> None:
    subprocess.run(
        [
            "kubectl",
            "delete",
            "namespace",
            namespace,
            "--ignore-not-found",
        ],
        text=True,
        capture_output=True,
    )


def reset_namespace(
    namespace: str,
    timeout: int = 60,
    interval: int = 2,
) -> None:
    delete_namespace(namespace)

    start_time = time.time()

    while time.time() - start_time < timeout:
        result = subprocess.run(
            [
                "kubectl",
                "get",
                "namespace",
                namespace,
            ],
            text=True,
            capture_output=True,
        )

        if result.returncode != 0:
            break

        time.sleep(interval)

        ensure_namespace(namespace)
