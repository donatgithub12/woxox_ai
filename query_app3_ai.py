from flask import Flask, request, jsonify, render_template
from pymongo import MongoClient
from flask_cors import CORS
import os
import openai
import ast
import re

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable Cross-Origin Resource Sharing

# MongoDB connection settings
client = MongoClient("mongodb://localhost:27017/")
db = client["study_abroad_crm"]  # Database name
collection = db["applicants"]  # Collection name

# Fetch the OpenAI API key from environment variables
openai.api_key = os.getenv("sample")

if not openai.api_key:
    raise ValueError("OPENAI_API_KEY environment variable is not set!")

import json
import re

def generate_mongo_query(user_query):
    """
    Generate MongoDB query or aggregation pipeline from natural language using OpenAI API.
    """
    try:
        # Add MongoDB collection structure for context
        collection_structure = (
            "The MongoDB collection 'applicants' has the following fields: "
            "'_id' (ObjectId), 'id' (integer), 'name' (string), 'country_of_interest' (string), "
            "'program' (string), and 'state' (string)."
        )
        full_query = f"{collection_structure} {user_query}"

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "system", "content": "You are an assistant that generates valid MongoDB queries or aggregation pipelines."},
                      {"role": "user", "content": full_query}],
            max_tokens=200,
            temperature=0
        )

        query_text = response['choices'][0]['message']['content'].strip()
        if not query_text:
            return {"error": "Generated query is empty or invalid."}

        print("Generated Query (Raw):", query_text)  # Debugging

        # Match the MongoDB query part (e.g., { country_of_interest: "Canada" })
        query_match = re.search(r'\{.*\}', query_text)
        if query_match:
            query = query_match.group(0)
            
            # Replace unquoted field names with quoted field names
            query = re.sub(r'(\w+)(?=\s*:)', r'"\1"', query)  # Wrap field names with double quotes
            
            try:
                # Convert the query string into a dictionary
                mongo_query = json.loads(query)
                return mongo_query
            except json.JSONDecodeError as e:
                return {"error": f"Failed to decode JSON from response: {str(e)}"}
        else:
            return {"error": "No valid MongoDB query found in the response."}

    except (SyntaxError, ValueError) as parse_error:
        return {"error": f"Invalid query format generated: {str(parse_error)}"}
    except Exception as e:
        return {"error": f"Error generating MongoDB query: {str(e)}"}





@app.route("/")
def home():
    """
    Render the HTML page for user interaction.
    """
    return render_template("query_window3.html")

@app.route('/query', methods=['POST'])
def process_query():
    """
    Process a natural language query using OpenAI API to generate and execute a MongoDB query or aggregation pipeline.
    """
    try:
        if not request.is_json:
            return jsonify({"error": "Request must be in JSON format."}), 400

        user_query = request.json.get('query')

        if not user_query:
            return jsonify({"error": "Query field is required in the request."}), 400

        # Generate MongoDB query using OpenAI API
        mongo_query = generate_mongo_query(user_query)
        if "error" in mongo_query:
            # Return error message if the query cannot be generated
            return jsonify({"error": mongo_query["error"]}), 400

        print("Mongo Query:", mongo_query)  # Debugging

        # Execute the query
        if isinstance(mongo_query, dict):
            # Simple filter or count query
            if "count" in user_query.lower():
                # Count documents matching the filter
                count = collection.count_documents(mongo_query)
                return jsonify({"message": "Query executed successfully.", "count": count})
            else:
                # Fetch documents matching the filter
                results = list(collection.find(mongo_query, {"_id": 0}))
        elif isinstance(mongo_query, list):
            # Execute aggregation pipelines
            results = list(collection.aggregate(mongo_query))
        else:
            raise ValueError("Generated query is not a valid MongoDB query or pipeline.")

        if not results:
            return jsonify({"message": "No data found.", "results": []})

        return jsonify({"message": "Query executed successfully.", "results": results})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/fetch_all', methods=['GET'])
def fetch_all_applicants():
    """
    Fetch all applicants from the database and return them as JSON.
    """
    try:
        projection = {"_id": 0}  # Exclude MongoDB's _id field
        applicants = list(collection.find({}, projection))
        return jsonify({"applicants": applicants})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
