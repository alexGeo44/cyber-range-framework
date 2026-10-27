import pytest

from scenario_engine.target_catalog_loader import (
    load_target_catalog,
    select_target,
)

from scenario_engine.target_provider import EvaluationMode

def test_load_target_catalog():
    catalog = load_target_catalog()

    assert len(catalog.targets) == 3

    by_name = {
        target.name: target
        for target in catalog.targets
    }

    assert by_name["vulnerable-web"].evaluation_mode == EvaluationMode.UNKNOWN_GROUND_TRUTH
    assert by_name["webgoat"].evaluation_mode == EvaluationMode.UNKNOWN_GROUND_TRUTH
    assert by_name["dvwa"].evaluation_mode == EvaluationMode.UNKNOWN_GROUND_TRUTH
    
def test_catalog_ground_truth_flags():
    catalog = load_target_catalog()

    for target in catalog.targets:
        assert target.ground_truth_available is False
        assert target.manual_validation is True

def test_catalog_ground_truth_keys():
    catalog = load_target_catalog()

    by_name = {
        target.name: target
        for target in catalog.targets
    }

    assert by_name["vulnerable-web"].ground_truth_key == "juice-shop"
    assert by_name["webgoat"].ground_truth_key == "webgoat"
    assert by_name["dvwa"].ground_truth_key == "dvwa"

def test_dvwa_ref_is_pinned_commit():
    catalog = load_target_catalog()

    by_name = {
        target.name: target
        for target in catalog.targets
    }

    dvwa = by_name["dvwa"]

    assert dvwa.ref == "068d974487a297c155c48722f9fcf7180a83adc4"
    assert len(dvwa.ref) == 40

def test_select_target_docker_hub_loads_ground_truth(monkeypatch):
    choices = iter([1, 1])

    monkeypatch.setattr(
        "scenario_engine.target_catalog_loader.read_choice",
        lambda *args, **kwargs: next(choices),
    )

    
    monkeypatch.setattr(
        "scenario_engine.target_catalog_loader.list_repository_tags",
        lambda *args, **kwargs: ["v20.3.0"],
    )

    monkeypatch.setattr(
        "scenario_engine.target_catalog_loader.pull_image",
        lambda *args, **kwargs: None,

    )

    monkeypatch.setattr(
        "scenario_engine.target_catalog_loader.resolve_image_digest",
        lambda *args, **kwargs:
            "sha256:cea5a4af4aacee498c491491af0408934ec81d004035c0a02ef3e54395e3bf27"
    )

    target = select_target()

    assert target.name == "vulnerable-web"
    assert target.ref == "v20.3.0"
    assert target.ground_truth_loaded is True
    assert target.ground_truth_complete is False
    assert target.ground_truth_finding_count == 2

def test_select_target_github_loads_ground_truth(monkeypatch):
    monkeypatch.setattr(
        "scenario_engine.target_catalog_loader.read_choice",
        lambda *args, **kwargs: 3,
    )

    monkeypatch.setattr(
        "scenario_engine.target_catalog_loader.build_github_target",
        lambda *args, **kwargs: (
            "cyber-range/dvwa:068d974487a2",
            "068d974487a297c155c48722f9fcf7180a83adc4",
        ),
    )

    target = select_target()

    assert target.name == "dvwa"
    assert target.ref == "068d974487a297c155c48722f9fcf7180a83adc4"
    assert target.commit_sha == "068d974487a297c155c48722f9fcf7180a83adc4"
    assert target.ground_truth_loaded is True
    assert target.ground_truth_complete is False
    assert target.ground_truth_finding_count == 2

def test_select_target_github_rejects_ground_truth_commit_mismatch(
    monkeypatch
):
    monkeypatch.setattr(
        "scenario_engine.target_catalog_loader.read_choice",
        lambda *args, **kwargs: 3
    )

    monkeypatch.setattr(
        "scenario_engine.target_catalog_loader.build_github_target",
        lambda *args, **kwargs: (
            "cyber-range/dvwa:different",
            "a" * 40,
        ),
    )

    with pytest.raises(
        ValueError,
        match="ground truth commit_sha does not match selected commit",
    ):
        select_target()

def test_select_target_docker_hub_rejects_ground_truth_digest_mismatch(
    monkeypatch,
):
    choices = iter([1, 1])

    monkeypatch.setattr(
        "scenario_engine.target_catalog_loader.read_choice",
        lambda *args, **kwargs: next(choices),
    )

    monkeypatch.setattr(
        "scenario_engine.target_catalog_loader.list_repository_tags",
        lambda *args, **kwargs: ["v20.3.0"],
    )

    monkeypatch.setattr(
        "scenario_engine.target_catalog_loader.pull_image",
        lambda *args, **kwargs: None,
    )

    monkeypatch.setattr(
        "scenario_engine.target_catalog_loader.resolve_image_digest",
        lambda *args, **kwargs: "sha256:" + "a" * 64,
    )

    with pytest.raises(
        ValueError,
        match="ground truth image_digest does not match selected image digest",
    ):
        select_target()

def test_select_target_unknown_ground_truth_without_matching_file(
    monkeypatch,
):
    choices = iter([2, 1])

    monkeypatch.setattr(
        "scenario_engine.target_catalog_loader.read_choice",
        lambda *args, **kwargs: next(choices),
    )

    monkeypatch.setattr(
        "scenario_engine.target_catalog_loader.list_repository_tags",
        lambda *args, **kwargs: ["v1.0.0"],
    )

    monkeypatch.setattr(
        "scenario_engine.target_catalog_loader.pull_image",
        lambda *args, **kwargs: None,
    )

    monkeypatch.setattr(
        "scenario_engine.target_catalog_loader.resolve_image_digest",
        lambda *args, **kwargs: "sha256:" + "b" * 64,
    )

    target = select_target()

    assert target.name == "webgoat"
    assert target.ground_truth_key == "webgoat"
    assert target.ground_truth_loaded is False
    assert target.ground_truth_complete is False
    assert target.ground_truth_finding_count == 0
    assert target.ground_truth_scope is None
