from flask import Flask, jsonify, request, redirect, url_for, render_template
import datetime
import logging
import redis
import requests
import os
import uuid

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Connect to Redis
redis_client = redis.Redis(host='localhost', port=6379, db=0, charset="utf-8", decode_responses=True)

# Set up environment variables for OLLMALA_URL and MODEL
OLLMALA_URL = os.getenv('OLLMALA_URL') or "http://localhost:11434"
MODEL = os.getenv('MODEL') or "granite3-dense"
SUMMARIZE_PROMPT = "The following is a meeting transcript. Write in Markdown format a bulleted list of all the points of discusion during the meeting. Do not skip any themes of discussion. \n\n Here is the meeting transcript: \n\n"

# Define the app
app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    """
    Handles incoming requests to the main page and processes them accordingly.

    Returns:
        If a POST request is made, it will return the response from the create_transcript endpoint.
        If a GET request is made, it will render the index.html template.
    """
    if request.method == 'POST':
        file = request.files['transcript']
        try:
            response = requests.post(url_for('create_transcript', _external=True), files={'transcript': file})
            if response.status_code == 200:
                transcript_id = response.json()['id']
            else:
                return "Error uploading transcript", 500
        except Exception as e:
            logger.error(f"Error uploading transcript: {e}")

    transcripts = list_transcripts().json

    return render_template('index.html', transcripts=transcripts)

def get_file_contents(file, transcript_id):
    """
    Reads the contents of a file and returns it as a string.

    Args:
        file (requests.Response): The file object containing the transcript.
        transcript_id (str): The unique identifier for the transcript.

    Returns:
        str: The contents of the file as a string.
    """
    file_location = transcript_id + "-transcript.txt"
    file.save(file_location)

    with open(file_location) as f:
        file_contents = f.read()
        return file_contents

@app.route('/transcripts', methods=['POST'])
def create_transcript():
    """
    Creates a new transcript and stores it in Redis.

    Returns:
        If successful, returns the unique identifier for the newly created transcript.
        If an error occurs, returns a 500 status code.
    """
    logging.info("Creating new transcript")
    transcript_id = str(uuid.uuid4())

    try:
        file_contents = get_file_contents(request.files['transcript'], transcript_id)
        summary = summarize(file_contents)
        transcript_entry = {
            'transcript': file_contents,
            'summary': summary,
            'date_created': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'id': transcript_id
        }
        redis_client.hset(name=transcript_id, mapping=transcript_entry)
        logger.info(f"Created new transcript with id: {transcript_id}")
        return jsonify({'message': 'Transcript created', 'id': transcript_id})
    except Exception as e:
        logger.error(f"Error creating transcript: {e}")
        return "Error creating transcript", 500

def summarize(file_content: str):
    """
    Summarizes the contents of a file using the OLLMALA API.

    Args:
        file_content (str): The contents of the file to be summarized.

    Returns:
        str: The summary of the file as a string.
    """
    try:
        response = requests.post(OLLMALA_URL + "/api/generate", json={
            "model": MODEL,
            "prompt": SUMMARIZE_PROMPT + file_content,
            "stream": False
        })
        data = response.json()
        return data["response"]

    except Exception as e:
        logger.error(f"Error summarizing transcript: {e}")
        return ""

@app.route('/transcripts', methods=['GET'])
def list_transcripts():
    """
    Lists all existing transcripts. 
    Returns:
        If successful, returns a JSON object containing the list of transcripts.
        If an error occurs, returns a 500 status code.
    """
    keys = redis_client.keys("*")
    transcripts = []
    for key in keys:
        info = redis_client.hgetall(key)
        date_created = info['date_created']
        transcripts.append({'id': str(key), 'date_created': str(date_created)})
    return jsonify(transcripts)


@app.route('/transcripts/<transcript_id>', methods=['GET'])
def get_transcript(transcript_id):
    """
    Gets a specific transcript by ID.
    """
    if not redis_client.exists(transcript_id):
        return jsonify({'message': 'Transcript not found'}), 404 
    transcript = redis_client.hgetall(transcript_id)
    print(transcript)
    summary_text = transcript['summary']

    return jsonify({**transcript, 'summary': summary_text})


@app.route('/transcripts/<transcript_id>', methods=['PUT'])
def update_transcript(transcript_id):
    """
    Updates the contents of an existing transcript in Redis.

    Returns:
        If successful, returns a 200 status code.
        If an error occurs, returns a 500 status code.
    """
    if not redis_client.exists(transcript_id):
        message = "Transcript not found"
        logger.error(message)
        return message, 404

    file = request.files['transcript']
    try:
        summary = summarize(get_file_contents(file, transcript_id))
        response = requests.post(OLLMALA_URL + "/api/generate", json={
            "model": MODEL,
            "prompt": f"{SUMMARIZE_PROMPT} {summary}",
            "stream": False
        })
        data = response.json()
        transcript_entry = {
            'transcript': summary,
            'date_updated': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'id': transcript_id
        }
        redis_client.hset(name=transcript_id, mapping=transcript_entry)
        return jsonify({'message': 'Transcript updated'})
    except Exception as e:
        logger.error(f"Error updating transcript: {e}")
        return "Error updating transcript", 500

@app.route('/transcripts/<transcript_id>', methods=['DELETE'])
def delete_transcript(transcript_id):
    """
    Deletes an existing transcript from Redis.

    Returns:
        If successful, returns a 200 status code.
        If an error occurs, returns a 500 status code.
    """
    if not redis_client.exists(transcript_id):
        return "Transcript not found", 404

    redis_client.delete(transcript_id)
    return jsonify({'message': 'Transcript deleted'})

if __name__ == '__main__':
    # Run the app in debug mode
    app.run(debug=True, port=5000)

