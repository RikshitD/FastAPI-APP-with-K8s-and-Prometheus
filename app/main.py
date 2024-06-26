from fastapi import FastAPI, HTTPException
from kubernetes import client, config
from kubernetes.client.rest import ApiException
from pydantic import BaseModel
from prometheus_client import CollectorRegistry, Gauge, generate_latest

app = FastAPI()

config.load_incluster_config()

class DeploymentConfig(BaseModel):
    image: str
    replicas: int

@app.post("/createDeployment/{deployment_name}")
async def create_deployment(deployment_name: str, config: DeploymentConfig):
    api_instance = client.AppsV1Api()
    
    deployment = client.V1Deployment(
        api_version="apps/v1",
        kind="Deployment",
        metadata=client.V1ObjectMeta(name=deployment_name),
        spec=client.V1DeploymentSpec(
            replicas=config.replicas,
            selector={"matchLabels": {"app": deployment_name}},
            template=client.V1PodTemplateSpec(
                metadata=client.V1ObjectMeta(labels={"app": deployment_name}),
                spec=client.V1PodSpec(containers=[
                    client.V1Container(
                        name=deployment_name,
                        image=config.image,
                        ports=[client.V1ContainerPort(container_port=80)]
                    )
                ])
            )
        )
    )

    try:
        api_response = api_instance.create_namespaced_deployment(
            namespace="default",
            body=deployment
        )
        return {"message": "Deployment created successfully", "details": str(api_response)}
    except ApiException as e:
        raise HTTPException(status_code=e.status, detail=str(e))

@app.get("/getPromdetails")
async def get_prom_details():
    v1 = client.CoreV1Api()
    
    try:
        pods = v1.list_pod_for_all_namespaces(watch=False)
        pod_details = []
        for pod in pods.items:
            pod_info = {
                "name": pod.metadata.name,
                "namespace": pod.metadata.namespace,
                "status": pod.status.phase,
                "node_name": pod.spec.node_name,
                "start_time": pod.status.start_time
            }
            pod_details.append(pod_info)
        
        registry = CollectorRegistry()
        gauge = Gauge('pod_running_status', 'Pod running status', ['namespace', 'pod_name', 'node_name'], registry=registry)

        for pod in pod_details:
            if pod['status'] == 'Running':
                gauge.labels(namespace=pod['namespace'], pod_name=pod['name'], node_name=pod['node_name']).set(1)
            else:
                gauge.labels(namespace=pod['namespace'], pod_name=pod['name'], node_name=pod['node_name']).set(0)
        
        prom_metrics = generate_latest(registry)
        
        return {
            "pod_details": pod_details,
            "prometheus_metrics": prom_metrics.decode('utf-8')
        }
        
    except ApiException as e:
        raise HTTPException(status_code=e.status, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
