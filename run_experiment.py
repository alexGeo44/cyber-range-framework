from scenario_engine.deployer import (
    deploy_manifests,
    reset_namespace,
    )

from scenario_engine.validator import (
    wait_for_workloads,
    validate_workloads,
    validate_network_topology,
    validate_vulnerabilities,
    validate_cluster_nodes,
    validate_node_resources,
    validate_workload_resources,
    validate_aggregate_resources,
    validate_node_taints,
    validate_workload_tolerations,
    validate_target_service,
)

from scenario_engine.loader import load_scenario
from scenario_engine.generator import (
    generate_workloads,
    generate_services,
    generate_relationships,
    generate_network_policies,
    generate_default_deny_policies,
    generate_target_deployment,
    generate_target_service,
    save_workloads,
    save_services,
    save_network_policies,
    save_vulnerability_resources,
    save_target_resources,
    clean_manifest_directory,
)

from scenario_engine.target_catalog_loader import select_target

from scenario_engine.vulnerability_catalog import (
    select_vulnerabilities,
    inject_vulnerabilities,
    generate_vulnerability_resources,
)

from scenario_engine.ground_truth import (
    save_ground_truth,
)

from scenario_engine.validation_report import (
    save_validation_report,
)

from scenario_engine.artifacts import (
    prepare_experiment_directory
)

from scenario_engine.target_evaluation import (
    evaluate_agent_findings_file,
)

from pathlib import Path

import json

def main():
    scenario = load_scenario("scenarios/simple.yaml")

    namespace = f"cyber-range-{scenario.name}-{scenario.seed}"

    experiment_dir = (
        f"generated/{scenario.name}-{scenario.seed}"
    )

    manifests_dir = (
        f"{experiment_dir}/manifests"
    )

    prepare_experiment_directory(
        experiment_dir
    )

    cluster_valid = False
    taints_valid = False
    workload_tolerations_valid = False
    resources_valid = False
    aggregate_resources_valid = False
    workload_resources_valid = False
    target_valid = False
    scenario_valid = False
    network_valid = False
    vulnerabilities_valid = False
    validated_vulnerabilities = []

    evaluation = None

    agent_findings_path = Path(
        experiment_dir,
        "agent_findings.json"
    )


    print("Scenario loaded successfully")
    print(scenario)
    print(f"\nExperiment namespace: {namespace}")


    print("\nValidating cluster nodes...")

    cluster_valid = validate_cluster_nodes(
        scenario
    )

    if not cluster_valid:
        print("\nCluster validation failed")

        validation_path = save_validation_report(
                scenario=scenario,
                namespace=namespace,
                cluster_valid=cluster_valid,
                taints_valid=taints_valid,
                workload_tolerations_valid=workload_tolerations_valid,
                resources_valid=resources_valid,
                aggregate_resources_valid=aggregate_resources_valid,
                workload_resources_valid=workload_resources_valid,
                target_valid=target_valid,
                scenario_valid=scenario_valid,
                network_valid=network_valid,
                vulnerabilities_valid=vulnerabilities_valid,
                validated_vulnerabilities=validated_vulnerabilities,
                output_dir=experiment_dir,
        )

        print(
            f"\nValidation report saved to "
            f"{validation_path}"
        )

        return

    print("\nCluster validation successful")

    print("\nValidating node taints...")

    taints_valid = validate_node_taints(
        scenario
    )

    if not taints_valid:
        print("\nNode taint validation failed")

        validation_path = save_validation_report(
                scenario=scenario,
                namespace=namespace,
                cluster_valid=cluster_valid,
                taints_valid=taints_valid,
                workload_tolerations_valid=workload_tolerations_valid,
                resources_valid=resources_valid,
                aggregate_resources_valid=aggregate_resources_valid,
                workload_resources_valid=workload_resources_valid,
                target_valid=target_valid,
                scenario_valid=scenario_valid,
                network_valid=network_valid,
                vulnerabilities_valid=vulnerabilities_valid,
                validated_vulnerabilities=validated_vulnerabilities,
                output_dir=experiment_dir,
        )
        print(
            f"Validation report saved to "
            f"{validation_path}"
        )

        return

    print("\nNode taint validation successful")

    print("\nValidating node resources...")

    resources_valid = validate_node_resources(
        scenario
    )

    if not resources_valid:
        print("\nNode resource validation failed")
        validation_path = save_validation_report(
            scenario=scenario,
            namespace=namespace,
            cluster_valid=cluster_valid,
            taints_valid=taints_valid,
            workload_tolerations_valid=workload_tolerations_valid,
            resources_valid=resources_valid,
            aggregate_resources_valid=aggregate_resources_valid,
            workload_resources_valid=workload_resources_valid,
            target_valid=target_valid,
            scenario_valid=scenario_valid,
            network_valid=network_valid,
            vulnerabilities_valid=vulnerabilities_valid,
            validated_vulnerabilities=validated_vulnerabilities,
            output_dir=experiment_dir,
        )

        print(
            f"\nValidation report saved to "
            f"{validation_path}"
        )

        return

    print("\nNode resource validation successful")

    workloads = generate_workloads(scenario)

    target = select_target()

    print("\nSelected target:")
    print(" name:", target.name)
    print(" image:", target.image)
    print(" port:", target.port)
    print(" evaluation_mode:", target.evaluation_mode)

    target_node_type = (
        scenario.target.node_type
    )

    target_resources = scenario.nodes.resources[target_node_type]

    target_deployment = generate_target_deployment(
        target=target,
        node_type=target_node_type,
        resources=target_resources,
    )

    target_service = generate_target_service(target)

    workloads_with_target = workloads + [target_deployment]

    print("\nValidating aggregate workload resources...")

    aggregate_resources_valid = validate_aggregate_resources(
        workloads_with_target,
        namespace,
    )

    if not aggregate_resources_valid:
        print("\nAggregate resource validation failed")

        validation_path = save_validation_report(
            scenario=scenario,
            namespace=namespace,
            cluster_valid=cluster_valid,
            taints_valid=taints_valid,
            workload_tolerations_valid=workload_tolerations_valid,
            resources_valid=resources_valid,
            aggregate_resources_valid=aggregate_resources_valid,
            workload_resources_valid=workload_resources_valid,
            target_valid=target_valid,
            scenario_valid=scenario_valid,
            network_valid=network_valid,
            vulnerabilities_valid=vulnerabilities_valid,
            validated_vulnerabilities=validated_vulnerabilities,
            output_dir=experiment_dir,
            target=target,
        )

        print(
            f"\nValidation report saved to "
            f"{validation_path}"
        )

        return

    print("\nAggregate resource validation successful")


    services = generate_services(workloads)
    relationships = generate_relationships(workloads)

    default_deny_policies = generate_default_deny_policies(
        workloads
    )

    network_policies = (
        default_deny_policies
        + generate_network_policies(relationships)
    )

    selected_vulnerabilities = select_vulnerabilities(
        scenario,
        workloads,
    )

    workloads = inject_vulnerabilities(
        workloads,
        selected_vulnerabilities,
    )

    vulnerability_resources = generate_vulnerability_resources(
        workloads,
        selected_vulnerabilities,
    )


    print("\nGenerated workloads:")

    for workload in workloads:
        name = workload["metadata"]["name"]

        workload_type = (
            workload["spec"]
            ["template"]
            ["metadata"]
            ["labels"]
            ["workload-type"]
        )

        node_type = (
            workload["spec"]
            ["template"]
            ["spec"]
            ["nodeSelector"]
            ["node-type"]
        )

        print(
            f"{name} -> "
            f"type={workload_type}, "
            f"node={node_type}"
        )

    print("\nGenerated services:")

    for service in services:
        name = service["metadata"]["name"]
        port = service["spec"]["ports"][0]["port"]


        print(
            f"{name} -> "
            f"port={port}"
        )

    print("\nGenerated relationships:")
    for relationship in relationships:
        print(
            f"{relationship['source']} -> "
            f"{relationship['target']} "
            f"({relationship['type']})"
        )


    print("\nSelected vulnerabilities:")

    for vulnerability in selected_vulnerabilities:
        print(
            f"{vulnerability['target']} -> "
            f"{vulnerability['vulnerability_id']} "
            f"({vulnerability['severity']})"
        )


    print("\nGenerated network policies:")

    for policy in network_policies:
        print(policy["metadata"]["name"])


    print("\nCleaning generated manifest directory...")

    clean_manifest_directory(
        manifests_dir
    )

    save_workloads(
        workloads,
        output_dir=manifests_dir,
    )

    save_services(
        services,
        output_dir=manifests_dir,
    )

    save_network_policies(
        network_policies,
        output_dir=manifests_dir,
    )

    save_vulnerability_resources(
        vulnerability_resources,
        output_dir=manifests_dir,
    )

    save_target_resources(
        deployment=target_deployment,
        service=target_service,
        output_dir=manifests_dir,
    )
    


    print(f"\nWorkload, service and network policy manifests saved in {manifests_dir}")
    print(f"Experiment directory: {experiment_dir}")

    print(
        f"\nResetting experiment namespace: "
        f"{namespace}"
    )

    reset_namespace(namespace)

    print("\nDeploying manifests to Kubernetes...")

    deploy_manifests(
        manifests_dir,
        namespace=namespace,
    )

    print("\nWaiting for workloads to become ready...")

    ready = wait_for_workloads(
        workloads_with_target,
        namespace=namespace,
        timeout=300,
        interval=2
    )

    if not ready:
        print("\nWorkloads did not become ready before timeout")
    else:
        print("\nValidating scenario...")

        scenario_valid = validate_workloads(
        workloads,
        namespace=namespace,
        )

        if scenario_valid:
            print("\nScenario validation successful")

            print("\nValidating workload tolerations...")

            workload_tolerations_valid = validate_workload_tolerations(
                    workloads_with_target,
                    namespace=namespace,
            )

            if workload_tolerations_valid:
                print(
                    "\nWorkload toleration validation successful"
                )
            else:
                print(
                    "\nWorkload toleration failed"
                )

                validation_path = save_validation_report(
                        scenario=scenario,
                        namespace=namespace,
                        cluster_valid=cluster_valid,
                        taints_valid=taints_valid,
                        workload_tolerations_valid=workload_tolerations_valid,
                        resources_valid=resources_valid,
                        aggregate_resources_valid=aggregate_resources_valid,
                        workload_resources_valid=workload_resources_valid,
                        target_valid=target_valid,
                        scenario_valid=scenario_valid,
                        network_valid=network_valid,
                        vulnerabilities_valid=vulnerabilities_valid,
                        validated_vulnerabilities=validated_vulnerabilities,
                        output_dir=experiment_dir,
                        target=target,
                )

                print(
                    f"\nValidation report saved to "
                    f"{validation_path}"
                )

                return


            print("\nValidating workload resources...")

            workload_resources_valid = validate_workload_resources(
                workloads_with_target,
                scenario,
                namespace=namespace,
            )

            if workload_resources_valid:
                print(
                    "\nWorkload resource validation successful"
                )
            else:
                print(
                    "\nWorkload resource validation failed"
                )

            print("\nValidating target service...")

            target_valid = validate_target_service(
                target_deployment,
                target_service,
                namespace=namespace,
            )

            if target_valid:
                print("\nTarget service validation successful")
            else:
                print("\nTarget service validation failed")


            print("\nValidating network topology...")

            network_valid = validate_network_topology(
                workloads,
                services,
                relationships,
                namespace=namespace,
            )

            if network_valid:
                print("\nNetwork topology validation successful")
            else:
                print("\nNetwork topology validation failed")


            print("\nValidating injected vulnerabilities...")

            vulnerabilities_valid, validated_vulnerabilities = (
                validate_vulnerabilities(
                    selected_vulnerabilities,
                    namespace=namespace,
                )
            )


            if vulnerabilities_valid:
                print("\nVulnerability validation successful")

                ground_truth_path = save_ground_truth(
                    scenario,
                    validated_vulnerabilities,
                    output_dir=experiment_dir,
                )

                print(
                    f"\nVerified ground truth saved to "
                    f"{ground_truth_path}"
                )


            else:
                print("\nVulnerability validation failed")

        else:
            print("\nScenario validation failed")


    if agent_findings_path.exists():
        print("\nEvaluating agent findings...")

        evaluation = evaluate_agent_findings_file(
            target,
            str(agent_findings_path),
        )

        print(
            "\nAgent finding evaluation completed:"
            f"  matched={evaluation.matched_count},"
            f"  unmatched={evaluation.unmatched_count},"
            f" precision={evaluation.precision}"
        )


    validation_path = save_validation_report(
        scenario=scenario,
        namespace=namespace,
        cluster_valid=cluster_valid,
        taints_valid=taints_valid,
        workload_tolerations_valid=workload_tolerations_valid,
        resources_valid=resources_valid,
        aggregate_resources_valid=aggregate_resources_valid,
        workload_resources_valid=workload_resources_valid,
        target_valid=target_valid,
        scenario_valid=scenario_valid,
        network_valid=network_valid,
        vulnerabilities_valid=vulnerabilities_valid,
        validated_vulnerabilities=validated_vulnerabilities,
        output_dir=experiment_dir,
        target=target,
        evaluation=evaluation,
    )

    print(
        f"\nValidation report saved to "
        f"{validation_path}"
    )


if __name__ == "__main__":
    main()
