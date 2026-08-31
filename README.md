# Cyber Range Framework

A reproducible Kubernetes-based cyber range framework for controlled security assessment experiments in hybrid cloud, fog, and edge environments.

## Overview

This project implements a Scenario Engine for generating, deploying, and validating reproducible cyber range scenarios on Kubernetes.

The current implementation focuses on:

* deterministic scenario generation
* cloud/fog/edge workload placement
* Kubernetes scheduling enforcement
* resource validation
* network isolation
* controlled vulnerability injection
* live vulnerability verification
* verified ground-truth generation
* structured validation reporting

## Architecture

The cyber range currently uses three Kubernetes node types:

* `cloud`
* `fog`
* `edge`

Each node type is represented using Kubernetes node labels and taints.

Workloads are assigned to the intended node type using:

* `nodeSelector`
* matching tolerations
* Kubernetes resource requests and limits

The current Minikube environment contains one node for each node type.

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

The framework validates both node taints and workload tolerations.

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
* available node resources
* aggregate resource demand per node type

## Network Isolation

The framework automatically generates Kubernetes NetworkPolicies.

Each workload receives a default-deny policy.

Only explicitly generated workload relationships are allowed.

The framework also performs live connectivity checks to verify that:

* expected communication paths are reachable
* unauthorized communication paths remain blocked

## Pod Readiness

The framework waits for workloads to become ready before continuing with validation.

A workload is considered ready only when the Kubernetes Pod `Ready` condition is `True`.

## Vulnerability Injection

The current vulnerability catalogue includes controlled container-security misconfigurations:

* `run_as_root`
* `privileged_container`
* `allow_privilege_escalation`

Vulnerabilities are selected deterministically based on the scenario seed and injected into generated workloads.

## Live Vulnerability Validation

After deployment, the framework reads the live Kubernetes Pod configuration and verifies whether the selected vulnerability is actually present.

This ensures that vulnerabilities are not considered valid only because they were intended to be injected.

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
* workload deployment
* Pod readiness
* workload scheduling
* workload tolerations
* workload resource requests and limits
* network topology
* injected vulnerabilities

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

The report makes it possible to identify whether each validation stage completed successfully.

## Controlled Failure Testing

The framework has also been tested using intentionally invalid configurations.

Tests performed so far include:

* resource requests exceeding available capacity
* aggregate workload demand exceeding node-type capacity
* missing Kubernetes node taints
* invalid workload tolerations
* workloads becoming unschedulable because of taint/toleration mismatches

The validation pipeline detects these conditions and stops the experiment at the appropriate stage.

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
├── run_experiment.py
├── .gitignore
└── README.md
```

## Running an Experiment

The project requires access to a Kubernetes cluster configured with the required cloud, fog, and edge node labels and taints.

Run:

```bash
python run_experiment.py
```

The experiment pipeline will:

1. Load the scenario.
2. Validate the Kubernetes environment.
3. Validate node taints and resources.
4. Generate workloads and relationships.
5. Inject controlled vulnerabilities.
6. Generate Kubernetes manifests.
7. Reset the experiment namespace.
8. Deploy the scenario.
9. Wait for workloads to become ready.
10. Validate workload scheduling.
11. Validate workload tolerations.
12. Validate workload resources.
13. Validate network connectivity.
14. Validate injected vulnerabilities.
15. Generate verified ground truth.
16. Generate the validation report.

## Current Status

The current implementation provides a working end-to-end Scenario Engine with:

* deterministic scenario generation
* reproducible workload topology
* cloud/fog/edge workload placement
* Kubernetes scheduling enforcement
* node taint validation
* workload toleration validation
* resource-aware validation
* aggregate resource validation
* Pod readiness validation
* automatic NetworkPolicy generation
* live network validation
* controlled vulnerability injection
* live vulnerability verification
* verified ground-truth generation
* structured validation reporting
* controlled failure testing

