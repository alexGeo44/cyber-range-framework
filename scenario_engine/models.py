from pydantic import BaseModel, Field, model_validator

from scenario_engine.resources import (
    parse_cpu,
    parse_memory,
)


class ResourceValues(BaseModel):
    cpu: str
    memory: str

class NodeResources(BaseModel):
    requests: ResourceValues
    limits: ResourceValues

    @model_validator(mode="after")
    def validate_requests_limits(self):
        request_cpu = parse_cpu(self.requests.cpu)
        limit_cpu = parse_cpu(self.limits.cpu)

        request_memory = parse_memory(self.requests.memory)
        limit_memory = parse_memory(self.limits.memory)

        if request_cpu > limit_cpu:
            raise ValueError(
                "CPU request cannot be greater than CPU limit"
            )

        if request_memory > limit_memory:
            raise ValueError(
                "Memory request cannot be greater than memory limit"
            )

        return self


class NodeConfig(BaseModel):
    cloud: int = Field(ge=0)
    fog: int = Field(ge=0)
    edge: int = Field(ge=0)

    resources: dict[str, NodeResources]

class WorkloadConfig(BaseModel):
    count: int = Field(ge=0)

class VulnerabilityConfig(BaseModel):
    count: int = Field(ge=0)

class ScenarioConfig(BaseModel):
    name: str
    seed: int
    nodes: NodeConfig
    workloads: WorkloadConfig
    vulnerabilities: VulnerabilityConfig



