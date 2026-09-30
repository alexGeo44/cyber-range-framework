# Cyber Range Framework

A reproducible Kubernetes-based cyber range framework for controlled security assessment experiments in hybrid cloud, fog, and edge environments.

## Overview

This project implements a Scenario Engine for generating, deploying, and validating reproducible cyber range scenarios on Kubernetes.

The current implementation focuses on:

* deterministic scenario generation
* cloud/fog/edge workload placement
* Kubernetes scheduling enforcement
* detailed resource validation
* aggregate and per-node resource feasibility checks
* network isolation
* controlled vulnerability injection
* namespace-level RBAC misconfiguration injection
* live vulnerability verification
* verified ground-truth generation
* structured validation reporting
* automated validator testing

## Architecture

The cyber range currently uses three Kubernetes node types:

* `cloud`
* `fog`
* `edge`

Each node type is represented using Kubernetes node labels and matching taints.

Workloads are assigned to the intended node type using:

* `nodeSelector`
* matching tolerations
* Kubernetes resource requests and limits

The current Minikube environment contains one node for each node type.

The resource validation logic is also designed to support multiple nodes of the same type.

## Scenario Engine

The Scenario Engine reads a YAML scenario definition and generates an experiment using a deterministic seed.

A scenario currently defines:

* scenario name
* deterministic seed
* cloud/fog/edge node counts
* resource profiles per node type
* workload count
* vulnerability count

Using the same scenario configuration and the same seed produces the same generated topology and vulnerability selection.

Each experiment is deployed into an isolated Kubernetes namespace derived from the scenario name and seed.

## Workloads

The current workload catalogue includes:

* web workloads
* API workloads
* database workloads

Example container images include:

```text
nginx:alpine
hashicorp/http-echo
postgres:alpine
```

The Scenario Engine automatically generates Kubernetes Deployments and Services for the workloads.

## Workload Relationships

The Scenario Engine also generates deterministic relationships between workloads.

These relationships define the expected communication topology of the scenario.

They are used to generate Kubernetes NetworkPolicies and to validate network connectivity after deployment.

## Kubernetes Scheduling

Cloud, fog, and edge nodes use the following labels:

```text
node-type=cloud
node-type=fog
node-type=edge
```

Nodes also use matching `NoSchedule` taints.

Generated workloads include matching `nodeSelector` rules and tolerations so they are scheduled only on the intended node type.

The framework validates:

* Kubernetes node counts
* node labels
* node taints
* workload tolerations
* actual workload placement

## Resource Profiles

Different Kubernetes resource profiles are defined for each node type.

Example:

```yaml
cloud:
  requests:
    cpu: "500m"
    memory: "512Mi"
  limits:
    cpu: "2"
    memory: "2Gi"

fog:
  requests:
    cpu: "250m"
    memory: "256Mi"
  limits:
    cpu: "1"
    memory: "1Gi"

edge:
  requests:
    cpu: "100m"
    memory: "128Mi"
  limits:
    cpu: "500m"
    memory: "512Mi"
```

The framework validates:

* CPU requests
* memory requests
* CPU limits
* memory limits
* allocatable Kubernetes node resources
* aggregate resource demand per node type
* resources already consumed by Pods outside the experiment namespace
* available CPU and memory on each individual node
* workload placement feasibility on individual nodes
* resource fragmentation across nodes of the same type

## Pod Resource Accounting

The resource validator accounts for Kubernetes Pod scheduling requirements rather than only the first application container.

Resource accounting currently includes:

* multiple regular containers
* standard init containers
* restartable init containers / native sidecars
* Pod overhead
* existing non-terminal Pods already scheduled on the cluster

For regular containers, resource requests are summed.

For standard init containers, the effective request follows the Kubernetes scheduling model by considering the largest init-stage requirement against the steady-state workload requirement.

Restartable init containers are treated as cumulative because they continue running while later init containers and application containers execute.

Pod overhead is added to the final effective Pod request.

Pods in the `Succeeded` or `Failed` phase are excluded from active resource usage.

## Aggregate Resource Validation

The framework calculates the total resource capacity available for each node type.

It also calculates:

* resources already consumed by workloads outside the current experiment namespace
* resources requested by the generated scenario workloads

The validator checks that the requested scenario resources do not exceed the remaining aggregate CPU and memory capacity of the corresponding node type.

## Per-Node Placement Validation

Aggregate capacity alone is not sufficient when multiple nodes share the same node type.

A scenario may have enough total CPU and memory across a group of nodes while still being impossible to schedule because individual workloads cannot fit into the remaining capacity of any specific node.

The framework therefore performs an additional per-node placement feasibility check.

For each node type, the validator:

1. calculates the remaining CPU and memory available on every individual node
2. collects the resource requirements of workloads assigned to that node type
3. attempts to assign each workload to a specific node
4. uses backtracking when an initial placement prevents a valid assignment

This allows the validator to detect resource fragmentation that would otherwise be hidden by aggregate capacity checks.

## Network Isolation

The framework automatically generates Kubernetes NetworkPolicies.

Each workload receives a default-deny policy.

Only explicitly generated workload relationships are allowed.

The framework also performs live connectivity checks to verify that:

* expected communication paths are reachable
* unauthorized communication paths remain blocked

Temporary probe Pods use the node-type scheduling constraints of the workload they represent.

## Pod Readiness

The framework waits for workloads to become ready before continuing with validation.

A workload is considered ready only when:

* the Pod is in the `Running` phase
* the Kubernetes Pod `Ready` condition is `True`

## Vulnerability Injection

The framework includes a controlled vulnerability catalogue covering container, host, identity, and RBAC-related security weaknesses.

The current catalogue includes:

### Container Security

* `run_as_root`
* `privileged_container`
* `allow_privilege_escalation`
* `unconfined_seccomp_profile`
* `add_sys_admin`
* `add_net_admin`
* `add_sys_ptrace`

### Host Exposure

* `host_network`
* `host_pid`
* `host_ipc`
* `host_path_mount`
* `writable_host_path`

### Identity and RBAC

* `automount_service_account_token`
* `overprivileged_service_account`

Vulnerabilities are selected deterministically based on the scenario seed and injected into generated Kubernetes resources.

The workload baseline uses secure defaults where appropriate.

For example, automatic ServiceAccount token mounting is disabled unless a selected vulnerability explicitly enables it.

## Namespace-Level RBAC Vulnerability

The `overprivileged_service_account` vulnerability creates controlled namespace-level RBAC objects.

The injected configuration includes:

* a dedicated ServiceAccount
* a namespace-scoped Role
* a RoleBinding
* a workload configured to use the ServiceAccount

The Role grants controlled read access to Pods and Secrets.

The validator checks both:

* the structural Role and RoleBinding configuration
* the effective permissions of the ServiceAccount using `kubectl auth can-i`

The current validation confirms that the ServiceAccount can:

* get Secrets
* list Secrets

and verifies that it cannot:

* delete Secrets

This allows the framework to validate the effective authorization behavior rather than only the intended RBAC manifest structure.

## Live Vulnerability Validation

After deployment, the framework reads the live Kubernetes configuration and verifies whether each selected vulnerability is actually present.

This ensures that vulnerabilities are not considered valid only because they were intended to be injected.

Live validation currently covers security properties such as:

* container security contexts
* privileged mode
* privilege escalation
* seccomp configuration
* Linux capabilities
* host namespaces
* hostPath volumes and mounts
* ServiceAccount token mounting
* RBAC resources
* effective ServiceAccount permissions

## Ground Truth

Verified vulnerabilities are stored in:

```text
ground_truth.json
```

Only vulnerabilities confirmed in the deployed Kubernetes environment are included in the ground truth.

This prevents failed or incorrectly deployed vulnerabilities from being recorded as valid results.

## Validation Pipeline

The current validation pipeline checks:

* scenario configuration
* Kubernetes node counts
* node labels
* node taints
* node resources
* aggregate workload resource requirements
* per-node workload placement feasibility
* workload deployment
* Pod readiness
* workload scheduling
* workload tolerations
* workload resource requests and limits
* network topology
* injected vulnerabilities
* namespace-level RBAC configuration
* effective ServiceAccount permissions

## Validation Report

Each experiment produces a JSON validation report.

Example:

```json
{
  "cluster_valid": true,
  "taints_valid": true,
  "workload_tolerations_valid": true,
  "resources_valid": true,
  "aggregate_resources_valid": true,
  "workload_resources_valid": true,
  "scenario_valid": true,
  "network_valid": true,
  "vulnerabilities_valid": true
}
```

The `aggregate_resources_valid` result includes both aggregate resource validation and per-node placement feasibility.

The report makes it possible to identify whether each validation stage completed successfully.

## Controlled Failure Testing

The framework has also been tested using intentionally invalid configurations.

Tests performed so far include:

* resource requests exceeding available capacity
* aggregate workload demand exceeding node-type capacity
* workloads that cannot fit on any individual node
* resource fragmentation across nodes
* missing Kubernetes node taints
* invalid workload tolerations
* workloads becoming unschedulable because of taint/toleration mismatches

The validation pipeline detects these conditions and marks the experiment invalid at the appropriate stage.

## Automated Tests

Validator unit tests are located in:

```text
tests/test_validator_resources.py
```

The current automated tests cover:

* regular container resource accounting
* standard init container accounting
* restartable init container / native sidecar accounting
* Pod overhead
* multiple regular containers
* feasible per-node workload placement
* oversized workload rejection
* resource fragmentation detection
* backtracking-based workload placement

Run the tests with:

```bash
python3 -m pytest
```

## Project Structure

```text
cyber-range-framework/
├── scenario_engine/
│   ├── __init__.py
│   ├── artifacts.py
│   ├── catalog.py
│   ├── deployer.py
│   ├── generator.py
│   ├── ground_truth.py
│   ├── loader.py
│   ├── models.py
│   ├── resources.py
│   ├── validation_report.py
│   ├── validator.py
│   └── vulnerability_catalog.py
├── scenarios/
│   └── simple.yaml
├── tests/
│   └── test_validator_resources.py
├── run_experiment.py
├── .gitignore
└── README.md
```

Generated experiment artifacts are stored under:

```text
generated/
```

and are excluded from version control.

## Running an Experiment

The project requires access to a Kubernetes cluster configured with the required cloud, fog, and edge node labels and taints.

Run:

```bash
python3 run_experiment.py
```

The experiment pipeline will:

1. Load the scenario.
2. Validate the Kubernetes environment.
3. Validate node taints and resources.
4. Validate aggregate and per-node scheduling capacity.
5. Generate workloads and workload relationships.
6. Select and inject controlled vulnerabilities.
7. Generate Services and NetworkPolicies.
8. Generate Kubernetes manifests.
9. Reset the experiment namespace.
10. Deploy the scenario.
11. Wait for workloads to become ready.
12. Validate workload scheduling.
13. Validate workload tolerations.
14. Validate workload resources.
15. Validate network connectivity.
16. Validate injected vulnerabilities.
17. Validate namespace-level RBAC configuration and effective permissions.
18. Generate verified ground truth.
19. Generate the validation report.

## Current Status

The current implementation provides a working end-to-end Scenario Engine with:

* deterministic scenario generation
* reproducible workload topology
* cloud/fog/edge workload placement
* Kubernetes scheduling enforcement
* node taint validation
* workload toleration validation
* detailed Pod resource accounting
* aggregate resource validation
* external Pod resource accounting
* per-node scheduling feasibility validation
* resource fragmentation detection
* backtracking-based workload placement validation
* Pod readiness validation
* automatic NetworkPolicy generation
* live network validation
* controlled container-security vulnerability injection
* controlled host-security vulnerability injection
* controlled identity and RBAC vulnerability injection
* live vulnerability verification
* effective RBAC permission validation
* verified ground-truth generation
* structured validation reporting
* controlled failure testing
* automated validator unit tests
