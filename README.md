# Cyber Range Framework

A reproducible Kubernetes-based cyber range framework for controlled security assessment experiments in hybrid cloud, fog, and edge environments.

## Overview

This project implements a Scenario Engine for generating, deploying, and validating reproducible cyber range scenarios on Kubernetes. It also includes a vulnerable-target integration layer, version-specific target ground-truth loading, and an initial pipeline for evaluating structured agent findings. Autonomous agents are not yet implemented.

The current implementation focuses on:

- deterministic scenario generation
- cloud/fog/edge workload placement
- Kubernetes scheduling enforcement
- detailed resource validation
- aggregate and per-node resource feasibility checks
- network isolation
- controlled vulnerability injection
- namespace-level RBAC misconfiguration injection
- live vulnerability verification
- verified ground-truth generation
- structured validation reporting
- automated validator testing
- interactive vulnerable-target selection and deployment
- Docker Hub and GitHub target providers
- immutable Docker image digests and Git commit identities
- partial, version-specific target ground truth
- structured agent finding evaluation (when findings are supplied)

## Architecture

The cyber range currently uses three Kubernetes node types:

- `cloud`
- `fog`
- `edge`

Each node type is represented using Kubernetes node labels and matching taints.

Workloads are assigned to the intended node type using:

- `nodeSelector`
- matching tolerations
- Kubernetes resource requests and limits

The current Minikube environment contains one node for each node type.

The resource validation logic is also designed to support multiple nodes of the same type.

## Scenario Engine

The Scenario Engine reads a YAML scenario definition and generates an experiment using a deterministic seed.

A scenario currently defines:

- scenario name
- deterministic seed
- cloud/fog/edge node counts
- resource profiles per node type
- workload count
- vulnerability count

Using the same scenario configuration and the same seed produces the same generated topology and vulnerability selection.

Each experiment is deployed into an isolated Kubernetes namespace derived from the scenario name and seed.

## Workloads

The current workload catalogue includes:

- web workloads
- API workloads
- database workloads

Example container images include:

```
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

```
node-type=cloud
node-type=fog
node-type=edge
```

Nodes also use matching `NoSchedule` taints.

Generated workloads include matching `nodeSelector` rules and tolerations so they are scheduled only on the intended node type.

The framework validates:

- Kubernetes node counts
- node labels
- node taints
- workload tolerations
- actual workload placement

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

- CPU requests
- memory requests
- CPU limits
- memory limits
- allocatable Kubernetes node resources
- aggregate resource demand per node type
- resources already consumed by Pods outside the experiment namespace
- available CPU and memory on each individual node
- workload placement feasibility on individual nodes
- resource fragmentation across nodes of the same type

## Pod Resource Accounting

The resource validator accounts for Kubernetes Pod scheduling requirements rather than only the first application container.

Resource accounting currently includes:

- multiple regular containers
- standard init containers
- restartable init containers / native sidecars
- Pod overhead
- existing non-terminal Pods already scheduled on the cluster

For regular containers, resource requests are summed.

For standard init containers, the effective request follows the Kubernetes scheduling model by considering the largest init-stage requirement against the steady-state workload requirement.

Restartable init containers are treated as cumulative because they continue running while later init containers and application containers execute.

Pod overhead is added to the final effective Pod request.

Pods in the `Succeeded` or `Failed` phase are excluded from active resource usage.

## Aggregate Resource Validation

The framework calculates the total resource capacity available for each node type.

It also calculates:

- resources already consumed by workloads outside the current experiment namespace
- resources requested by the generated scenario workloads

The validator checks that the requested scenario resources do not exceed the remaining aggregate CPU and memory capacity of the corresponding node type.

## Per-Node Placement Validation

Aggregate capacity alone is not sufficient when multiple nodes share the same node type.

A scenario may have enough total CPU and memory across a group of nodes while still be impossible to schedule because individual workloads cannot fit into the remaining capacity of any specific node.

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

- expected communication paths are reachable
- unauthorized communication paths remain blocked

Temporary probe Pods use the node-type scheduling constraints of the workload they represent.

## Pod Readiness

The framework waits for workloads to become ready before continuing with validation.

A workload is considered ready only when:

- the Pod is in the `Running` phase
- the Kubernetes Pod `Ready` condition is `True`

## Vulnerability Injection

The framework includes a controlled vulnerability catalogue covering container, host, identity, and RBAC-related security weaknesses.

The current catalogue includes:

### Container Security

- `run_as_root`
- `privileged_container`
- `allow_privilege_escalation`
- `unconfined_seccomp_profile`
- `add_sys_admin`
- `add_net_admin`
- `add_sys_ptrace`

### Host Exposure

- `host_network`
- `host_pid`
- `host_ipc`
- `host_path_mount`
- `writable_host_path`

### Identity and RBAC

- `automount_service_account_token`
- `overprivileged_service_account`

Vulnerabilities are selected deterministically based on the scenario seed and injected into generated Kubernetes resources.

The workload baseline uses secure defaults where appropriate.

For example, automatic ServiceAccount token mounting is disabled unless a selected vulnerability explicitly enables it.

## Namespace-Level RBAC Vulnerability

The `overprivileged_service_account` vulnerability creates controlled namespace-level RBAC objects.

The injected configuration includes:

- a dedicated ServiceAccount
- a namespace-scoped Role
- a RoleBinding
- a workload configured to use the ServiceAccount

The Role grants controlled read access to Pods and Secrets.

The validator checks both:

- the structural Role and RoleBinding configuration
- the effective permissions of the ServiceAccount using `kubectl auth can-i`

The current validation confirms that the ServiceAccount can:

- get Secrets
- list Secrets

and verifies that it cannot:

- delete Secrets

This allows the framework to validate the effective authorization behavior rather than only the intended RBAC manifest structure.

## Live Vulnerability Validation

After deployment, the framework reads the live Kubernetes configuration and verifies whether each selected vulnerability is actually present.

This ensures that vulnerabilities are not considered valid only because they were intended to be injected.

Live validation currently covers security properties such as:

- container security contexts
- privileged mode
- privilege escalation
- seccomp configuration
- Linux capabilities
- host namespaces
- hostPath volumes and mounts
- ServiceAccount token mounting
- RBAC resources
- effective ServiceAccount permissions

## Ground Truth

Verified vulnerabilities are stored in:

```
ground_truth.json
```

Only vulnerabilities confirmed in the deployed Kubernetes environment are included in the ground truth.

This prevents failed or incorrectly deployed vulnerabilities from being recorded as valid results.

## Validation Pipeline

The current validation pipeline checks:

- scenario configuration
- Kubernetes node counts
- node labels
- node taints
- node resources
- aggregate workload resource requirements
- per-node workload placement feasibility
- workload deployment
- Pod readiness
- workload scheduling
- workload tolerations
- workload resource requests and limits
- network topology
- injected vulnerabilities
- namespace-level RBAC configuration
- effective ServiceAccount permissions

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

- resource requests exceeding available capacity
- aggregate workload demand exceeding node-type capacity
- workloads that cannot fit on any individual node
- resource fragmentation across nodes
- missing Kubernetes node taints
- invalid workload tolerations
- workloads becoming unschedulable because of taint/toleration mismatches

The validation pipeline detects these conditions and marks the experiment invalid at the appropriate stage.

## Automated Tests

Validator unit tests are located in:

```
tests/test_validator_resources.py
```

The current automated tests cover:

- regular container resource accounting
- standard init container accounting
- restartable init container / native sidecar accounting
- Pod overhead
- multiple regular containers
- feasible per-node workload placement
- oversized workload rejection
- resource fragmentation detection
- backtracking-based workload placement

Run the tests with:

```bash
python3 -m pytest
```

## Vulnerable Target Integration

The Scenario Engine supports deploying an additional intentionally vulnerable application into the experiment namespace. Target definitions are stored in `targets/catalog.yaml`.

| Target | Origin | Repository | Port | Evaluation mode |
| --- | --- | --- | --- | --- |
| OWASP Juice Shop (`vulnerable-web`) | Docker Hub | `bkimminich/juice-shop` | 3000 | `unknown_ground_truth` |
| OWASP WebGoat (`webgoat`) | Docker Hub | `webgoat/webgoat` | 8080 | `unknown_ground_truth` |
| DVWA (`dvwa`) | GitHub | `digininja/DVWA` | 80 | `unknown_ground_truth` |

Target selection is interactive. Docker Hub targets require selecting an available image tag; the provider pulls the image and resolves its repository digest for deployment. GitHub targets are cloned at the configured ref, checked out at an exact commit, built into a Docker image, and loaded into Minikube. DVWA is configured at commit `068d974487a297c155c48722f9fcf7180a83adc4`.

The selected target receives a Deployment and a Kubernetes Service. The runner validates the target service as part of the experiment. Target placement currently uses `scenario.target.node_type`; the target name specified in `scenarios/simple.yaml` is not used to select the runtime catalog entry.

## Two Distinct Ground-Truth Sources

**Scenario ground truth** is produced by the existing vulnerability-injection pipeline. `scenario_engine/ground_truth.py` saves verified, injected Kubernetes vulnerabilities to the experiment's `ground_truth.json` after live validation.

**Target ground truth** describes built-in vulnerabilities of third-party vulnerable applications. It is stored separately in curated, version-specific YAML files under `targets/ground_truth/`. It must not be confused with injected scenario vulnerabilities.

Current curated target references:

- `targets/ground_truth/dvwa/068d974487a297c155c48722f9fcf7180a83adc4.yaml` — two findings (SQL injection and reflected XSS).
- `targets/ground_truth/juice-shop/v20.3.0.yaml` — two findings (SQL injection and reflected XSS).
- No curated WebGoat ground-truth YAML is included at present.

Both existing curated sets declare `complete: false`. They are **partial references**, not exhaustive inventories of vulnerabilities. All three targets are currently configured in `unknown_ground_truth` mode.

The `TargetGroundTruth` schema includes the target and repository identity, ref, declared scope, optional immutable image digest or commit SHA, completeness flag, and structured findings with provenance. The loader verifies identity and metadata consistency when a matching reference file is found. A target may use `known_ground_truth` only with an appropriate complete ground-truth set for a declared scope and immutable target identity. A target without a matching curated set can still be run in unknown-ground-truth mode.

## Agent Finding Evaluation (Initial Implementation)

The repository defines an `AgentFinding` schema and evaluation helpers in `scenario_engine/target_evaluation.py`. The supported input is a JSON **list** of structured findings placed at:

```text
generated/<scenario-name>-<seed>/agent_findings.json
```

Each entry requires `finding_id`, `title`, `category`, and `severity`, and may also include `affected_component`, `endpoint`, and `evidence`. Field values must satisfy the Pydantic model constraints.

When this file exists, `run_experiment.py` loads the findings, loads the selected target's version-matched ground truth, computes an `EvaluationSummary`, and embeds it into the validation report. Evaluation currently relies on **exact canonical `finding_id` equality**; it is not semantic or evidence-based matching. This is a preliminary evaluation interface, not an autonomous agent runtime. If no findings file exists, the report's `evaluation` field is `null`, meaning that no evaluation was performed—not that an agent detected zero vulnerabilities.

The evaluator reports total, matched, and unmatched finding counts. It avoids counting duplicate canonical IDs more than once as matched. For incomplete ground truth, `recall`, `false_negative_count`, and `f1_score` remain `null`. The current `precision` computation measures matches against the curated reference; **with partial ground truth this must not be interpreted as verified real-world precision**, because unmatched findings may be valid discoveries. Repeated findings also require explicit policy before metrics are used for a final experimental comparison.

**Important limitation:** If an experiment directory is reused, a previously existing `agent_findings.json` may be evaluated again. Findings must be managed explicitly and associated with the correct experiment run.

## Current Development Scope and Next Steps

The implemented system includes the Scenario Engine, target providers, ground-truth data models/loaders, and an initial finding evaluator. It does **not** yet implement autonomous reconnaissance or assessment agents, multi-agent coordination, policy-based agent governance, or full experimental observability.

Planned work includes deterministic ground-truth candidate extraction (initially from pinned DVWA source), candidate normalization and review, improved partial-ground-truth metric semantics, realistic finding matching, autonomous agent execution, governance controls, observability, and systematic experimental evaluation. Extracted candidates must not automatically be treated as verified findings or as proof of complete ground truth.

## Project Structure

Key repository paths (non-exhaustive):

```text
cyber-range-framework/
├── scenario_engine/
│   ├── artifacts.py
│   ├── deployer.py
│   ├── docker_hub.py
│   ├── generator.py
│   ├── github.py
│   ├── ground_truth.py
│   ├── models.py
│   ├── target_catalog.py
│   ├── target_catalog_loader.py
│   ├── target_evaluation.py
│   ├── target_ground_truth.py
│   ├── target_ground_truth_loader.py
│   ├── target_provider.py
│   ├── validation_report.py
│   ├── validator.py
│   └── vulnerability_catalog.py
├── scenarios/
│   └── simple.yaml
├── targets/
│   ├── catalog.yaml
│   └── ground_truth/
│       ├── dvwa/
│       │   └── 068d974487a297c155c48722f9fcf7180a83adc4.yaml
│       └── juice-shop/
│           └── v20.3.0.yaml
├── tests/
│   ├── test_validator_resources.py
│   ├── test_target_catalog_loader.py
│   ├── test_target_evaluation.py
│   ├── test_target_ground_truth.py
│   ├── test_target_ground_truth_loader.py
│   ├── test_target_provider.py
│   └── test_validation_report.py
├── run_experiment.py
└── README.md
```

Generated experiment artifacts are stored under `generated/` and excluded from version control.

## Running an Experiment

The project requires Python dependencies used by the repository, Docker, Minikube, and access to a Kubernetes cluster configured with the required cloud, fog, and edge node labels and taints. Docker Hub target selection requires network access; GitHub targets additionally require repository access and a working image-build/load toolchain.

Run:

```bash
python3 run_experiment.py
```

The runner reads `scenarios/simple.yaml` and prompts for a vulnerable target (and for a Docker Hub tag when applicable). It is interactive and is not currently a non-interactive batch command.

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
19. Generate the validation report, including target metadata and optional agent-finding evaluation.

## Current Status

The original end-to-end Scenario Engine functionality described below remains the core of the project; the vulnerable-target and evaluation extensions are described above. The original engine provides:

- deterministic scenario generation
- reproducible workload topology
- cloud/fog/edge workload placement
- Kubernetes scheduling enforcement
- node taint validation
- workload toleration validation
- detailed Pod resource accounting
- aggregate resource validation
- external Pod resource accounting
- per-node scheduling feasibility validation
- resource fragmentation detection
- backtracking-based workload placement validation
- Pod readiness validation
- automatic NetworkPolicy generation
- live network validation
- controlled container-security vulnerability injection
- controlled host-security vulnerability injection
- controlled identity and RBAC vulnerability injection
- live vulnerability verification
- effective RBAC permission validation
- verified ground-truth generation
- structured validation reporting
- controlled failure testing
- automated validator unit tests

## Tests

Run the repository test suite from the project root:

```bash
python3 -m pytest -q
```

The supplied repository snapshot was checked with 67 passing tests. This result covers the available automated tests and does not independently establish successful live deployment for every target and scenario.

