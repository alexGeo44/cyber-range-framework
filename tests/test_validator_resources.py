from scenario_engine.validator import (
    calculate_pod_requests,
    can_place_workloads_on_nodes,
)

def test_regular_container_requests():
    pod_spec = {
        "containers": [
            {
                "resources": {
                    "requests": {
                        "cpu": "500m",
                        "memory": "512Mi"
                    }
                }
            }
        ]
    }

    result = calculate_pod_requests(pod_spec)

    assert result["cpu"] == 0.5
    assert result["memory"] == 536870912.0

def test_class_init_container_requests():
    pod_spec = {
        "containers": [
            {
                "resources": {
                    "requests": {
                        "cpu": "500m",
                        "memory": "256Mi",
                    }
                }
            }
        ],
        "initContainers": [
            {
                "name": "init-heavy",
                "resources": {
                    "requests": {
                        "cpu": "900m",
                        "memory": "128Mi",
                    }
                },
            }
        ],
    }

    result = calculate_pod_requests(pod_spec)

    assert result["cpu"] == 0.9
    assert result["memory"] == 268435456.0


def test_restartable_init_container_requests():
    pod_spec = {
        "containers": [
            {
                "resources": {
                    "requests": {
                        "cpu": "500m",
                        "memory": "256Mi",
                    }
                }
            }
        ],
        "initContainers": [
            {
                "name": "sidecar-init",
                "restartPolicy": "Always",
                "resources": {
                    "requests": {
                        "cpu": "200m",
                        "memory": "64Mi",
                    }
                },
            },
            {
                "name": "normal-init",
                "resources": {
                    "requests": {
                        "cpu": "900m",
                        "memory": "128Mi"
                    }
                },
            },
        ],
    }

    result = calculate_pod_requests(pod_spec)

    assert result["cpu"] == 1.1
    assert result["memory"] == 335544320.0

def test_pod_overhead_requests():
    pod_spec = {
        "containers": [
            {
                "resources" : {
                    "requests": {
                        "cpu": "500m",
                        "memory": "512Mi",
                    }
                }
            }
        ],
        "overhead": {
            "cpu": "200m",
            "memory": "64Mi",
        },
    }

    result = calculate_pod_requests(pod_spec)

    assert result["cpu"] == 0.7
    assert result["memory"] == 603979776.0

def test_multiple_regular_containers_requests():
    pod_spec = {
        "containers": [
            {
                "resources": {
                    "requests": {
                        "cpu": "300m",
                        "memory": "128Mi",
                    }
                }
            },
            {
                "resources": {
                    "requests": {
                        "cpu": "200m",
                        "memory": "64Mi",
                    }
                }
            },
        ]
    }

    result = calculate_pod_requests(pod_spec)

    assert result["cpu"] == 0.5
    assert result["memory"] == 201326592.0


def test_can_place_workloads_on_nodes_feasible():
    workloads = [
        {
            "name": "workload-1",
            "cpu": 1.0,
            "memory": 512 * 1024 * 1024,
        },
        {
            "name": "workload-2",
            "cpu": 0.5,
            "memory": 256 * 1024 * 1024,
        },
    ]

    nodes = {
            "node-a": {
            "cpu": 1.0,
            "memory": 512 * 1024 * 1024,
        },
        "node-b": {
            "cpu": 1.0,
            "memory": 512 * 1024 * 1024,
        },
    }

    assert can_place_workloads_on_nodes(
        workloads,
        nodes,
    ) is True


def test_can_place_workloads_on_nodes_rejects_oversized_workload():
    workloads = [
        {
            "name": "workload-too-large",
            "cpu": 2.0,
            "memory": 1024 * 1024 * 1024,
        },
    ]

    nodes = {
            "node-a": {
                "cpu": 1.0,
                "memory": 512 * 1024 * 1024,
            },
            "node-b": {
                "cpu": 1.5,
                "memory": 768 * 1024 * 1024,
            }
    }

    assert can_place_workloads_on_nodes(
        workloads,
        nodes,
    ) is False

def test_can_place_workloads_on_nodes_detects_fragmentation():
    workloads = [
        {
            "name": "workload-1",
            "cpu": 1.5,
            "memory": 512 * 1024 * 1024,
        },
        {
            "name": "workload-2",
            "cpu": 1.5,
            "memory": 512 * 1024 * 1024,
        },
    ]

    nodes = {
        "node-a": {
            "cpu": 2.0,
            "memory": 768 * 1024 * 1024,
        },
        "node-b": {
            "cpu": 1.0,
            "memory": 256 * 1024 * 1024,
        },
    }

    assert can_place_workloads_on_nodes(
        workloads,
        nodes,
    ) is False


def test_can_place_workloads_on_nodes_uses_backtracking():
    workloads = [
        {
            "name": "workload-1",
            "cpu": 3.0,
            "memory": 1.0,
        },
        {
            "name": "workload-2",
            "cpu": 2.0,
            "memory": 2.0,
        },
        {
            "name": "workload-3",
            "cpu": 2.0,
            "memory": 2.0,
        },
    ]


    nodes = {
        "node-a": {
            "cpu": 4.0,
            "memory": 4.0,
        },
        "node-b": {
            "cpu": 3.0,
            "memory": 1.0,
        },
    }

    assert can_place_workloads_on_nodes(
        workloads,
        nodes,
    ) is True
