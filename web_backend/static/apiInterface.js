// TODO: fix by passing it from the server
function getSessionId() {
    let path = window.location.pathname;
    var name = path.match(/([^\/]*)\/*$/)[1];
    return name;
}

function getTranscriptionApiURL(sessionId) {
    // TODO: fix by passing values from the server?
    return window.location.origin + "/transcribe/" + sessionId
}

async function transcribeBlob(blob, startTime, author, callback) {
    // make a POST request to API_URL with the blob in webm as the contents
    let data = new FormData();
    let sessionId = getSessionId();
    data.append('chunk', blob);
    data.append('author', author);
    data.append('startTime', startTime);
    let api_url = getTranscriptionApiURL(sessionId);
    const request = new Request(api_url, {
        method: 'POST',
        body: data,
        headers: new Headers({
            'Content-Type': 'multipart/form-data'
        })
    });
    const response = await fetch(request);
    const transcriptData = await response.json();
    callback(transcriptData, author, startTime);
}

export default transcribeBlob;