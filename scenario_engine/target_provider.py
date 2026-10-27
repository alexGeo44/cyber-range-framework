from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, model_validator


class EvaluationMode(str, Enum):
    KNOWN_GROUND_TRUTH = "known_ground_truth"
    UNKNOWN_GROUND_TRUTH = "unknown_ground_truth"

class TargetOrigin(str, Enum):
    DOCKER_HUB = "docker_hub"
    GITHUB = "github"
    LOCAL = "local"
    GENERATED = "generated"


class TargetCatalogEntry(BaseModel):
    name: str
    display_name: str
    origin: TargetOrigin
    repository: str
    ref: Optional[str] = None
    dockerfile: Optional[str] = None
    ground_truth_key: Optional[str] = None

    port: int = Field(
        ge=1,
        le=65535
    )

    evaluation_mode: EvaluationMode
    ground_truth_available: bool = False
    manual_validation: bool = False
    environment: dict[str, str] = Field(
        default_factory=dict
    )

class TargetSource(str, Enum):
    GENERATED = "generated"
    CONTAINER = "container"


class TargetDefinition(BaseModel):
    name: str
    source: TargetSource
    evaluation_mode: EvaluationMode

    image: Optional[str] = None
    image_digest: Optional[str] = None
    origin: Optional[TargetOrigin] = None
    repository: Optional[str] = None
    ref: Optional[str] = None
    commit_sha: Optional[str] = None
    ground_truth_key: Optional[str] = None
    ground_truth_complete: bool = False
    ground_truth_loaded: bool = False

    ground_truth_finding_count: int = Field(
        default=0,
        ge=0,
    ) 

    ground_truth_scope: Optional[str] = None

    port: Optional[int] = Field(
        default=None,
        ge=1,
        le=65535,
    )

    ground_truth_available: bool = False
    manual_validation: bool = False
    environment: dict[str, str] = Field(
        default_factory=dict
    )

    @model_validator(mode="after")
    def validate_container_target(self):
        if self.source == TargetSource.CONTAINER and not self.image:
            raise ValueError(
                "container targets must define an image"
            )

        if self.source == TargetSource.CONTAINER and self.port is None:
            raise ValueError(
                "container targets must define a port"
            )

        if (
            self.evaluation_mode == EvaluationMode.KNOWN_GROUND_TRUTH
            and not self.ground_truth_available
        ):
            raise ValueError(
                "known-ground-truth targets must have ground_truth_available=True"
            )

        if (
            self.evaluation_mode == EvaluationMode.UNKNOWN_GROUND_TRUTH
            and self.ground_truth_available
        ):
            raise ValueError(
                "unknown-ground-truth targets cannot have ground_truth_available=True"
            )

        if (
            self.ground_truth_complete 
            and not self.ground_truth_loaded
        ):
            raise ValueError(
                "complete ground truth requires ground_truth_loaded=True"
            )

        if (
            self.ground_truth_finding_count > 0
            and not self.ground_truth_loaded
        ):
            raise ValueError(
                "ground truth findings require ground_truth_loaded=True"
            )

        if (
            self.ground_truth_complete
            and self.ground_truth_finding_count == 0
        ):
            raise ValueError(
                "complete ground truth requires at least one finding"
            )

        if (
            self.ground_truth_scope is not None
            and not self.ground_truth_loaded
        ):
            raise ValueError(
                "ground truth scope requires ground_truth_loaded=True"
            )

        if (
            self.ground_truth_loaded
            and self.ground_truth_key is None
        ):
            raise ValueError(
                "loaded ground truth requires ground_truth_key"
            )

        return self 
