// the file with all the requests to the backend API
// TODO: based on a domain
const API_URL = 'http://localhost:7777/transcribe';

async function transcribeBlob(blob, callback) {
    // make a POST request to API_URL with the blob in webm as the contents
    let data = new FormData();
    data.append('chunk', blob);
    const request = new Request(API_URL, {
        method: 'POST',
        body: blob,
    });
    const response = await fetch(request);
    const transcriptData = await response.json();
    callback(transcriptData);
}

export default transcribeBlob;