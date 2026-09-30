from pathlib import Path
from typing import Dict, Any, List

import shutil
import yaml
import random

from scenario_engine.models import ScenarioConfig
from scenario_engine.catalog import WORKLOAD_CATALOG


def generate_deployment(
    name: str,
    node_type: str,
    workload_type: str,
    resources,
) -> Dict[str, Any]:

    template = WORKLOAD_CATALOG[workload_type]

    container = {
        "name": name,
        "image": template["image"],
        "ports": [
            {
                "containerPort": template["port"]
            }
        ],
        "resources": {
            "requests": {
                "cpu": resources.requests.cpu,
                "memory": resources.requests.memory,
            },
            "limits": {
                "cpu": resources.limits.cpu,
                "memory": resources.limits.memory,
            },
        },
    }

    if "env" in template:
        container["env"] = template["env"]

    deployment = {
        "apiVersion": "apps/v1",
        "kind": "Deployment",
        "metadata": {
            "name" : name
        },
        "spec": {
            "replicas": 1,
            "selector": {
                "matchLabels": {
                    "app": name
                }
            },
            "template": {
                "metadata": {
                    "labels": {
                        "app": name,
                        "workload-type": workload_type,
                    }
                },
                "spec": {
                    "automountServiceAccountToken": False,
                    "nodeSelector": {
                        "node-type": node_type
                    },
                    "tolerations": [
                        {
                            "key": "node-type",
                            "operator": "Equal",
                            "value": node_type,
                            "effect": "NoSchedule",
                        }
                    ],
                    "containers": [
                        container
                    ]
                }
            }
        }
    }

    return deployment

def generate_workloads(scenario):
    rng = random.Random(scenario.seed)

    workloads = []

    workload_types = list(WORKLOAD_CATALOG.keys())

    available_node_types = []

    if scenario.nodes.cloud > 0:
        available_node_types.append("cloud")

    if scenario.nodes.fog > 0:
        available_node_types.append("fog")

    if scenario.nodes.edge > 0:
        available_node_types.append("edge")


    for index in range(scenario.workloads.count):
        workload_type = rng.choice(workload_types)

        template = WORKLOAD_CATALOG[workload_type]

        allowed_nodes = [
            node_type
            for node_type in template["allowed_node_types"]
            if node_type in available_node_types
        ]

        if not allowed_nodes:
            raise ValueError(
                f"No valid node type for "
                f"workload type '{workload_type}'"
            )

        node_type = rng.choice(allowed_nodes)

        workload_name = f"workload-{index + 1}"

        resources = scenario.nodes.resources[node_type]

        workload = generate_deployment(
            name=workload_name,
            node_type=node_type,
            workload_type=workload_type,
            resources=resources,
        )

        workloads.append(workload)

    return workloads



def save_workloads(workloads, output_dir: str = "generated"):
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)


    for workload in workloads:
        name = workload["metadata"]["name"]
        file_path = output_path / f"{name}.yaml"


        with file_path.open("w") as file:
            yaml.safe_dump(
                workload,
                file,
                sort_keys=False
            )



def generate_service(
    name: str,
    workload_type: str,
) -> Dict[str, Any]:

    template = WORKLOAD_CATALOG[workload_type]

    service = {
        "apiVersion": "v1",
        "kind": "Service",
        "metadata": {
            "name": f"{name}-service"
        },
        "spec": {
            "selector": {
               "app": name
            },
            "ports": [
                {
                    "port" : template["port"],
                    "targetPort": template["port"]
                }
            ],
            "type": "ClusterIP"
        }
    }

    return service

def generate_services(workloads) -> List[Dict[str, Any]]:
    services = []

    for workload in workloads:
        name = workload["metadata"]["name"]

        workload_type = (
            workload["spec"]
            ["template"]
            ["metadata"]
            ["labels"]
            ["workload-type"]
        )

        template = WORKLOAD_CATALOG[workload_type]

        if not template.get("service", False):
            continue


        service = generate_service(
            name=name,
            workload_type=workload_type
        )

        services.append(service)

    return services

def save_services(
    services,
    output_dir: str = "generated"
):
    output_path = Path(output_dir)
    output_path.mkdir(
        parents=True,
        exist_ok=True
    )

    for service in services:
        name = service["metadata"]["name"]

        file_path = output_path / f"{name}.yaml"

        with file_path.open("w") as file:
            yaml.safe_dump(
                service,
                file,
                sort_keys=False
            )

def generate_relationships(workloads):
    relationships = []

    workloads_by_type = {}

    for workload in workloads:
        workload_type = (
            workload["spec"]
            ["template"]
            ["metadata"]
            ["labels"]
            ["workload-type"]
        )

        workload_name = workload["metadata"]["name"]

        workloads_by_type.setdefault(
            workload_type,
            []
        ).append(workload_name)

    web_workloads = workloads_by_type.get(
        "web",
        []
    )

    api_workloads = workloads_by_type.get(
        "api",
        []
    )

    database_workloads = workloads_by_type.get(
        "database",
        []
    )

    for web in web_workloads:
        if api_workloads:
            relationships.append({
                "source": web,
                "target": api_workloads[0],
                "type": "http",
            })

    for api in api_workloads:
        if database_workloads:
            relationships.append({
                "source": api,
                "target": database_workloads[0],
                "type": "database",
            })

    return relationships

def generate_network_policy(
    source_name: str,
    target_name: str,
) -> Dict[str, Any]:

    policy = {
        "apiVersion": "networking.k8s.io/v1",
        "kind": "NetworkPolicy",
        "metadata": {
            "name" : f"allow-{source_name}-to-{target_name}"
        },
        "spec": {
            "podSelector": {
                "matchLabels": {
                    "app": target_name
                }
            },
            "policyTypes": [
                "Ingress"
            ],
            "ingress": [
                {
                    "from": [
                        {
                            "podSelector": {
                                "matchLabels": {
                                    "app": source_name
                                }
                            }
                        }
                    ]
                }
            ]
        }
    }

    return policy

def generate_network_policies(
    relationships
) -> List[Dict[str, Any]]:

    policies = []

    for relationship in relationships:
        source = relationship["source"]
        target = relationship["target"]

        policy = generate_network_policy(
            source_name=source,
            target_name=target,
        )

        policies.append(policy)

    return policies

def save_network_policies(
    policies,
    output_dir: str = "generated"
):
    output_path = Path(output_dir)

    output_path.mkdir(
        parents=True,
        exist_ok=True
    )

    for policy in policies:
        name = policy["metadata"]["name"]

        file_path = output_path / f"{name}.yaml"

        with file_path.open("w") as file:
            yaml.safe_dump(
                policy,
                file,
                sort_keys=False
            )

def generate_default_deny_policy(
    workload_name: str,
) -> Dict[str, Any]:

    return {
        "apiVersion": "networking.k8s.io/v1",
        "kind": "NetworkPolicy",
        "metadata": {
            "name": f"default-deny-{workload_name}"
        },
        "spec": {
            "podSelector": {
                "matchLabels": {
                    "app": workload_name
                }
            },
            "policyTypes": [
                "Ingress"
            ],
            "ingress": []
        }
    }


def generate_default_deny_policies(
    workloads,
) -> List[Dict[str, Any]]:

    policies = []

    for workload in workloads:
        name = workload["metadata"]["name"]

        policies.append(
            generate_default_deny_policy(name)
        )

    return policies


def clean_manifest_directory(
    output_dir: str = "generated/manifests",
) -> None:
    path = Path(output_dir)

    if path.exists():
        shutil.rmtree(path)

    path.mkdir(
        parents=True,
        exist_ok=True,
    )

def save_vulnerability_resources(
    resources,
    output_dir: str = "generated",

):
    output_path = Path(output_dir)

    output_path.mkdir(
        parents=True,
        exist_ok=True,
    )

    for resource in resources:
        kind = resource["kind"].lower()
        name = resource["metadata"]["name"]

        file_path = (
            output_path
            / f"{kind}-{name}.yaml"
        )

        with file_path.open("w") as file:
            yaml.safe_dump(
                resource,
                file,
                sort_keys=False,
            )
