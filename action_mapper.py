def map_action(parsed_query: dict) -> dict:
    """
    Maps the parsed query to an executable action.
    Returns a dictionary containing the action type and necessary parameters.
    """
    action = parsed_query.get('action')
    resource = parsed_query.get('resource')
    target_name = parsed_query.get('target_name')
    namespace = parsed_query.get('namespace')
    field = parsed_query.get('field')
    related_to = parsed_query.get('related_to', {'resource': None, 'name': None})

    # Adjust action type based on the field or action
    if field == 'logs':
        action_type = 'logs'
    elif field == 'count':
        action_type = 'list'
    elif field in ['container_count', 'containers']:
        action_type = 'get' 
        if resource not in ['deployments', 'pods']:
            resource = 'deployments' 
    elif action in ['list', 'get', 'describe', 'status']:
        action_type = action
    else:
        action_type = 'get'  

    # Build mapped action dictionary
    mapped_action = {
        'action_type': action_type,
        'resource': resource,
        'target_name': target_name,
        'namespace': namespace,
        'field': field,
        'related_to': related_to
    }

    return mapped_action
