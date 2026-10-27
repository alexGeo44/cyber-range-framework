from pydantic import BaseModel, Field, model_validator
from typing import Literal

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
    
    @model_validator(mode="after")
    def validate_resource_profiles(self):
        for node_type in ("cloud", "fog", "edge"):
            node_count = getattr(self, node_type)

            if(
                node_count > 0
                and node_type not in self.resources
            ):
                raise ValueError(
                    f"missing resources for node_type '{node_type}'"
                )

        valid_node_types = {"cloud", "fog", "edge"}

        unknown_resource_types = (
            set(self.resources.keys()) - valid_node_types
        )

        if unknown_resource_types:
            raise ValueError(
                "unknown resource node_type(s): "
                + ", ".join(sorted(unknown_resource_types))
            )

        return self



class WorkloadConfig(BaseModel):
    count: int = Field(ge=0)

class VulnerabilityConfig(BaseModel):
    count: int = Field(ge=0)

class TargetConfig(BaseModel):
    name: str
    node_type: Literal["cloud", "fog", "edge"]

class ScenarioConfig(BaseModel):
    name: str
    seed: int
    nodes: NodeConfig
    workloads: WorkloadConfig
    vulnerabilities: VulnerabilityConfig
    target: TargetConfig

    @model_validator(mode="after")
    def validate_target_node_exists(self):
        target_node_count = getattr(
            self.nodes,
            self.target.node_type,
        )

        if target_node_count <= 0:
            raise ValueError(
                f"target node_type '{self.target.node_type}' "
                f"must have at least one node"
            )

        return self




