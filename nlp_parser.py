import json
import os
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

# Get the API key from the environment variables
api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    raise ValueError("OPENAI_API_KEY not found. Ensure it is set in the .env file.")

# Create the OpenAI client with the API key
client = OpenAI(api_key=api_key)

# Kubernetes-specific pluralization rules
PLURAL_RULES = {
    'pod': 'pods',
    'deployment': 'deployments',
    'service': 'services',
    'node': 'nodes',
    'namespace': 'namespaces',
    'job': 'jobs',
    'cronjob': 'cronjobs',
    'ingress': 'ingresses',
    'event': 'events'
}

def pluralize_resource(resource: str) -> str:
    """
    Pluralizes Kubernetes resource names based on predefined rules.
    """
    resource = resource.lower()
    return PLURAL_RULES.get(resource, resource)  # Default to the resource itself if no rule matches

def parse_query(query: str) -> dict:
    """
    Parses the user's natural language query using GPT-4 to extract components.
    Returns a dictionary containing the parsed components.
    """
    prompt = f"""
    You are a Kubernetes assistant. Extract the following information from the user's query and return it as a JSON object with the exact keys specified below. Do not include any additional information or keys.

    **Required JSON Structure:**
    {{
        "action": string or null,
        "resource": string or null,
        "target_name": string or null,
        "namespace": string or null,
        "field": string or null,
        "related_to": {{
            "resource": string or null,
            "name": string or null
        }}
    }}

    **Definitions:**
    - **action**: The operation to perform (e.g., "get", "list", "describe", "show", "fetch").
    - **resource**: The Kubernetes resource type in plural form (e.g., "pods", "deployments", "services").
    - **target_name**: The name of the specific resource, if any.
    - **namespace**: The Kubernetes namespace, if specified.
    - **field**: A specific attribute to retrieve (e.g., "logs", "containers", "container_count", "labels", "replicas", "IP address", "count", "status").
    - **related_to**: An object specifying a related resource, if applicable.

    **Additional Instructions:**
    - Use plural forms for resources when the query implies multiple instances.
    - Ensure all fields are populated appropriately, using `null` where applicable.
    - If the query mentions "logs", set the `field` to "logs".
    - If the query is about the number of containers, set `field` to "container_count".
    - If the query requests listing containers, set `field` to "containers".
    - Respond strictly in JSON format as per the instructions.

    **User's Query:**
    "{query}"

    **Extracted JSON:**
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a Kubernetes assistant. Respond strictly in JSON format as per the instructions."},
                {"role": "user", "content": prompt}
            ],
            temperature=0,
            max_tokens=150
        )

        assistant_reply = response.choices[0].message.content.strip()

        # Extract the JSON part from the response
        json_start = assistant_reply.find("{")
        json_end = assistant_reply.rfind("}") + 1
        json_str = assistant_reply[json_start:json_end]

        # Parse the JSON output
        parsed_result = json.loads(json_str)

        # Ensure all expected keys are present
        expected_keys = ['action', 'resource', 'target_name', 'namespace', 'field', 'related_to']
        parsed_result_lower = {key.lower(): parsed_result.get(key.lower(), None) for key in expected_keys}

        # Adjust parsed result for specific queries
        if "logs" in query.lower():
            parsed_result_lower['field'] = 'logs'
            parsed_result_lower['action'] = 'logs'
        elif "containers" in query.lower():
            if 'how many' in query.lower() or 'number of' in query.lower():
                parsed_result_lower['field'] = 'container_count'
            else:
                parsed_result_lower['field'] = 'containers'

        # Pluralize resource name if necessary
        if parsed_result_lower['resource']:
            parsed_result_lower['resource'] = pluralize_resource(parsed_result_lower['resource'])

        # Ensure related_to has both 'resource' and 'name'
        if not isinstance(parsed_result_lower.get('related_to'), dict):
            parsed_result_lower['related_to'] = {'resource': None, 'name': None}

        return parsed_result_lower

    except json.JSONDecodeError as jde:
        print(f"JSON Decode Error: {jde}")
    except Exception as e:
        print(f"Error parsing query with GPT-4: {e}")

    # Return a dictionary with all keys set to None in case of error
    return {
        'action': None,
        'resource': None,
        'target_name': None,
        'namespace': None,
        'field': None,
        'related_to': {'resource': None, 'name': None}
    }
