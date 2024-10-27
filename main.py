import logging
from pydantic import BaseModel, ValidationError
from flask import Flask, request, jsonify
from nlp_parser import parse_query
from action_mapper import map_action
from k8s_executor import execute_action

# Configure logging
logging.basicConfig(level=logging.DEBUG, 
                    format='%(asctime)s %(levelname)s - %(message)s',
                    filename='agent.log', filemode='a')

app = Flask(__name__)

class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    query: str
    answer: str

@app.route('/query', methods=['POST'])
def create_query():
    try:
        request_data = request.get_json()
        if not request_data or 'query' not in request_data:
            logging.error("Invalid request: 'query' field is missing.")
            return jsonify({"error": "Invalid request, 'query' field is required."}), 400
        query = request_data['query']
        logging.info(f"Received query: {query}")

        # Parse the query
        parsed_result = parse_query(query)
        logging.info(f"Parsed result: {parsed_result}")

        # Map the action
        mapped_action = map_action(parsed_result)
        logging.debug(f"Mapped action: {mapped_action}")

        # Execute the action and get the answer
        answer = execute_action(mapped_action)
        logging.info(f"Generated answer: {answer}")

        # Create and return the response model
        response = QueryResponse(query=query, answer=answer)
        return jsonify(response.dict())

    except ValidationError as e:
        logging.error(f"Validation error: {e}")
        return jsonify({"error": e.errors()}), 400
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        return jsonify({"error": "Internal server error."}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
