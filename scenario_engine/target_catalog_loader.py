from scenario_engine.target_provider import ( 
    TargetCatalogEntry,
    TargetDefinition,
    TargetSource,
    TargetOrigin,
    EvaluationMode,
)

from scenario_engine.docker_hub import( 
    list_repository_tags,
    pull_image,
    resolve_image_digest,                                       
)

from scenario_engine.target_ground_truth_loader import (
    load_target_ground_truth_for_ref,
    target_ground_truth_exists,
)

from scenario_engine.github import build_github_target
from pathlib import Path

import yaml
from pydantic import BaseModel


class TargetCatalog(BaseModel):
    targets: list[TargetCatalogEntry]

def load_target_catalog(
    path: str = "targets/catalog.yaml"
) -> TargetCatalog:
    catalog_path = Path(path)

    if not catalog_path.exists():
        raise FileNotFoundError(
            f"target catalog not found: {path}"
        )

    with catalog_path.open("r", encoding="utf-8") as file:
        data = yaml.safe_load(file)

    return TargetCatalog.model_validate(data)

def list_available_targets() -> None:
    catalog = load_target_catalog()

    for index, target in enumerate(catalog.targets, start=1):
        print(f"[{index}] {target.display_name}")
        print(f"    origin: {target.origin.value}")
        print(f"    repository: {target.repository}")

        if target.origin == TargetOrigin.DOCKER_HUB:
            tags = list_repository_tags(
                target.repository,
                page_size=10,
            )

            print("    available tags:")
            for tag in tags:
                print(f"      - {tag}")

        elif target.origin == TargetOrigin.GITHUB:
            print(f"    ref: {target.ref}")
            print(f"    dockerfile: {target.dockerfile}")

        print()

def select_target() -> TargetDefinition:
    catalog = load_target_catalog()

    print("Available vulnerable targets:")
    for index, target in enumerate(catalog.targets, start=1):
        print(f"[{index}] {target.display_name}")

    target_choice = read_choice(
        "Select target: ",
        len(catalog.targets),
    )

    selected = catalog.targets[target_choice - 1]
    
    if selected.origin == TargetOrigin.DOCKER_HUB:
        tags = list_repository_tags(
            selected.repository,
            page_size=10,
        )

        print("\nAvailable tags:")
        for index, tag in enumerate(tags, start=1):
            print(f"[{index}] {tag}")

        tag_choice = read_choice(
            "Select tag: ",
            len(tags),
        )
        
        selected_tag = tags[tag_choice - 1]
        selected_image = f"{selected.repository}:{selected_tag}"

        pull_image(
            selected_image
        )

        image_digest = resolve_image_digest(
            selected_image
        )

        resolved_image = (
            f"{selected.repository}@{image_digest}"
        )

        print(
            f"Ground-truth key: {selected.ground_truth_key}"
        )

        ground_truth_complete = False
        ground_truth_finding_count = 0
        ground_truth_scope = None
        ground_truth_loaded = False

        if (
            selected.ground_truth_key is not None
            and target_ground_truth_exists(
                selected.ground_truth_key,
                selected_tag,
            )
        ):
            ground_truth = load_target_ground_truth_for_ref(
                selected.ground_truth_key,
                selected_tag,
            )
            
            ground_truth_loaded = True

            ground_truth_complete = ground_truth.complete
            ground_truth_finding_count = len(ground_truth.findings)
            ground_truth_scope = ground_truth.scope
            


            print(
                f"Ground truth loaded: "
                f"{ground_truth.target_name} "
                f"({ground_truth.ref})"
            )

            if ground_truth.repository != selected.repository:
                raise ValueError(
                    "ground truth repository does not match selected target"
                )

            if ground_truth.ref != selected_tag:
                raise ValueError(
                    "ground truth ref does not match selected target ref"
                )

            if (
                ground_truth.image_digest is not None
                and ground_truth.image_digest != image_digest
            ):
                raise ValueError(
                    "ground truth image_digest does not match selected image digest"
                )

            if ground_truth.target_name != selected.name:
                raise ValueError(
                    "ground truth target_name does not match selected target"
                )

            if (
                selected.evaluation_mode == EvaluationMode.KNOWN_GROUND_TRUTH
                and not ground_truth.complete
            ):
                raise ValueError(
                    "known-ground-truth target requires complete ground truth"
                )

        elif (
            selected.evaluation_mode
            == EvaluationMode.KNOWN_GROUND_TRUTH
        ):
            raise ValueError(
                "known-ground-truth target requires "
                "a matching ground-truth file"
            )

        else:
            print(
                "No matching ground-truth file; "
                "continuing in unknown-ground-truth mode"
            )



        return TargetDefinition(
            name=selected.name,
            source=TargetSource.CONTAINER,
            evaluation_mode=selected.evaluation_mode,
            image=resolved_image,
            image_digest=image_digest,
            origin=selected.origin,
            repository=selected.repository,
            ref=selected_tag,
            ground_truth_key=selected.ground_truth_key,
            ground_truth_complete=ground_truth_complete,
            ground_truth_loaded=ground_truth_loaded,
            ground_truth_finding_count=ground_truth_finding_count,
            ground_truth_scope=ground_truth_scope,
            port=selected.port,
            ground_truth_available=selected.ground_truth_available,
            manual_validation=selected.manual_validation,
            environment=selected.environment,
        )

    if selected.origin == TargetOrigin.GITHUB:
        image_name = f"cyber-range/{selected.name}:{selected.ref}"

        built_image, commit_sha = build_github_target(
            repository=selected.repository,
            ref=selected.ref,
            dockerfile=selected.dockerfile,
            image_name=image_name,
        )

        print(
            f"Ground-truth key: {selected.ground_truth_key}"
        )

        ground_truth_complete = False
        ground_truth_finding_count = 0
        ground_truth_scope = None
        ground_truth_loaded = False

        if (
            selected.ground_truth_key is not None
            and target_ground_truth_exists(
                selected.ground_truth_key,
                selected.ref,
            )
        ):
            ground_truth = load_target_ground_truth_for_ref(
                selected.ground_truth_key,
                selected.ref,
            )

            ground_truth_loaded = True

            ground_truth_complete = ground_truth.complete
            ground_truth_finding_count = len(ground_truth.findings)
            ground_truth_scope = ground_truth.scope

            if ground_truth.repository != selected.repository:
                raise ValueError(
                    "ground truth repository does not match selected target"
                )

            if ground_truth.ref != selected.ref:
                raise ValueError(
                    "ground truth ref does not match selected target ref"
                )

            if (
                ground_truth.commit_sha is not None
                and ground_truth.commit_sha != commit_sha
            ):
                raise ValueError(
                    "ground truth commit_sha does not match selected commit"
                )


            if ground_truth.target_name != selected.name:
                raise ValueError(
                    "ground truth target_name does not match selected target"
                )

            if (
                selected.evaluation_mode == EvaluationMode.KNOWN_GROUND_TRUTH
                and not ground_truth.complete
            ):
                raise ValueError(
                    "known-ground-truth target requires complete ground truth"
                )

            print(
                f"Ground truth loaded: "
                f"{ground_truth.target_name} "
                f"({ground_truth.ref})"
            )

        elif (
            selected.evaluation_mode
            == EvaluationMode.KNOWN_GROUND_TRUTH
        ):
            raise ValueError(
                "known-ground-truth target requires "
                "a matching ground-truth file"
            )

        else:
            print(
                "No matching ground-truth file; "
                "continuing in unknown-ground-truth mode"
            )


        return TargetDefinition(
            name=selected.name,
            source=TargetSource.CONTAINER,
            evaluation_mode=selected.evaluation_mode,
            image=built_image,
            origin=selected.origin,
            repository=selected.repository,
            ref=selected.ref,
            commit_sha=commit_sha,
            ground_truth_key=selected.ground_truth_key,
            ground_truth_complete=ground_truth_complete,
            ground_truth_loaded=ground_truth_loaded,
            ground_truth_finding_count=ground_truth_finding_count,
            ground_truth_scope=ground_truth_scope,
            port=selected.port,
            ground_truth_available=selected.ground_truth_available,
            manual_validation=selected.manual_validation,
            environment=selected.environment,
        )

    raise ValueError(
        f"unsupported target origin: {selected.origin}"
    )


def read_choice(prompt: str, max_choice: int) -> int:
    while True:
        try:
            choice = int(input(prompt))
        except ValueError:
            print(
                f"Please enter a number between 1 and {max_choice}."
            )
            continue

        if 1 <= choice <= max_choice:
            return choice

        print(
            f"Please enter a number between 1 and {max_choice}."
        )

