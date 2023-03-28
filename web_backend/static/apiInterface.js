// TODO: based on a domain
function getTranscriptionApiURL() {
    // TODO: fix by passing values from the server
    return window.location.origin + "/transcribe"
}

async function transcribeBlob(blob, startTime, author, callback) {
    // make a POST request to API_URL with the blob in webm as the contents
    let data = new FormData();
    data.append('chunk', blob);
    let api_url = getTranscriptionApiURL();
    const request = new Request(api_url, {
        method: 'POST',
        body: blob,
    });
    const response = await fetch(request);
    const transcriptData = await response.json();
    callback(transcriptData, author, startTime);
}

export default transcribeBlob;