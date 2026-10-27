from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, HttpUrl, model_validator

class GroundTruthSource(str, Enum):
    OFFICIAL_DOCUMENTATION = "official_documentation"
    REPOSITORY = "repository"
    MANUAL_VERIFICATION = "manual_verification"


class FindingSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class FindingCategory(str, Enum):
    INJECTION = "injection"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    XSS = "xss"
    CSRF = "csrf"
    FILE_INCLUSION = "file_inclusion"
    COMMAND_EXECUTION = "command_execution"
    INFORMATION_DISCLOSURE = "information_disclosure"
    OTHER = "other"


class TargetGroundTruthFinding(BaseModel):

    finding_id: str = Field(
        min_length=1,
        pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$",
    )
    title: str = Field(min_length=1, pattern=r".*\S.*")
    category: FindingCategory
    severity: FindingSeverity

    affected_component: Optional[str] = Field(
        default=None,
        min_length=1,
        pattern=r".*\S.*",
    )
    endpoint: Optional[str] = Field(
        default=None,
        min_length=1,
        pattern=r"^/.*\S.*$",
    )
    expected_evidence: Optional[str] = Field(
        default=None,
        min_length=1,
        pattern=r".*\S.*",
    )

    source: GroundTruthSource
    reference: Optional[HttpUrl] = None

    @model_validator(mode="after")
    def validate_reference(self):
        if (
            self.source
            in {
                GroundTruthSource.REPOSITORY,
                GroundTruthSource.OFFICIAL_DOCUMENTATION,
            }
            and self.reference is None
        ):
            raise ValueError(
                "repository and official documentation findings must define a reference"
            )

        return self 


class TargetGroundTruth(BaseModel):
    target_name: str = Field(min_length=1, pattern=r".*\S.*")
    repository: str = Field(min_length=1, pattern=r".*\S.*")
    ref: str = Field(min_length=1, pattern=r".*\S.*")
    scope: str = Field(min_length=1, pattern=r".*\S.*")

    image_digest: Optional[str] = Field(
        default=None,
        pattern=r"^sha256:[0-9a-fA-F]{64}$"
    )

    commit_sha: Optional[str] = Field(
        default=None,
        pattern=r"^[0-9a-fA-F]{40}$",
    )

    complete: bool = False

    findings: list[TargetGroundTruthFinding] = Field(
        default_factory=list
    )
    
    @model_validator(mode="after")
    def validate_ground_truth(self):
        finding_ids = [
            finding.finding_id
            for finding in self.findings
        ]

        if len(finding_ids) != len(set(finding_ids)):
            raise ValueError(
                "target ground truth contains duplicate finding_id values"
            )

        if self.complete and not self.findings:
            raise ValueError(
                "complete target ground truth must contain at least one finding"
            )

        if self.complete and not (self.image_digest or self.commit_sha):
            raise ValueError(
                "complete target ground truth must define an immutable target identity"
            )

        if self.image_digest and self.commit_sha:
            raise ValueError(
                "target ground truth must define either image_digest or commit_sha, not both"
            )

        return self
