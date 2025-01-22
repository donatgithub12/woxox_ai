# from flask import Flask, request, jsonify, render_template
# import spacy
# from pymongo import MongoClient
# from flask_cors import CORS

# # Initialize Flask app
# app = Flask(__name__)
# CORS(app)  # Enable Cross-Origin Resource Sharing

# # Load the spaCy NLP model
# try:
#     nlp = spacy.load("en_core_web_sm")
# except OSError:
#     from spacy.cli import download
#     download("en_core_web_sm")
#     nlp = spacy.load("en_core_web_sm")

# # MongoDB connection settings
# client = MongoClient("mongodb://localhost:27017/")
# db = client["study_abroad_crm"]  # Database name
# collection = db["applicants"]  # Collection name

# # Define fields and synonyms for mapping
# field_mappings = {
#     "country_of_interest": ["interested in", "country"],
#     "state": ["state", "region", "district"],
#     "program": ["program", "course", "study"],
#     "name": ["name", "applicants", "person"],
# }

# def parse_query(user_query):
#     """
#     Parse the natural language query to identify fields and values.
#     """
#     doc = nlp(user_query)
#     filters = []
#     used_terms = set()
#     print("Doc ents: ", doc.ents)

#     for ent in doc.ents:
#         entity_text = ent.text.strip().lower()
#         preposition = None

#         # Check for preposition preceding the entity
#         if ent.root.dep_ == "pobj" and ent.root.head.pos_ == "ADP":
#             preposition = ent.root.head.text.lower()

#         # Determine the field based on context
#         if preposition == "from" and "state" not in used_terms:
#             filters.append({"state": {"$regex": ent.text.strip(), "$options": "i"}})
#             print(f"Mapped to state: {entity_text}")
#             used_terms.add("state")
#         elif "interested in" in user_query.lower() or "country" in user_query.lower():
#             if "country_of_interest" not in used_terms:
#                 filters.append({"country_of_interest": {"$regex": ent.text.strip(), "$options": "i"}})
#                 print(f"Mapped to country_of_interest: {entity_text}")
#                 used_terms.add("country_of_interest")

#     # Intent detection
#     intent = None
#     if "how many" in user_query.lower() or "count" in user_query.lower():
#         intent = "COUNT"
#     elif "list" in user_query.lower() or "show" in user_query.lower():
#         intent = "LIST"

#     # Combine filters into a single `$and` query
#     if filters:
#         mongo_filter = {"$and": filters}
#     else:
#         mongo_filter = {}

#     return mongo_filter, intent




# @app.route("/")
# def home():
#     """
#     Renders the HTML page for user interaction.
#     """
#     return render_template("query_window3.html")


# @app.route('/query', methods=['POST'])
# def process_query():
#     """
#     Process a natural language query to dynamically generate and execute a MongoDB query.
#     """
#     try:
#         if not request.is_json:
#             return jsonify({"error": "Request must be in JSON format."}), 400
#         user_query = request.json.get('query')

#         if not user_query:
#             return jsonify({"error": "Query field is required in the request."}), 400

#         print(f"Received query: {user_query}")

#         # Parse the user query
#         filters, intent = parse_query(user_query)
#         if not intent:
#             return jsonify({
#                 "error": "Could not determine the intent of the query. "
#                          "Supported intents include 'count' and 'list'."
#             }), 400

#         # Execute MongoDB query based on intent
#         if intent == "COUNT":
#             count = collection.count_documents(filters)
#             return jsonify({"query_filters": filters, "message": f"Total count: {count}"})

#         elif intent == "LIST":
#             projection = {"_id": 0}  # Exclude MongoDB's _id field in results
#             applicants = list(collection.find(filters, projection))
#             return jsonify({"query_filters": filters, "applicants": applicants})

#     except Exception as e:
#         return jsonify({"error": str(e)}), 500


# if __name__ == '__main__':
#     app.run(debug=True)

#==================================================================================================================================

from flask import Flask, request, jsonify, render_template
import spacy
from pymongo import MongoClient
from flask_cors import CORS

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable Cross-Origin Resource Sharing

# Load the spaCy NLP model
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    from spacy.cli import download
    download("en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

# MongoDB connection settings
client = MongoClient("mongodb://localhost:27017/")
db = client["study_abroad_crm"]  # Database name
collection = db["applicants"]  # Collection name

# Define fields and synonyms for mapping
field_mappings = {
    "country_of_interest": ["interested in", "country"],
    "state": ["state", "region", "district"],
    "program": ["program", "course", "study"],
    "name": ["name", "applicants", "person"],
}

def parse_query(user_query):
    """
    Parse the natural language query to identify fields and values.
    """
    doc = nlp(user_query)
    filters = []
    used_terms = set()

    for ent in doc.ents:
        entity_text = ent.text.strip().lower()
        preposition = None

        # Check for preposition preceding the entity
        if ent.root.dep_ == "pobj" and ent.root.head.pos_ == "ADP":
            preposition = ent.root.head.text.lower()

        # Determine the field based on context
        if preposition == "from" and "state" not in used_terms:
            filters.append({"state": {"$regex": ent.text.strip(), "$options": "i"}})
            used_terms.add("state")
        elif "interested in" in user_query.lower() or "country" in user_query.lower():
            if "country_of_interest" not in used_terms:
                filters.append({"country_of_interest": {"$regex": ent.text.strip(), "$options": "i"}})
                used_terms.add("country_of_interest")

    # Intent detection
    intent = None
    if "how many" in user_query.lower() or "count" in user_query.lower():
        intent = "COUNT"
    elif "list" in user_query.lower() or "show" in user_query.lower():
        intent = "LIST"

    # Combine filters into a single `$and` query
    if filters:
        mongo_filter = {"$and": filters}
    else:
        mongo_filter = {}

    return mongo_filter, intent

@app.route("/")
def home():
    """
    Renders the HTML page for user interaction.
    """
    return render_template("query_window3.html")

@app.route('/query', methods=['POST'])
def process_query():
    """
    Process a natural language query to dynamically generate and execute a MongoDB query.
    """
    try:
        if not request.is_json:
            return jsonify({"error": "Request must be in JSON format."}), 400
        user_query = request.json.get('query')

        if not user_query:
            return jsonify({"error": "Query field is required in the request."}), 400

        # Parse the user query
        filters, intent = parse_query(user_query)
        if not intent:
            return jsonify({
                "error": "Could not determine the intent of the query. "
                         "Supported intents include 'count' and 'list'."
            }), 400

        # Execute MongoDB query based on intent
        projection = {"_id": 0}  # Exclude MongoDB's _id field in results
        applicants = list(collection.find(filters, projection))

        if intent == "COUNT":
            count = len(applicants)
            return jsonify({"query_filters": filters, "message": f"Total count: {count}", "applicants": applicants})

        elif intent == "LIST":
            return jsonify({"query_filters": filters, "applicants": applicants})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/fetch_all', methods=['GET'])
def fetch_all_applicants():
    """
    Fetches all applicants from the database and returns them as JSON.
    """
    try:
        projection = {"_id": 0}  # Exclude MongoDB's _id field
        applicants = list(collection.find({}, projection))
        return jsonify({"applicants": applicants})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
