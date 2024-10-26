import logging
from pydantic import BaseModel, ValidationError
from flask import Flask, request, jsonify
from nlp_parser import parse_query  # Assuming utils.py contains parse_query
from k8s_client import perform_action  # Import from k8s_client.py

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
        # Validate and parse the incoming request
        request_data = request.get_json()
        if not request_data or 'query' not in request_data:
            return jsonify({"error": "Invalid request, 'query' field is required."}), 400
        query = request_data['query']

        # Log the question
        logging.info(f"Received query: {query}")

        # Parse the query
        parsed_result = parse_query(query)
        logging.info(f"Parsed result: {parsed_result}")

        # Perform the Kubernetes action and get the answer
        try:
            answer = perform_action(parsed_result)
        except Exception as e:
            answer = f"Failed to perform action: {e}"
            logging.error(answer)

        # Log the generated answer
        logging.info(f"Generated answer: {answer}")

        # Create and return the response model
        response = QueryResponse(query=query, answer=answer)
        return jsonify(response.dict())

    except ValidationError as e:
        logging.error(f"Validation error: {e}")
        return jsonify({"error": e.errors()}), 400

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
