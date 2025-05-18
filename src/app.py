from flask import Flask, request, jsonify, render_template, Response
from src.classifier import classify_file
from dotenv import load_dotenv
import logging
import os
from functools import wraps
from flasgger import Swagger

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load API token
API_TOKEN = os.getenv("API_TOKEN")
if not API_TOKEN:
    raise RuntimeError("Missing API_TOKEN in environment variables")

# Initialize Flask app and Swagger
app = Flask(__name__)
swagger = Swagger(app, template={
    "swagger": "2.0",
    "info": {
        "title": "Your API",
        "description": "API for classifying files",
        "version": "1.0"
    },
    "securityDefinitions": {
        "Bearer": {
            "type": "apiKey",
            "name": "Authorization",
            "in": "header",
            "description": "Enter: **Bearer &lt;your-token&gt;**"
        }
    },
    "security": [{"Bearer": []}]
})

logger.info("App started")

# Allowed file types
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'docx', 'txt', 'xlsx', 'xls', 'csv'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Token-based authentication decorator
def requires_token_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return Response("Missing or invalid token", 401)
        
        token = auth_header.split(" ")[1]
        if token != API_TOKEN:
            return Response("Unauthorized", 403)
        return f(*args, **kwargs)
    return decorated

@app.route('/classify_file', methods=['POST'])
@requires_token_auth
def classify_file_route():
    """
    Classify a document file.
    ---
    consumes:
      - multipart/form-data
    security:
      - Bearer: []
    parameters:
      - in: formData
        name: file
        type: file
        required: true
        description: The document to classify
    responses:
      200:
        description: Classification result
        schema:
          type: object
          properties:
            file_class:
              type: string
            cost_in_microdollars:
              type: integer
            time_in_seconds:
              type: number
    """
    if 'file' not in request.files:
        return jsonify({"error": "No file part in the request"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "File type not allowed"}), 400

    file_class, cost, duration = classify_file(file)
    return jsonify({
        "file_class": file_class,
        "cost_in_microdollars": cost,
        "time_in_seconds": duration
    }), 200

@app.route('/')
def index():
    return '<h2>Visit <a href="/apidocs">/apidocs</a> to try the API</h2>'
