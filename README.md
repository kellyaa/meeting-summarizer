Here is an overview of how the Meeting Transcript Manager can be used to summarize meeting transcripts using AI:

1. Install required packages with pip:
    ```bash
    pip install -r requirements.txt
    ```

2. Run the Flask server:
    ```bash
    export FLASK_APP=api/api.py
    flask run
    ```

3. Access the application in your browser at http://localhost:5000/.

4. Click "Choose file" and select a meeting transcript file to upload.

5. The uploaded transcript will be processed and summarized, and the summary will be displayed below the transcript.

6. To view or edit the full transcript, click on the "Read Full Transcript..." link in the summary.

7. To delete a transcript, click on the "Delete" button next to the transcript's timestamp.

8. To update an existing transcript, click on the "Choose file" button and select a new transcript file. Then click "Update".

9. The application will automatically summarize the new transcript and display it below the updated transcript.

The API endpoints of the Meeting Transcript Manager include:
- GET /transcripts: Returns a list of all available meeting transcripts with their creation timestamps.
- GET /transcripts/{transcript_id}: Returns the full details of a specific transcript, including the original file, creation timestamp, and summary.
- DELETE /transcripts/{transcript_id}: Deletes a specific transcript.
- PUT /transcripts/{transcript_id}: Updates a specific transcript with a new file. The updated transcript will be summarized and displayed below.

To run tests for this application, you can use the following commands:
```bash
pip install -r test_requirements.txt
pytest
```