import subprocess
import time
import json

from scenario_engine.resources import (
    parse_cpu,
    parse_memory,
)


def get_pods(namespace: str = "default"):
    result = subprocess.run(
        [
            "kubectl",
            "get",
            "pods",
            "-n",
            namespace,
            "-o",
            "json",
        ],
        check=True,
        text=True,
        capture_output=True,
    )

    return json.loads(result.stdout)


def get_all_pods():
    result = subprocess.run(
        [
            "kubectl",
            "get",
            "pods",
            "-A",
            "-o",
            "json"
        ],
        check=True,
        text=True,
        capture_output=True,
    )

    return json.loads(result.stdout)



def get_nodes():
    result = subprocess.run(
        [
            "kubectl",
            "get",
            "nodes",
            "-o",
            "json",
        ],
        check=True,
        text=True,
        capture_output=True,
    )

    return json.loads(result.stdout)

def wait_for_workloads(
    workloads,
    namespace: str = "default",
    timeout: int = 60,
    interval: int = 2,
):
    start_time = time.time()

    while time.time() - start_time < timeout:
        pods_data = get_pods(namespace)

        all_ready = True

        for workload in workloads:
            workload_name = workload["metadata"]["name"]

            matching_pods = []

            for pod in pods_data["items"]:
                labels = pod["metadata"].get("labels", {})

                if (
                    labels.get("app") == workload_name
                    and "workload-type" in labels
                ):
                    matching_pods.append(pod)

            if not matching_pods:
                all_ready = False
                break

            pod = matching_pods[0]

            if pod["status"]["phase"] != "Running":
                all_ready = False
                break

            conditions = pod["status"].get(
                "conditions",
                [],
            )

            ready = False

            for condition in conditions:
                if (
                    condition.get("type") == "Ready"
                    and condition.get("status") == "True"
                ):
                    ready = True
                    break

            if not ready:
                all_ready = False
                break

        if all_ready:
            return True

        time.sleep(interval)

    return False


def validate_workloads(
    workloads,
    namespace: str = "default",

):
    pods_data = get_pods(namespace)
    nodes_data = get_nodes()

    success = True

    node_types = {}

    for node in nodes_data["items"]:
        node_name = node["metadata"]["name"]
        labels = node["metadata"].get("labels", {})
        node_type = labels.get("node-type")

        node_types[node_name] = node_type

    for workload in workloads:
        workload_name = workload["metadata"]["name"]

        expected_node_type = (
            workload["spec"]
            ["template"]
            ["spec"]
            ["nodeSelector"]
            ["node-type"]
        )

        matching_pods = []

        for pod in pods_data["items"]:
            labels = pod["metadata"].get("labels", {})

            if (
                labels.get("app") == workload_name
                and "workload-type" in labels
            ):
                matching_pods.append(pod)

        if not matching_pods:
            print(f"[FAIL] {workload_name}: no pod found")
            success = False
            continue

        pod = matching_pods[0]

        pod_name = pod["metadata"]["name"]
        status = pod["status"]["phase"]
        node_name = pod["spec"].get("nodeName")

        if status != "Running":
            print(
                f"[FAIL] {workload_name}: "
                f"pod={pod_name}, "
                f"status={status}, "
                f"node={node_name}, "
                f"expected-type={expected_node_type}"
            )
            success = False
            continue

        actual_node_type = node_types.get(node_name)

        if actual_node_type != expected_node_type:
            print(
                f"[FAIL] {workload_name}: "
                f"pod={pod_name}, "
                f"status={status}, "
                f"node={node_name}, "
                f"expected-type={expected_node_type}, "
                f"actual-type={actual_node_type}"
            )
            success = False
            continue


        print(
            f"[OK] {workload_name}: "
            f"pod={pod_name}, "
            f"node={node_name}, "
            f"expected-type={expected_node_type}, "
            f"actual-type={actual_node_type}"
        )

    return success

def create_probe_pod(
    name: str,
    app_label: str,
    node_type: str,
    namespace: str = "default"
):
    pod_manifest = {
        "apiVersion": "v1",
        "kind": "Pod",
        "metadata": {
            "name": name,
            "namespace": namespace,
            "labels": {
                "app": app_label,
            },
        },
        "spec": {
            "nodeSelector": {
                "node-type": node_type,
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
                {
                    "name": name,
                    "image": "busybox:1.36",
                    "args": [
                        "sleep",
                        "3600"
                    ],
                }
            ],
            "restartPolicy": "Never"
        },
     }

    subprocess.run(
        [
            "kubectl",
             "apply",
             "-f",
             "-",
        ],
        input=json.dumps(pod_manifest),
        check=True,
        text=True,
        capture_output=True,
    )


def wait_for_probe(
    name: str,
    namespace: str = "default",
    timeout: int = 30,
    interval: int = 1,
) -> bool:
    start_time = time.time()


    while time.time() - start_time < timeout:
        result = subprocess.run(
            [
                "kubectl",
                "get",
                "pod",
                name,
                "-n",
                namespace,
                "-o",
                "json",
            ],
            text=True,
            capture_output=True,
        )

        if result.returncode != 0:
            time.sleep(interval)
            continue

        pod = json.loads(result.stdout)

        if pod["status"]["phase"] == "Running":
            return True

        time.sleep(interval)

    return False


def delete_probe_pod(
    name: str,
    namespace : str = "default",
):
    subprocess.run(
        [
            "kubectl",
            "delete",
            "pod",
            name,
            "-n",
            namespace,
            "--ignore-not-found",
        ],
        text=True,
        capture_output=True,
    )


def test_tcp_connectivity(
    probe_name: str,
    target_service: str,
    target_port: int,
    namespace: str = "default",
    timeout: int = 5,
) -> bool:

    result = subprocess.run(
        [
            "kubectl",
            "exec",
            "-n",
            namespace,
            probe_name,
            "--",
            "nc",
            "-zvw",
            str(timeout),
            target_service,
            str(target_port),
        ],
        text=True,
        capture_output=True
    )

    return result.returncode == 0


def validate_network_topology(
    workloads,
    services,
    relationships,
    namespace: str = "default",
):
    success = True

    service_by_workload = {}

    for service in services:
        workload_name = service["spec"]["selector"]["app"]
        service_name = service["metadata"]["name"]
        port = service["spec"]["ports"][0]["port"]

        service_by_workload[workload_name] = {
            "name": service_name,
            "port": port,
        }

    allowed_pairs = {
        (
            relationship["source"],
            relationship["target"],
        )
        for relationship in relationships
    }

    workload_names = [
            workload["metadata"]["name"]
            for workload in workloads
    ]

    for source in workload_names:
        probe_name = f"probe-{source}"

        delete_probe_pod(
            probe_name,
            namespace=namespace,
        )

        source_workload = next(
            workload
            for workload in workloads
            if workload["metadata"]["name"] == source
        )

        source_node_type = (
            source_workload["spec"]
            ["template"]
            ["spec"]
            ["nodeSelector"]
            ["node-type"]
        )

        create_probe_pod(
            name=probe_name,
            app_label=source,
            node_type=source_node_type,
            namespace=namespace,
        )

        if not wait_for_probe(
            probe_name,
            namespace=namespace,
        ):
            print(
                    f"[FAIL] could not start probe for {source}"
            )
            success = False
            continue

        for target in workload_names:
            if source == target:
                continue

            target_service = service_by_workload.get(target)

            if not target_service:
                continue

            actual_allowed =test_tcp_connectivity(
                probe_name=probe_name,
                target_service=target_service["name"],
                target_port=target_service["port"],
                namespace=namespace,
            )

            expected_allowed = (
                source,
                target,
            ) in allowed_pairs

            if actual_allowed == expected_allowed:
                state = (
                    "allowed"
                    if actual_allowed
                    else "blocked"
                )

                print(
                    f"[OK] {source} -> {target}: "
                    f"{state}"
                )

            else:
                print(
                    f"[FAIL] {source} -> {target}: "
                    f"expected="
                    f"{'allowed' if expected_allowed else 'blocked'}, "
                    f"actual="
                    f"{'allowed' if actual_allowed else 'blocked' }"
                )

                success = False

        delete_probe_pod(
            probe_name,
            namespace=namespace,

        )

    return success

def validate_vulnerabilities(
    selected_vulnerabilities,
    namespace: str = "default",
):
    success = True
    validated = []

    pods_data = get_pods(namespace)

    for vulnerability in selected_vulnerabilities:
        target = vulnerability["target"]
        vulnerability_id = vulnerability["vulnerability_id"]

        matching_pods = []

        for pod in pods_data["items"]:
            labels = pod["metadata"].get("labels", {})

            if(
                labels.get("app") == target
                and "workload-type" in labels
            ):
                matching_pods.append(pod)


        if not matching_pods:
            print(
                f"[FAIL] {target} -> {vulnerability_id}: "
                "no workload pod found"
            )
            success = False
            continue

        pod = matching_pods[0]

        containers = pod["spec"].get("containers", [])

        if not containers:
            print(
                f"[FAIL] {target} -> {vulnerability_id}: "
                f"no container found"
            )
            success = False
            continue

        container = containers[0]

        security_context = container.get(
            "securityContext",
            {}
        )

        is_valid = False

        if vulnerability_id == "run_as_root":
            is_valid = (
                security_context.get("runAsUser") == 0
                and security_context.get("runAsNonRoot") is False
            )

        elif vulnerability_id == "allow_privilege_escalation":
            is_valid = (
                security_context.get(
                    "allowPrivilegeEscalation"
                ) is True
            )

        elif vulnerability_id == "privileged_container":
            is_valid = (
                security_context.get("privileged") is True
            )

        elif vulnerability_id == "unconfined_seccomp_profile":
            seccomp_profile = security_context.get(
                "seccompProfile",
                {},
            )

            is_valid = (
                seccomp_profile.get("type") == "Unconfined"
            )

        elif vulnerability_id in (
            "add_sys_admin",
            "add_net_admin",
            "add_sys_ptrace",
        ):
            capability_map = {
                "add_sys_admin": "SYS_ADMIN",
                "add_net_admin": "NET_ADMIN",
                "add_sys_ptrace": "SYS_PTRACE",
            }

            added_capabilities = (
                security_context
                .get("capabilities", {})
                .get("add", [])
            )

            expected_capability = capability_map[
                vulnerability_id
            ]

            is_valid = (
                expected_capability in added_capabilities
            )

        elif vulnerability_id == "host_network":
            is_valid = (
                pod["spec"].get("hostNetwork") is True
            )

        elif vulnerability_id == "host_pid":
            is_valid = (
                pod["spec"].get("hostPID") is True
            )

        elif vulnerability_id == "host_ipc":
            is_valid = (
                pod["spec"].get("hostIPC") is True
            )

        elif vulnerability_id == "host_path_mount":
            volumes = pod["spec"].get(
                "volumes",
                []
            )

            volume_mounts = container.get(
                "volumeMounts",
                []
            )

            host_volume_found = any(
                volume.get("name") == "host-etc"
                and volume.get("hostPath", {}).get("path") == "/etc"
                and volume.get("hostPath", {}).get("type") == "Directory"
                for volume in volumes
            )

            host_mount_found = any(
                mount.get("name") == "host-etc"
                and mount.get("mountPath") == "/host-etc"
                and mount.get("readOnly") is True
                for mount in volume_mounts
            )

            is_valid = (
                host_volume_found
                and host_mount_found
            )

        elif vulnerability_id == "writable_host_path":
            volumes = pod["spec"].get(
                "volumes",
                []
            )

            volume_mounts = container.get(
                "volumeMounts",
                []
            )

            host_volume_found = any(
                volume.get("name") == "host-tmp"
                and volume.get("hostPath", {}).get("path") == "/tmp"
                and volume.get("hostPath", {}).get("type") == "Directory"
                for volume in volumes
            )

            writable_mount_found = any(
                mount.get("name") == "host-tmp"
                and mount.get("mountPath") == "/host-tmp"
                and mount.get("readOnly", False) is False
                for mount in volume_mounts
            )

            is_valid = (
                host_volume_found
                and writable_mount_found
            )

        elif vulnerability_id == "automount_service_account_token":
            is_valid = (
                pod["spec"].get("automountServiceAccountToken") is True
            )

        elif vulnerability_id == "overprivileged_service_account":
            is_valid = validate_overprivileged_service_account(
                pod,
                target,
                namespace,
            )

        if is_valid:
            print(
                f"[OK] {target} -> "
                f"{vulnerability_id}: validated"
            )

            validated.append(vulnerability)

        else:
            print(
                f"[FAIL] {target} -> "
                f"{vulnerability_id}: not present"
            )

            success = False

    return success, validated

def validate_cluster_nodes(scenario):
    nodes_data = get_nodes()

    actual_counts = {
        "cloud": 0,
        "fog": 0,
        "edge": 0,
    }

    for node in nodes_data["items"]:
        labels = node["metadata"].get("labels", {})
        node_type = labels.get("node-type")

        if node_type in actual_counts:
            actual_counts[node_type] += 1

    expected_counts = {
        "cloud": scenario.nodes.cloud,
        "fog": scenario.nodes.fog,
        "edge": scenario.nodes.edge,
    }

    success = True

    for node_type, expected in expected_counts.items():
        actual = actual_counts[node_type]


        if actual < expected:
            print(
                f"[FAIL] node-type={node_type}: "
                f"expected>={expected}, actual={actual}"
            )
            success = False
        else:
            print(
                f"[OK] node-type={node_type}: "
                f"expected>={expected}, actual={actual}"
            )

    return success


def validate_node_resources(scenario):
    nodes_data = get_nodes()

    success = True

    required_resources = (
        scenario.nodes.resources
    )

    for node in nodes_data["items"]:
        node_name = node["metadata"]["name"]

        labels = (
            node["metadata"]
            .get("labels", {})
        )

        node_type = labels.get("node-type")

        if node_type not in required_resources:
            continue

        allocatable = (
            node["status"]
            .get("allocatable", {})
        )

        actual_cpu = parse_cpu(
            allocatable["cpu"]
        )

        actual_memory = parse_memory(
            allocatable["memory"]
        )

        expected = (
                required_resources[node_type]
        )

        expected_cpu = parse_cpu(
            expected.requests.cpu
        )

        expected_memory = parse_memory(
            expected.requests.memory
        )

        cpu_valid = (
            actual_cpu >= expected_cpu
        )

        memory_valid = (
            actual_memory >= expected_memory
        )

        if cpu_valid and memory_valid:
            print(
                f"[OK] {node_name} "
                f"({node_type}): "
                f"cpu={allocatable['cpu']} "
                f"(required>={expected.requests.cpu}), "
                f"memory={allocatable['memory']} "
                f"(required>={expected.requests.memory})"
            )
        else:
            print(
                f"[FAIL] {node_name} "
                f"({node_type}): "
                f"cpu={allocatable['cpu']} "
                f"(required>={expected.requests.cpu}), "
                f"memory={allocatable['memory']} "
                f"(required>={expected.requests.memory})"
            )

            success = False

    return success

def validate_workload_resources(
    workloads,
    scenario,
    namespace: str = "default",
):
    pods_data = get_pods(namespace)

    success = True

    for workload in workloads:
        workload_name = workload["metadata"]["name"]

        expected_node_type = (
            workload["spec"]
            ["template"]
            ["spec"]
            ["nodeSelector"]
            ["node-type"]
        )

        expected_resources = (
            scenario.nodes.resources[
                expected_node_type
            ]
        )

        matching_pods = []

        for pod in pods_data["items"]:
            labels = pod["metadata"].get(
                "labels",
                {},
            )

            if labels.get("app") == workload_name:
                matching_pods.append(pod)

        if not matching_pods:
            print(
                f"[FAIL] {workload_name}: "
                f"no pod found"
            )
            success = False
            continue

        pod = matching_pods[0]

        containers = pod["spec"].get(
            "containers",
            [],
        )

        if not containers:
            print(
                f"[FAIL] {workload_name}: "
                f"no container found"
            )
            success = False
            continue

        container = containers[0]

        actual_resources = container.get(
            "resources",
            {},
        )

        actual_requests = actual_resources.get(
            "requests",
            {},
        )

        actual_limits = actual_resources.get(
            "limits",
            {},
        )

        expected_requests = {
            "cpu": expected_resources.requests.cpu,
            "memory": expected_resources.requests.memory,
        }

        expected_limits = {
            "cpu": expected_resources.limits.cpu,
            "memory": expected_resources.limits.memory,
        }

        requests_valid = (
            actual_requests == expected_requests
        )

        limits_valid = (
            actual_limits == expected_limits
        )


        if requests_valid and limits_valid:
            print(
                f"[OK] {workload_name}: "
                f"resources validated "
                f"(node-type={expected_node_type})"
            )
        else:
            print(
                f"[FAIL] {workload_name}: "
                f"resource mismatch"
            )

            print(
                f"expected request="
                f"{expected_requests}"
                )

            print(
                f"actual requests="
                f"{actual_requests}"
            )

            print(
                f"expected limits="
                f"{expected_limits}"
            )

            print(
                f"actual limits="
                f"{actual_limits}"
            )

            success = False

    return success

def calculate_pod_requests(pod_spec):
    regular_cpu = 0.0
    regular_memory = 0.0

    for container in pod_spec.get("containers", []):
        requests = (
            container
            .get("resources", {})
            .get("requests", {})
        )

        cpu = requests.get("cpu")
        memory = requests.get("memory")

        if cpu is not None:
            regular_cpu += parse_cpu(cpu)

        if memory is not None:
            regular_memory += parse_memory(memory)

    restartable_init_cpu = 0.0
    restartable_init_memory =0.0

    max_init_cpu = 0.0
    max_init_memory = 0.0

    for container in pod_spec.get("initContainers", []):
        requests = (
            container
            .get("resources", {})
            .get("requests", {})
        )

        cpu = requests.get("cpu")
        memory = requests.get("memory")

        cpu_value = (
            parse_cpu(cpu)
            if cpu is not None
            else 0.0
        )

        memory_value = (
            parse_memory(memory)
            if memory is not None
            else 0.0
        )

        if container.get("restartPolicy") == "Always":
            restartable_init_cpu += cpu_value
            restartable_init_memory += memory_value
        else:
            max_init_cpu = max(
                max_init_cpu,
                restartable_init_cpu + cpu_value
            )

            max_init_memory = max(
                max_init_memory,
                restartable_init_memory + memory_value,
            )

    overhead = pod_spec.get("overhead", {})

    overhead_cpu = 0.0
    overhead_memory = 0.0

    if overhead.get("cpu") is not None:
        overhead_cpu = parse_cpu(
            overhead["cpu"]
        )

    if overhead.get("memory") is not None:
        overhead_memory = parse_memory(
            overhead["memory"]
        )

    return {
        "cpu": (
            max(
                regular_cpu + restartable_init_cpu,
                max_init_cpu,
            )
            + overhead_cpu
        ),
        "memory": (
            max(
                regular_memory + restartable_init_memory,
                max_init_memory,
            )
            + overhead_memory
        ),
    }

def can_place_workloads_on_nodes(
    workloads,
    nodes,
):

    workloads = sorted(
        workloads,
        key=lambda workload: (
            workload["cpu"],
            workload["memory"],
        ),
        reverse=True,
    )

    remaining = {
        node_name: {
            "cpu": resources["cpu"],
            "memory": resources["memory"],
        }
        for node_name, resources in nodes.items()
    }

    def place_workload(index):
        if index == len(workloads):
            return True

        workload = workloads[index]

        for node_resources in remaining.values():
            if (
                workload["cpu"] <= node_resources["cpu"]
                and workload["memory"] <= node_resources["memory"]
            ):
                node_resources["cpu"] -= workload["cpu"]
                node_resources["memory"] -= workload["memory"]

                if place_workload(index + 1):
                    return True

                node_resources["cpu"] += workload["cpu"]
                node_resources["memory"] += workload["memory"]

        return False

    return place_workload(0)



def validate_aggregate_resources(
    workloads,
    namespace: str,
):
    nodes_data = get_nodes()
    pods_data = get_all_pods()

    success = True

    node_type_by_name = {}
    capacity_by_node = {}

    for node in nodes_data["items"]:
        node_name = node["metadata"]["name"]
        labels = node["metadata"].get("labels", {})
        node_type = labels.get("node-type")

        if node_type in ("cloud", "fog", "edge"):
            node_type_by_name[node_name] = node_type

            allocatable = node["status"].get(
                "allocatable",
                {},
            )

            capacity_by_node[node_name] = {
                "node_type": node_type,
                "cpu": parse_cpu(allocatable["cpu"]),
                "memory": parse_memory(allocatable["memory"]),
            }

    capacity_by_type = {
        "cloud": {
            "cpu": 0.0,
            "memory": 0.0,
        },
        "fog": {
            "cpu": 0.0,
            "memory": 0.0,
        },
        "edge": {
            "cpu": 0.0,
            "memory": 0.0,
        },
    }

    used_by_type = {
        "cloud": {
            "cpu": 0.0,
            "memory": 0.0,
        },
        "fog": {
            "cpu": 0.0,
            "memory": 0.0,
        },
        "edge": {
            "cpu": 0.0,
            "memory": 0.0,
        },
    }


    used_by_node = {
        node_name: {
            "cpu": 0.0,
            "memory": 0.0,
        }
        for node_name in capacity_by_node
    }

    for node in nodes_data["items"]:
        labels = node["metadata"].get(
            "labels",
            {},
        )

        node_type = labels.get("node-type")

        if node_type not in capacity_by_type:
            continue


        allocatable = node["status"].get(
            "allocatable",
            {},
        )

        capacity_by_type[node_type]["cpu"] += (
            parse_cpu(allocatable["cpu"])
        )

        capacity_by_type[node_type]["memory"] += (
            parse_memory(allocatable["memory"])
        )

    for pod in pods_data["items"]:
        pod_phase = pod.get("status", {}).get("phase")

        if pod_phase in ("Succeeded", "Failed"):
            continue

        pod_namespace = pod["metadata"].get("namespace")

        if pod_namespace == namespace:
            continue

        node_name = pod["spec"].get("nodeName")

        if not node_name:
            continue

        node_type = node_type_by_name.get(node_name)

        if node_type is None:
            continue

        pod_requests = calculate_pod_requests(
            pod["spec"]
        )

        used_by_type[node_type]["cpu"] += (
            pod_requests["cpu"]
        )

        used_by_type[node_type]["memory"] += (
            pod_requests["memory"]
        )

        if node_name in used_by_node:
            used_by_node[node_name]["cpu"] += (
                pod_requests["cpu"]
            )

            used_by_node[node_name]["memory"] += (
                pod_requests["memory"]
            )

    available_by_node = {}

    for node_name, capacity in capacity_by_node.items():
        used = used_by_node[node_name]

        available_by_node[node_name] = {
            "node_type": capacity["node_type"],
            "cpu": capacity["cpu"] - used["cpu"],
            "memory": capacity["memory"] - used["memory"],
        }



    requested_by_type = {
        "cloud": {
            "cpu": 0.0,
            "memory": 0.0,
        },
        "fog": {
            "cpu": 0.0,
            "memory": 0.0,
        },
        "edge": {
            "cpu": 0.0,
            "memory":0.0
        },
    }

    workload_requests_by_type = {
        "cloud": [],
        "fog": [],
        "edge": [],
    }

    for workload in workloads:
        pod_spec = (
            workload["spec"]
            ["template"]
            ["spec"]
        )

        node_type = (
                pod_spec["nodeSelector"]["node-type"]
        )

        pod_requests = calculate_pod_requests(
            pod_spec
        )

        workload_requests_by_type[node_type].append(
            {
                "name": workload["metadata"]["name"],
                "cpu": pod_requests["cpu"],
                "memory": pod_requests["memory"],
            }
        )

        requested_by_type[node_type]["cpu"] += (
            pod_requests["cpu"]
        )

        requested_by_type[node_type]["memory"] += (
            pod_requests["memory"]
        )

    for node_type in requested_by_type:
        requested_cpu = (
            requested_by_type[node_type]["cpu"]
        )

        requested_memory = (
            requested_by_type[node_type]["memory"]
        )

        available_cpu = (
            capacity_by_type[node_type]["cpu"]
            - used_by_type[node_type]["cpu"]
         )

        available_memory = (
            capacity_by_type[node_type]["memory"]
            - used_by_type[node_type]["memory"]
        )

        cpu_valid = (
              requested_cpu <= available_cpu
        )

        memory_valid = (
             requested_memory <= available_memory
         )

        if cpu_valid and memory_valid:
            print(
                f"[OK] node-type={node_type}: "
                f"requested_cpu={requested_cpu:.2f}, "
                f"available_cpu={available_cpu:.2f}, "
                f"requested_memory={requested_memory:.0f}, "
                f"available_memory={available_memory:.0f}"
             )
        else:
            print(
                f"[FAIL] node-type={node_type}: "
                f"requested_cpu={requested_cpu:.2f}, "
                f"available_cpu={available_cpu:.2f}, "
                f"requested_memory={requested_memory:.0f}, "
                f"available_memory={available_memory:.0f}"
            )

            success = False

        nodes_for_type = {
            node_name: resources
            for node_name, resources in available_by_node.items()
            if resources["node_type"] == node_type
        }

        placement_valid = can_place_workloads_on_nodes(
            workload_requests_by_type[node_type],
            nodes_for_type,
        )

        if placement_valid:
            print(
                f"[OK] node-type={node_type}: "
                f"per-node placement feasible"
            )
        else:
            print(
                f"[FAIL] node-type={node_type}: "
                f"per-node placement not feasible"
            )
            success = False


    return success

def validate_node_taints(scenario):
    nodes_data = get_nodes()

    expected_counts = {
        "cloud": scenario.nodes.cloud,
        "fog": scenario.nodes.fog,
        "edge": scenario.nodes.edge,
    }

    success = True

    for node in nodes_data["items"]:
        node_name = node["metadata"]["name"]


        labels = node["metadata"].get(
            "labels",
            {},
        )

        node_type = labels.get("node-type")

        if node_type not in expected_counts:
            continue

        taints = (
            node["spec"].get(
                "taints",
                [],
            )
        )

        expected_taints_found = False

        for taint in taints:
            if(
                taint.get("key") == "node-type"
                and taint.get("value") == node_type
                and taint.get("effect") == "NoSchedule"
            ):
                expected_taints_found = True
                break

        if expected_taints_found:
            print(
                f"[OK] {node_name} "
                f"({node_type}): "
                f"taint=node-type={node_type}:NoSchedule"
            )
        else:
            print(
                f"[FAIL] {node_name} "
                f"({node_type}): "
                f"taint=node-type={node_type}:NoSchedule"
            )

            success = False

    return success



def validate_workload_tolerations(
    workloads,
    namespace: str = "default",
):
    pods_data = get_pods(namespace)

    success = True

    for workload in workloads:
        workload_name = workload["metadata"]["name"]

        expected_node_type = (
            workload["spec"]
            ["template"]
            ["spec"]
            ["nodeSelector"]
            ["node-type"]
        )

        matching_pods = []

        for pod in pods_data["items"]:
            labels = pod["metadata"].get(
                "labels",
                {},
            )

            if labels.get("app") == workload_name:
                matching_pods.append(pod)

        if not matching_pods:
            print(
                f"[FAIL] {workload_name}: "
                f"no pod found"
            )
            success = False
            continue

        pod = matching_pods[0]

        tolerations = (
            pod["spec"].get(
                "tolerations",
                [],
            )
        )

        expected_toleration_found = False

        for toleration in tolerations:
            if (
                toleration.get("key") == "node-type"
                and toleration.get("operator") == "Equal"
                and toleration.get("value") == expected_node_type
                and toleration.get("effect") == "NoSchedule"
            ):
                expected_toleration_found = True
                break

        if expected_toleration_found:
            print(
                f"[OK] {workload_name}: "
                f"toleration=node-type="
                f"{expected_node_type}:NoSchedule"
            )
        else:
            print(
                f"[FAIL] {workload_name}: "
                f"missing toleration "
                f"node-type="
                f"{expected_node_type}:NoSchedule"
            )

            success = False

    return success

def get_namespaced_resource(
    kind: str,
    name: str,
    namespace: str,
):
    result = subprocess.run(
        [
            "kubectl",
            "get",
            kind,
            name,
            "-n",
            namespace,
            "-o",
            "json"
        ],
        text=True,
        capture_output=True,
    )

    if result.returncode != 0:
        return None

    return json.loads(result.stdout)

def can_service_account(
    service_account_name: str,
    verb: str,
    resource: str,
    namespace: str,
) -> bool:
    subject = (
        f"system:serviceaccount:"
        f"{namespace}:"
        f"{service_account_name}"
    )

    result = subprocess.run(
        [
            "kubectl",
            "auth",
            "can-i",
            verb,
            resource,
            "--as",
            subject,
            "-n",
            namespace,

        ],
        text=True,
        capture_output=True,
    )

    return (
        result.returncode == 0
        and result.stdout.strip() == "yes"
    )

def validate_overprivileged_service_account(
    pod,
    target: str,
    namespace: str,
) -> bool:
    service_account_name = f"{target}-overprivileged-sa"
    role_name = f"{target}-overprivileged-role"
    role_binding_name = f"{target}-overprivileged-binding"

    service_account= get_namespaced_resource(
        "serviceaccount",
        service_account_name,
        namespace,
    )

    role = get_namespaced_resource(
        "role",
        role_name,
        namespace,
    )

    role_binding = get_namespaced_resource(
        "rolebinding",
        role_binding_name,
        namespace,
    )

    pod_uses_service_account = (
        pod["spec"].get("serviceAccountName")
        == service_account_name
    )

    service_account_exists = (
        service_account is not None
    )

    role_binding_valid = False

    if role_binding is not None:
        subjects = role_binding.get(
            "subjects",
            [],
        )

        role_ref = role_binding.get(
            "roleRef",
            {},
        )

        subject_found = any(
            subject.get("kind") == "ServiceAccount"
            and subject.get("name") == service_account_name
            for subject in subjects
        )

        role_ref_valid = (
            role_ref.get("apiGroup")
            == "rbac.authorization.k8s.io"
            and role_ref.get("kind") == "Role"
            and role_ref.get("name") == role_name
        )

        role_binding_valid = (
            subject_found
            and role_ref_valid
        )

    role_permissions_valid = False

    if role is not None:
        rules = role.get(
            "rules",
            [],
        )

        role_permissions_valid = any(
            rule.get("apiGroups") == [""]
            and "pods" in rule.get("resources", [])
            and "secrets" in rule.get("resources", [])
            and "get" in rule.get("verbs", [])
            and "list" in rule.get("verbs", [])
            for rule in rules
        )

    can_get_secrets = can_service_account(
        service_account_name,
        "get",
        "secrets",
        namespace,
    )


    can_list_secrets = can_service_account(
        service_account_name,
        "list",
        "secrets",
        namespace,
    )


    cannot_delete_secrets = not can_service_account(
        service_account_name,
        "delete",
        "secrets",
        namespace,
    )

    return (
        pod_uses_service_account
        and service_account_exists
        and role_binding_valid
        and role_permissions_valid
        and can_get_secrets
        and can_list_secrets
        and cannot_delete_secrets
    )
