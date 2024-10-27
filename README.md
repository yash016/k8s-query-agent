# Kubernetes Query Agent (K8S-Query-Agent)

## Overview
This repository contains a Kubernetes Query Agent (K8S-Query-Agent), an AI-powered tool designed to interact with a Kubernetes cluster and answer natural language queries about deployed applications. This tool is particularly useful for developers, DevOps engineers, and SREs who need to gather insights or troubleshoot Kubernetes clusters efficiently. The agent uses a combination of prompting and rule-based approaches to provide accurate and relevant responses to user queries.

### Purpose & Practicality
The K8S-Query-Agent was built to make the management of Kubernetes clusters easier by allowing users to ask questions in natural language. This practical agent can help users retrieve information about pods, deployments, nodes, services, and other resources without needing in-depth Kubernetes knowledge or CLI commands. It is intended to save time, reduce manual queries, and simplify interactions with Kubernetes clusters.

### Current Approach
This implementation uses a **combination of a prompting approach for natural language understanding (NLU) and a rule-based approach for structured retrieval from the Kubernetes API**. The prompting approach, leveraging GPT-4, helps break down user queries into structured components, while the rule-based methods ensure accurate mapping to Kubernetes API calls.

#### Assumptions
- **Nature of Queries**: The queries are assumed to be focused on reading operations (e.g., retrieving status, counts, logs).
- **Scope of Examples**: The agent was tested with around 30 queries similar to the provided examples to ensure robustness.
- **Shorter Development Cycle**: To maintain a quick development pace, the solution was designed to be modular and easily extendable, allowing for future improvements.

#### Problem Breakdown
The problem was tackled by asking the following questions:
1. **How to interpret user queries effectively?**
2. **How to map parsed queries to Kubernetes API calls?**
3. **How to clean and format the response before sending it back?**

### Implementation Breakdown

#### Module Structure
The approach was broken down into three main modules, each serving a distinct function:

1. **Parser Module**
   - **Purpose**: Responsible for interpreting user queries and extracting components such as actions, resources, target names, namespaces, etc.
   - **Relevant File**: `nlp_parser.py`
   - **Description**: This module uses a combination of prompting (via GPT-4) and rule-based methods to interpret queries and break them into components. It defines specific rules for pluralization, action mapping, and relevant fields based on Kubernetes resources. The `parse_query()` function is central to this module, which returns structured information from user queries.

2. **Kubernetes Client Module**
   - **Purpose**: Interfaces with the Kubernetes API to retrieve information based on parsed queries.
   - **Relevant File**: `k8s_executor.py`
   - **Description**: This module handles the connection to the Kubernetes cluster, maps resources to API calls, and retrieves relevant information such as status, replicas, container counts, etc. The `execute_action()` function is used to handle API calls, while helper functions format responses.

3. **Response Formatter**
   - **Purpose**: Cleans and formats the output to provide clear answers.
   - **Relevant Files**: Included within `k8s_executor.py` functions
   - **Description**: Functions such as `simplify_name()` are used to clean resource names by removing numeric suffixes, making the response more readable. Other helper functions format labels, lists, and conditions into user-friendly outputs.

#### Mini Diagram of the Approach
```plaintext
                ┌─────────────┐
                │ User Query  │
                └─────┬───────┘
                      │
                      ▼
             ┌─────────────────┐
             │ Parser Module   │
             │  (nlp_parser)   │
             └─────────────────┘
                      │
                      ▼
            ┌─────────────────────┐
            │ Kubernetes Client   │
            │    Module           │
            │  (k8s_executor)     │
            └─────────────────────┘
                      │
                      ▼
            ┌────────────────────┐
            │ Response Formatter │
            │ (k8s_executor)     │
            └────────────────────┘
                      │
                      ▼
               ┌──────────────┐
               │  API Output  │
               └──────────────┘
```

## Previous Approaches

The initial approaches were foundational steps that informed the development of the current solution. These iterations helped identify effective parsing methods and API mapping strategies by exploring different natural language processing (NLP) techniques and retrieval logic.

### Iteration 1
- **Approach**: 
  - The initial implementation focused on using regular expressions (regex) for parsing user queries. The primary goal was to extract key components such as action types, resources, and target names. The retrieval logic was manually mapped to the Kubernetes API.
- **Outcome**: 
  - While this approach provided a basic structure for parsing, it was limited in handling the complexity of natural language variations, resulting in lower accuracy for nuanced queries. It served as a stepping stone to understand the basic requirements and constraints.

### Iteration 2
- **Approach Summary**:
  - **Parser**: The parsing logic was upgraded by switching to spaCy, an advanced NLP library with GloVe embeddings. Dependency parsing and word similarity matching were employed to better interpret user queries.
  - **Retrieval**: The elements extracted from parsing were mapped to corresponding Kubernetes API calls, aiming for a more comprehensive handling of resources and actions.
- **Outcome**: 
  - The outcome was similar to that of the first iteration, with improved parsing ability from the queries. However, this approach still struggled to classify the intent of the query efficiently, indicating that additional refinement was needed to better interpret user intent across diverse queries.

### Iteration 3 (Current Approach)
Building on the learnings from the previous iterations, the current approach integrates GPT-4 for more flexible parsing and uses a structured rule-based API handling mechanism. This combination incorporates the best aspects of the earlier techniques while offering a more practical and efficient solution for handling diverse Kubernetes queries.

## Resources
This section lists the resources used in building and refining the Kubernetes Query Agent:

- **OpenAI GPT-4 API Documentation**: For understanding and implementing the prompting approach for NLP.
  - [OpenAI GPT-4 Documentation](https://platform.openai.com/docs/overview)
- **Kubernetes API Concepts**: For understanding how to interact with the Kubernetes API.
  - [Kubernetes API Documentation](https://kubernetes.io/docs/reference/using-api/api-concepts/)
- **Minikube Documentation**: To set up and manage a local Kubernetes cluster.
  - [Minikube Documentation](https://minikube.sigs.k8s.io/docs/)
- **Pydantic Documentation**: For handling API responses and request validation.
  - [Pydantic Documentation](https://docs.pydantic.dev/latest/)
- **Retrieval-Augmented Generation (RAG)**: To understand retrieval methods for LLMs.
  - [RAG Overview](https://weaviate.io/blog/introduction-to-rag)
- **Dependency Parsing Guide**: For implementing dependency parsing in NLP.
  - [Dependency Parsing](https://towardsdatascience.com/natural-language-processing-dependency-parsing-cf094bbbe3f7)
- **Prompting Guide**: To design and refine the prompting mechanism.
  - [Prompting Guide](https://www.promptingguide.ai/)
- **Postman**: For testing the agent’s API endpoints.
  - [Postman](https://www.postman.com/)

## Conclusion
The Kubernetes Query Agent has been built and refined through a series of iterations that focus on practical NLP techniques and effective API retrieval strategies. The current implementation combines modern NLP methods with structured data handling, making it both efficient and scalable for Kubernetes-based applications.
