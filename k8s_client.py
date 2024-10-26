from kubernetes import client, config
import sys

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
    scope = parsed_result['scope']
    
    # Get the appropriate API client
    api_client = resource_api_mapping.get(resource_type)
    if not api_client:
        raise ValueError(f"Unsupported resource type: {resource_type}")

    if action == 'get':
        if resource_type == 'pods':
            if name:
                pod = api_client.read_namespaced_pod(name=name, namespace=namespace)
                status = pod.status.phase
                return status
            else:
                pods = api_client.list_namespaced_pod(namespace=namespace)
                pod_names = [pod.metadata.name for pod in pods.items]
                # Exclude identifiers
                simplified_names = [simplify_name(name) for name in pod_names]
                return ', '.join(simplified_names)
        elif resource_type == 'nodes':
            nodes = api_client.list_node()
            node_count = len(nodes.items)
            return str(node_count)
        elif resource_type == 'deployments':
            if name:
                deployment = api_client.read_namespaced_deployment(name=name, namespace=namespace)
                # Return relevant info
                return f"Deployment '{simplify_name(name)}' is available."
            else:
                deployments = api_client.list_namespaced_deployment(namespace=namespace)
                deployment_names = [dep.metadata.name for dep in deployments.items]
                simplified_names = [simplify_name(name) for name in deployment_names]
                return ', '.join(simplified_names)
        elif resource_type == 'services':
            services = api_client.list_namespaced_service(namespace=namespace)
            service_names = [svc.metadata.name for svc in services.items]
            simplified_names = [simplify_name(name) for name in service_names]
            return ', '.join(simplified_names)
        # Add other resources as needed
    elif action == 'list':
        # Similar to 'get' but may format the response differently
        pass
    # Since the assignment specifies only read actions, we avoid write actions like 'delete' or 'scale'
    else:
        raise ValueError(f"Unsupported action: {action}")

def simplify_name(name):
    # Simplify the resource name to exclude identifiers
    # Example: "mongodb-56c598c8fc" becomes "mongodb"
    return name.split('-')[0]
