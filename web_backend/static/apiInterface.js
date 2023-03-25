// the file with all the requests to the backend API
// TODO: based on a domain
const API_URL = 'http://localhost:5000/transcribe';

async function transcribeBlob(blob) {
    // make a POST request to API_URL with the blob in webm as the contents
    let data = new FormData();
    data.append('chunk', blob);
    const request = new Request(API_URL, {
        method: 'POST',
        body: blob,
    });
    const response = await fetch(request);
    return response;
}

export default transcribeBlob;