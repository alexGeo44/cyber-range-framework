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


def validate_aggregate_resources(
    workloads,
):
    nodes_data = get_nodes()

    success = True 

    capacity_by_type = {
        "cloud": {
            "cpu": 0.0,
            "memory": 0.0,
        },
        "fog": {
            "cpu": 0.0,
            "memory":0.0,
        },
        "edge": {
            "cpu": 0.0,
            "memory": 0.0,
        },
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

    for workload in workloads:
        pod_spec = (
            workload["spec"]
            ["template"]
            ["spec"]
        )

        node_type = (
                pod_spec["nodeSelector"]["node-type"]
        )

        container = pod_spec["containers"][0]

        requests = (
            container
            .get("resources", {})
            .get("requests", {})
        )

        requested_by_type[node_type]["cpu"] += (
                parse_cpu(requests["cpu"])
        )

        requested_by_type[node_type]["memory"] += (
                parse_memory(requests["memory"])
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
         )

        available_memory = (
            capacity_by_type[node_type]["memory"]
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
                f"requested_cpu={requested_cpu}, "
                f"available_cpu={available_cpu}, "
                f"requested_memory={requested_memory}, "
                f"available_memory={available_memory}"
             )
        else:
            print(
                f"[FAIL] node-type={node_type}: "
                f"requested_cpu={requested_cpu}, "
                f"available_cpu={available_cpu}, "
                f"requested_memory={requested_memory}, "
                f"available_memory={available_memory}"
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
