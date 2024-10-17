import pytest
from flask.testing import FlaskClient
from summarizer.api.api import app

@pytest.fixture
def client():
    with app.test_client() as c:
        yield c

def create_transcript(client):
    with open("example_file.txt", "w") as file:
        file.write("This is an example text.")
        file.close()

    with open("example_file.txt", "rb") as file:
        files = {"transcript": file}
        response = client.post("/transcripts", data=files)
        print(response.json)
        print(response.status_code)
        transcript_id = response.json["id"]

    response = client.get(f"/transcripts/{transcript_id}")
    if response.status_code == 200:
        return transcript_id
    else:
        return None


@pytest.fixture()
def transcript_id(client):
    return create_transcript(client)


def test_list_transcripts(client):
    response = client.get('/transcripts')
    assert response.status_code == 200
    assert isinstance(response.json, list)


def test_delete_transcript(client, transcript_id):
    response = client.delete('/transcripts/' + transcript_id)
    assert response.status_code == 200
    assert response.json == {'message': 'Transcript deleted'}


def test_update_transcript(client, transcript_id):
    with open("updated_file.txt", "w") as file:
        file.write("This is an updated example text.")
        file.close()

    with open("updated_file.txt", "rb") as file:
        files = {"transcript": file}
        response = client.put('/transcripts/' + transcript_id, data=files)
        assert response.status_code == 200
        assert response.json == {'message': 'Transcript updated'}
