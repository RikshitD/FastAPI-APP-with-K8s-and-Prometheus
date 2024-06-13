Deployed a Fast API pod on local system using the minikube which can perform following operations:

1. [POST]: “/createDeployment/<deployment_name>” 
Apply a Kubernetes deployment of name supplied in the post request.

2. [GET]: “/getPromdetails”
Fetch the details of all the running pods from the Prometheus client
