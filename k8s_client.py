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

# Mappings
resource_api_mapping = {
    'pods': v1,
    'deployments': apps_v1,
    'services': v1,
    'nodes': v1,
    # Add other resources as needed
}

def perform_action(parsed_result):
    resource_type = parsed_result['resource']
    action = parsed_result['action']
    name = parsed_result['target_name']
    namespace = parsed_result['namespace'] or 'default'
    field = parsed_result.get('field')
    related_to = parsed_result.get('related_to', {'resource': None, 'name': None})

    # Get the appropriate API client
    api_client = resource_api_mapping.get(resource_type)
    if not api_client:
        return f"Unsupported resource type: {resource_type}"

    # Handle different actions
    if action in ['get', 'list']:
        if resource_type == 'pods' and related_to['resource'] == 'deployments' and related_to['name']:
            return get_pods_by_deployment(related_to['name'], namespace)
        elif field == 'logs' and resource_type == 'pods' and name:
            return get_pod_logs(name, namespace)
        elif field == 'labels' and resource_type in ['pods', 'deployments'] and name:
            return get_resource_labels(api_client, resource_type, name, namespace)
        elif resource_type == 'pods' and name:
            pod = api_client.read_namespaced_pod(name=name, namespace=namespace)
            return pod.status.phase
        elif resource_type == 'nodes':
            # Count the number of nodes in the cluster
            nodes = api_client.list_node()
            node_count = len(nodes.items)
            return str(node_count)
        elif resource_type == 'deployments' and name:
            deployment = api_client.read_namespaced_deployment(name=name, namespace=namespace)
            return f"Deployment '{simplify_name(name)}' is available."
        elif resource_type == 'nodes' and action == 'list':
            nodes = api_client.list_node()
            return ', '.join([simplify_name(node.metadata.name) for node in nodes.items])
    else:
        return "Unsupported action or no relevant information found."


def get_pods_by_deployment(deployment_name, namespace='default'):
    try:
        deployment = apps_v1.read_namespaced_deployment(name=deployment_name, namespace=namespace)
        match_labels = deployment.spec.selector.match_labels
        label_selector = ','.join([f"{k}={v}" for k, v in match_labels.items()])
        pods = v1.list_namespaced_pod(namespace=namespace, label_selector=label_selector)
        pod_names = [pod.metadata.name for pod in pods.items]
        return ', '.join([simplify_name(n) for n in pod_names]) if pod_names else "No pods found."
    except client.exceptions.ApiException as e:
        return f"Failed to retrieve pods: {e}"

def get_pod_logs(pod_name, namespace):
    try:
        logs = v1.read_namespaced_pod_log(name=pod_name, namespace=namespace)
        return logs or "No logs found."
    except client.exceptions.ApiException as e:
        return f"Failed to retrieve logs: {e}"

def get_resource_labels(api_client, resource_type, name, namespace):
    try:
        if resource_type == 'pods':
            resource = api_client.read_namespaced_pod(name=name, namespace=namespace)
        elif resource_type == 'deployments':
            resource = apps_v1.read_namespaced_deployment(name=name, namespace=namespace)
        labels = resource.metadata.labels
        return ', '.join([f"{k}={v}" for k, v in labels.items()])
    except client.exceptions.ApiException as e:
        return f"Failed to retrieve labels: {e}"

import re

import re

def simplify_name(name):
    # Split the name by dashes
    parts = name.split('-')

    # Remove parts that are purely numbers or appear to be hash-like strings
    simplified_parts = []
    for part in parts:
        # Keep the part if it's not purely numeric or a random hash-like string
        if not re.match(r'^\d+$', part) and not re.match(r'^[a-f0-9]{4,}$', part):
            simplified_parts.append(part)

    # Join the remaining parts back together
    return '-'.join(simplified_parts) if simplified_parts else name


