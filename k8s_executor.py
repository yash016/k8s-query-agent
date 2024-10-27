import re
from kubernetes import client, config

# Load Kubernetes configuration
try:
    config.load_kube_config()
except:
    config.load_incluster_config()

# Initialize API clients
v1 = client.CoreV1Api()
apps_v1 = client.AppsV1Api()
batch_v1 = client.BatchV1Api()
rbac_v1 = client.RbacAuthorizationV1Api()
networking_v1 = client.NetworkingV1Api()

# Mappings with pluralized resource names
resource_api_mapping = {
    'pods': v1,
    'deployments': apps_v1,
    'services': v1,
    'nodes': v1,
    'namespaces': v1,
    'jobs': batch_v1,
    'cronjobs': batch_v1,
    'ingresses': networking_v1,
    'events': v1
}

def execute_action(mapped_action: dict) -> str:
    """
    Executes the action based on the mapped_action dictionary.
    Returns the result as a string.
    """
    action_type = mapped_action.get('action_type')
    resource = mapped_action.get('resource')
    target_name = mapped_action.get('target_name')
    namespace = mapped_action.get('namespace') or 'default'
    field = mapped_action.get('field')
    related_to = mapped_action.get('related_to', {'resource': None, 'name': None})

    api_client = resource_api_mapping.get(resource)
    if not api_client:
        return f"Unsupported resource type: {resource}"

    try:
        if action_type == 'get':
            return handle_get_action(api_client, resource, target_name, namespace, field, related_to)
        elif action_type == 'list':
            return handle_list_action(api_client, resource, namespace, field)
        elif action_type == 'logs':
            if resource == 'pods' and target_name:
                return get_pod_logs(target_name, namespace)
            elif resource == 'jobs' and target_name:
                return get_logs_from_job(target_name, namespace)
            else:
                return "Unsupported logs request."
        else:
            return "Unsupported action type."
    except client.exceptions.ApiException as e:
        return f"API Error: {e.reason} - {e.body}"

def handle_list_action(api_client, resource, namespace, field):
    """
    Handles 'list' actions for different Kubernetes resources.
    If 'field' is 'count', returns the count as a string.
    Otherwise, returns a comma-separated list of resource names.
    """
    if resource == 'pods':
        pods = api_client.list_namespaced_pod(namespace=namespace)
        if field == 'count':
            return str(len(pods.items))  # Return total count as a string
        pod_names = [simplify_name(pod.metadata.name) for pod in pods.items]
        return ', '.join(pod_names) if pod_names else "No pods found."
    
    elif resource == 'deployments':
        deployments = api_client.list_namespaced_deployment(namespace=namespace)
        if field == 'count':
            return str(len(deployments.items))  # Return total count as a string
        deployment_names = [simplify_name(dep.metadata.name) for dep in deployments.items]
        return ', '.join(deployment_names) if deployment_names else "No deployments found."
    
    elif resource == 'services':
        services = api_client.list_namespaced_service(namespace=namespace)
        if field == 'count':
            return str(len(services.items))  # Return total count as a string
        service_names = [simplify_name(svc.metadata.name) for svc in services.items]
        return ', '.join(service_names) if service_names else "No services found."
    
    elif resource == 'nodes':
        nodes = api_client.list_node()
        if field == 'count':
            return str(len(nodes.items))  # Return total count as a string
        node_names = [simplify_name(node.metadata.name) for node in nodes.items]
        return ', '.join(node_names) if node_names else "No nodes found."
    
    elif resource == 'jobs':
        jobs = api_client.list_namespaced_job(namespace=namespace)
        if field == 'count':
            return str(len(jobs.items))  # Return total count as a string
        job_names = [simplify_name(job.metadata.name) for job in jobs.items]
        return ', '.join(job_names) if job_names else "No jobs found."
    
    elif resource == 'cronjobs':
        cronjobs = api_client.list_namespaced_cron_job(namespace=namespace)
        if field == 'count':
            return str(len(cronjobs.items))  # Return total count as a string
        cronjob_names = [simplify_name(cj.metadata.name) for cj in cronjobs.items]
        return ', '.join(cronjob_names) if cronjob_names else "No cronjobs found."
    
    elif resource == 'ingresses':
        ingresses = api_client.list_namespaced_ingress(namespace=namespace)
        if field == 'count':
            return str(len(ingresses.items))  # Return total count as a string
        ingress_names = [simplify_name(ing.metadata.name) for ing in ingresses.items]
        return ', '.join(ingress_names) if ingress_names else "No ingresses found."
    
    elif resource == 'namespaces':
        namespaces = api_client.list_namespace()
        if field == 'count':
            return str(len(namespaces.items))  # Return total count as a string
        namespace_names = [ns.metadata.name for ns in namespaces.items]
        return ', '.join(namespace_names) if namespace_names else "No namespaces found."
    
    else:
        return f"Unsupported resource type: {resource}"

def handle_get_action(api_client, resource, name, namespace, field, related_to):
    """
    Handles 'get' actions for different Kubernetes resources.
    Returns specific information based on the field.
    """
    if resource == 'pods':
        if related_to['resource'] and related_to['name']:
            return get_pods_by_related_resource(related_to['resource'], related_to['name'], namespace)
        if name:
            pod = api_client.read_namespaced_pod(name=name, namespace=namespace)
            return get_pod_info(pod, field)
        else:
            return "Pod name not specified."

    elif resource == 'deployments':
        if name:
            deployment = api_client.read_namespaced_deployment(name=name, namespace=namespace)
            # Check if field relates to containers
            if field in ['containers', 'container_names']:
                return get_deployment_containers(deployment)
            return get_deployment_info(deployment, field)
        else:
            return "Deployment name not specified."

    elif resource == 'services':
        if name:
            service = api_client.read_namespaced_service(name=name, namespace=namespace)
            return get_service_info(service, field)
        else:
            return "Service name not specified."

    elif resource == 'nodes':
        if name:
            node = api_client.read_node(name=name)
            return get_node_info(node, field)
        else:
            return get_node_count(api_client)

    elif resource == 'namespaces':
        if name:
            ns = api_client.read_namespace(name=name)
            return get_namespace_info(ns, field)
        else:
            return list_namespaces(api_client)

    elif resource == 'jobs':
        if name:
            job = api_client.read_namespaced_job(name=name, namespace=namespace)
            return get_job_info(job, field)
        else:
            return "Job name not specified."

    elif resource == 'cronjobs':
        if name:
            cronjob = api_client.read_namespaced_cron_job(name=name, namespace=namespace)
            return get_cronjob_info(cronjob, field)
        else:
            return "CronJob name not specified."

    elif resource == 'ingresses':
        if name:
            ingress = api_client.read_namespaced_ingress(name=name, namespace=namespace)
            return get_ingress_info(ingress, field)
        else:
            return "Ingress name not specified."

    elif resource == 'events':
        if name:
            return get_pod_events(name, namespace)
        else:
            return "Pod name not specified for event retrieval."

    else:
        return f"Unsupported resource type: {resource}"

def get_pod_info(pod, field):
    """
    Retrieves specific information from a pod based on the field.
    """
    if field == 'status':
        return pod.status.phase
    elif field == 'labels':
        return format_labels(pod.metadata.labels)
    elif field == 'node':
        return pod.spec.node_name
    elif field == 'restart_count':
        restart_count = sum(cs.restart_count for cs in pod.status.container_statuses)
        return str(restart_count)
    elif field == 'container_count':
        return str(len(pod.spec.containers))
    elif field == 'replicas':
        # Pods don't have replicas; this field is typically for deployments
        return "Replicas field is not applicable to pods."
    else:
        return f"Pod '{simplify_name(pod.metadata.name)}' is in '{pod.status.phase}' state."

def get_deployment_info(deployment, field):
    """
    Retrieves specific information from a deployment based on the field.
    """
    if field == 'replicas':
        return str(deployment.spec.replicas)
    elif field == 'labels':
        return format_labels(deployment.metadata.labels)
    elif field == 'image':
        images = [container.image for container in deployment.spec.template.spec.containers]
        return ', '.join(images)
    elif field == 'status':
        conditions = deployment.status.conditions
        for condition in conditions:
            if condition.type == 'Available':
                return condition.status
        return "Unknown"
    elif field == 'container_count':
        containers = deployment.spec.template.spec.containers
        return str(len(containers))
    else:
        # Default response if field is not specifically handled
        available_replicas = deployment.status.available_replicas or 0
        return f"Deployment '{simplify_name(deployment.metadata.name)}' has {available_replicas} available replicas."

def get_service_info(service, field):
    """
    Retrieves specific information from a service based on the field.
    """
    if field == 'cluster_ip':
        return service.spec.cluster_ip
    elif field == 'external_ip':
        external_ips = service.status.load_balancer.ingress
        if external_ips:
            # Handle cases where IP or hostname is present
            ips = [ingress.ip or ingress.hostname for ingress in external_ips]
            return ', '.join(filter(None, ips)) or "No external IP assigned."
        elif service.spec.external_ips:
            return ', '.join(service.spec.external_ips)
        else:
            return "No external IP assigned."
    elif field == 'labels':
        return format_labels(service.metadata.labels)
    elif field == 'type':
        return service.spec.type
    else:
        # Default response if field is not specifically handled
        return f"Service '{simplify_name(service.metadata.name)}' has ClusterIP '{service.spec.cluster_ip}'."

def get_node_info(node, field):
    """
    Retrieves specific information from a node based on the field.
    """
    if field == 'status':
        conditions = node.status.conditions
        for condition in conditions:
            if condition.type == 'Ready':
                return condition.status
        return "Unknown"
    elif field == 'labels':
        return format_labels(node.metadata.labels)
    else:
        # Default to status if field is not specifically handled
        conditions = node.status.conditions
        for condition in conditions:
            if condition.type == 'Ready':
                return condition.status
        return "Unknown"

def get_namespace_info(ns, field):
    """
    Retrieves specific information from a namespace based on the field.
    """
    if field == 'status':
        return ns.status.phase
    elif field == 'labels':
        return format_labels(ns.metadata.labels)
    else:
        # Default response if field is not specifically handled
        return f"Namespace '{ns.metadata.name}' status is '{ns.status.phase}'."

def get_job_info(job, field):
    """
    Retrieves specific information from a job based on the field.
    """
    if field == 'status':
        if job.status.succeeded:
            return f"Job '{simplify_name(job.metadata.name)}' has succeeded."
        elif job.status.active:
            return f"Job '{simplify_name(job.metadata.name)}' is active."
        elif job.status.failed:
            return f"Job '{simplify_name(job.metadata.name)}' has failed."
        else:
            return "Unknown job status."
    elif field == 'labels':
        return format_labels(job.metadata.labels)
    elif field == 'completions':
        return str(job.spec.completions)
    else:
        # Default response if field is not specifically handled
        conditions = job.status.conditions
        return f"Job '{simplify_name(job.metadata.name)}' status is '{conditions}'."

def get_cronjob_info(cronjob, field):
    """
    Retrieves specific information from a cronjob based on the field.
    """
    if field == 'schedule':
        return cronjob.spec.schedule
    elif field == 'labels':
        return format_labels(cronjob.metadata.labels)
    else:
        # Default response if field is not specifically handled
        return f"CronJob '{simplify_name(cronjob.metadata.name)}' has schedule '{cronjob.spec.schedule}'."

def get_ingress_info(ingress, field):
    """
    Retrieves specific information from an ingress based on the field.
    """
    if field == 'hosts':
        hosts = [rule.host for rule in ingress.spec.rules]
        return ', '.join(hosts) if hosts else "No hosts defined."
    elif field == 'labels':
        return format_labels(ingress.metadata.labels)
    else:
        # Default response if field is not specifically handled
        hosts = [rule.host for rule in ingress.spec.rules]
        return f"Ingress '{simplify_name(ingress.metadata.name)}' has hosts '{', '.join(hosts)}'."

def get_deployment_containers(deployment):
    """
    Retrieves container names from a deployment.
    """
    container_names = [container.name for container in deployment.spec.template.spec.containers]
    return ', '.join(container_names) if container_names else "No containers found in the deployment."

def get_node_count(api_client):
    """
    Retrieves the count of nodes in the cluster.
    """
    nodes = api_client.list_node()
    return str(len(nodes.items))

def get_pod_logs(pod_name, namespace):
    """
    Retrieves logs from a specific pod.
    """
    try:
        logs = v1.read_namespaced_pod_log(name=pod_name, namespace=namespace, tail_lines=100)
        return logs or "No logs found."
    except client.exceptions.ApiException as e:
        return f"Failed to retrieve logs: {e}"

def get_pod_events(pod_name, namespace):
    """
    Retrieves events related to a specific pod.
    """
    try:
        field_selector = f"involvedObject.name={pod_name},involvedObject.kind=Pod"
        events = v1.list_namespaced_event(namespace=namespace, field_selector=field_selector)
        event_messages = [f"{event.type}: {event.message}" for event in events.items]
        return '\n'.join(event_messages) if event_messages else "No events found."
    except client.exceptions.ApiException as e:
        return f"Failed to retrieve events: {e}"

def get_pods_by_related_resource(resource, name, namespace):
    """
    Retrieves pods related to a specific resource, such as deployments or jobs.
    """
    if resource == 'deployments':
        return get_pods_by_deployment(name, namespace)
    elif resource == 'jobs':
        return get_pods_by_job(name, namespace)
    else:
        return "Unsupported related resource."

def get_pods_by_deployment(deployment_name, namespace='default'):
    """
    Retrieves pods created by a specific deployment.
    """
    try:
        deployment = apps_v1.read_namespaced_deployment(name=deployment_name, namespace=namespace)
        match_labels = deployment.spec.selector.match_labels
        if not match_labels:
            return "No match labels found in deployment."
        
        label_selector = ','.join([f"{k}={v}" for k, v in match_labels.items()])
        pods = v1.list_namespaced_pod(namespace=namespace, label_selector=label_selector)
        
        pod_names = [simplify_name(pod.metadata.name) for pod in pods.items]
        deployment_name_simplified = simplify_name(deployment_name)
        
        if pod_names:
            return deployment_name_simplified
        else:
            return f"No pods found for deployment '{deployment_name_simplified}'."
    except client.exceptions.ApiException as e:
        return f"Failed to retrieve pods: {e}"


def get_pods_by_job(job_name, namespace='default'):
    """
    Retrieves pods created by a specific job.
    """
    try:
        pods = v1.list_namespaced_pod(namespace=namespace, label_selector=f"job-name={job_name}")
        pod_names = [simplify_name(pod.metadata.name) for pod in pods.items]
        return ', '.join(pod_names) if pod_names else f"No pods found for job '{job_name}'."
    except client.exceptions.ApiException as e:
        return f"Failed to retrieve pods: {e}"

def get_logs_from_job(job_name, namespace):
    """
    Retrieves logs from all pods created by a specific job.
    """
    pods_response = get_pods_by_job(job_name, namespace)
    if pods_response.startswith("Failed"):
        return pods_response
    if pods_response.startswith("No pods found"):
        return f"No pods found for the job '{job_name}'."
    pod_names = [pod.strip() for pod in pods_response.split(',')]
    if not pod_names:
        return f"No pods found for the job '{job_name}'."
    # Collect logs from all pods
    all_logs = []
    for pod_name in pod_names:
        logs = get_pod_logs(pod_name, namespace)
        all_logs.append(f"Logs for pod '{pod_name}':\n{logs}")
    return '\n\n'.join(all_logs) if all_logs else "No logs found."

def format_labels(labels):
    """
    Formats the labels dictionary into a string.
    """
    return ', '.join([f"{k}={v}" for k, v in labels.items()]) if labels else "No labels found."

import re

def simplify_name(name):
    """
    Simplifies Kubernetes resource names by removing trailing numeric 
    or hash-like identifiers using regex.
    Example: "example-deployment-12345-abcde" becomes "example-deployment".
    """
    # Use regex to remove the trailing part starting with a dash followed by digits or hex-like strings
    simplified_name = re.sub(r'-[a-f0-9]+$', '', name)
    return simplified_name


def list_namespaces(api_client):
    """
    Lists all namespaces in the cluster.
    """
    namespaces = api_client.list_namespace()
    namespace_names = [ns.metadata.name for ns in namespaces.items]
    return ', '.join(namespace_names) if namespace_names else "No namespaces found."
