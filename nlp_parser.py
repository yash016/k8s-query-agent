from openai import OpenAI
import json
import os
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

# Get the API key from the environment variables
api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    raise ValueError("OPENAI_API_KEY not found. Ensure it is set in the .env file.")

# Create the OpenAI client with the API key
client = OpenAI(api_key=api_key)

def parse_query(query: str) -> dict:
    """
    Parses the user's natural language query using GPT-4 to extract components.
    Returns a dictionary containing the parsed components.
    """
    prompt = f"""
    You are a Kubernetes assistant. Extract the following information from the user's query and return it as a JSON object with the exact keys specified below. Do not include any additional information or keys.

    **Required JSON Structure:**
    ```json
    {{
        "action": string or null,
        "resource": string or null,
        "target_name": string or null,
        "namespace": string or null,
        "scope": string or null
    }}
    ```

    **Definitions:**
    - **action**: The operation to perform (e.g., "get", "delete", "scale", "list"). If the action is implied, infer it based on the context.
    - **resource**: The Kubernetes resource type in plural form (e.g., "pods", "deployments", "services").
    - **target_name**: The name of the specific resource, if any.
    - **namespace**: The Kubernetes namespace, if specified.
    - **scope**: The scope of the action ("cluster" or "namespace"). If not explicitly mentioned, infer based on the resource and context.

    **Additional Instructions:**
    - Use plural forms for resources when the query implies multiple instances.
    - Ensure all fields are populated appropriately, using `null` where applicable.
    - Respond strictly in JSON format as per the instructions.

    **User's Query:**
    "{query}"

    **Extracted JSON:**
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4",  # Ensure the correct model name is used
            messages=[
                {"role": "system", "content": "You are a Kubernetes assistant. Respond strictly in JSON format as per the instructions."},
                {"role": "user", "content": prompt}
            ],
            temperature=0,
            max_tokens=150
        )
        
        # Correct way to access response content
        assistant_reply = response.choices[0].message.content.strip()
        
        # Extract the JSON part from the response
        json_start = assistant_reply.find("{")
        json_end = assistant_reply.rfind("}") + 1
        json_str = assistant_reply[json_start:json_end]
        
        # Parse the JSON output
        parsed_result = json.loads(json_str)

        # Ensure all expected keys are present and in lowercase
        expected_keys = ['action', 'resource', 'target_name', 'namespace', 'scope']
        parsed_result_lower = {key.lower(): parsed_result.get(key.lower(), None) for key in expected_keys}

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
        'scope': None
    }

