import os
from kubernetes.client.models import (
    V1Container,
    V1PodSpec,
    V1PodTemplateSpec,
    V1ObjectMeta,
    V1Job,
    V1JobSpec,
)
from kubernetes import client, config, watch
import time


def create_job_manifest(
    container_name,
    namespace,
    job_name,
    image,
    command,
    volume_mount_path,
    volume_name,
    volume_claim_name,
):
    container = V1Container(
        # env=[
        #     client.V1EnvVar(
        #         name="DEPLOYMENT_TYPE", value=os.environ.get("DEPLOYMENT_TYPE", "LOCAL")
        #     ),
        #     client.V1EnvVar(name="MODEL_CACHE", value=os.environ.get("MODEL_CACHE")),
        #     client.V1EnvVar(
        #         name="AZURE_OPENAI_ENDPOINT",
        #         value=os.environ.get("AZURE_OPENAI_ENDPOINT"),
        #     ),
        #     client.V1EnvVar(
        #         name="AZURE_OPENAI_API_KEY",
        #         value=os.environ.get("AZURE_OPENAI_API_KEY"),
        #     ),
        # ],
        name=container_name,
        image=image,
        image_pull_policy="Always",
        command=command,
        volume_mounts=[
            client.V1VolumeMount(mount_path=volume_mount_path, name=volume_name)
        ],
    )

    pod_spec = V1PodSpec(
        containers=[container],
        restart_policy="Never",
        service_account_name="default-editor",
        volumes=[
            client.V1Volume(
                name=volume_name,
                persistent_volume_claim=client.V1PersistentVolumeClaimVolumeSource(
                    claim_name=volume_claim_name
                ),
            )
        ],
    )

    pod_template_spec = V1PodTemplateSpec(
        metadata=V1ObjectMeta(
            labels={"app": job_name}, annotations={"sidecar.istio.io/inject": "false"}
        ),
        spec=pod_spec,
    )

    job_spec = V1JobSpec(
        template=pod_template_spec,
        backoff_limit=4,
        ttl_seconds_after_finished=60 * 60,  # 1 hour
    )

    job = V1Job(
        api_version="batch/v1",
        kind="Job",
        metadata=V1ObjectMeta(name=job_name, namespace=namespace),
        spec=job_spec,
    )

    return job


# Deploy the Job
def deploy_job(api_instance, namespace, job_manifest):
    try:
        api_response = api_instance.create_namespaced_job(namespace, job_manifest)
        print("Job created. Status='%s'" % str(api_response.status))
    except Exception as e:
        print("Exception when creating Job: %s\n" % e)


# Check the Job status
def check_job_status(api_instance: client.BatchV1Api, namespace, job_name):
    print("Checking Job status...")
    while True:
        time.sleep(5)  # Check status every 5 seconds
        try:
            job_status = api_instance.read_namespaced_job_status(job_name, namespace)
            if (
                job_status.status.succeeded is not None
                and job_status.status.succeeded > 0
            ):
                print("Job completed successfully")
                break
            elif job_status.status.failed is not None and job_status.status.failed > 0:
                print("Job failed")
                break
            else:
                print("Job in progress")
        except Exception as e:
            print("Error checking Job status: %s" % e)


def check_jobs(api_instance: client.BatchV1Api, namespace: str) -> client.V1JobList:
    return api_instance.list_namespaced_job(namespace)
