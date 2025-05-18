# Heron Coding Challenge - File Classifier

Essential:
Make an OpenAI API account and generate an API Key. 
Contact Sidhee for a sample API Key.

Running Locally

1. Clone the repository:
    ```shell
    git clone <repository_url>
    cd join-the-seige
    ```

2. Add the following variables to a .env file:

OPENAI_API_KEY=your-key-here
FLASK_ENV=production
API_TOKEN=your-key-here

2. Install dependencies:
    ```shell
    python -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```
3. Install Tesseract (MacOS)
    ```
    brew install tesseract 
    ```
    For other OS refer https://tesseract-ocr.github.io/tessdoc/Installation.html

3. Run the Flask app:
    ```shell
    gunicorn -w 4 -b 0.0.0.0:8000 wsgi:app
    ```

4. Run tests:
   ```shell
    pytest
    ```

5. Navigate to http://localhost:8000/apidocs/  to use the API

6. Click on Authorize button and enter the API_TOKEN in this way:
    ```
    Bearer your-api-token
    ```

7. Use the API to upload a file and classify it


Running on Docker

1. Install Docker https://www.docker.com/get-started/
2. Open Docker Desktop / Start Docker Engine
3. Clone the repository:
    ```shell
    git clone <repository_url>
    cd join-the-seige
    ```
4. Add the following variables to a .env file:

OPENAI_API_KEY=your-key-here
FLASK_ENV=production
API_TOKEN=your-key-here

5. Build the Docker container
    ```
    docker build -t flask-classifier 
    ```
6. Run Docker Container
   ```
   docker run --env-file .env -p 8000:8000 flask-classifier
   ```