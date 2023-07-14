// TODO: fix by passing it from the server
function getSessionId() {
    let path = window.location.pathname;
    var name = path.match(/([^\/]*)\/*$/)[1];
    return name;
}

function getTranscriptionApiURL(sessionId) {
    // TODO: fix by passing values from the server?
    return window.location.origin + "/minuting/" + sessionId + "/transcribe/"
}

function sendAudioData(audioData, startTime, author, recorderId) {
    let data = new FormData();
    let sessionId = getSessionId();
    data.append('author', author);
    data.append('timestamp', startTime.toISOString());
    data.append('recorder_id', recorderId);
    const blob = new Blob([audioData.data.buffer], { type: 'application/octet-stream' });
    data.append('chunk', blob);
    let api_url = getTranscriptionApiURL(sessionId);
    const request = new Request(api_url, {
        method: 'POST',
        body: data,
    });
    fetch(request);
}

function setChunkLen(chunkLen) {
    let data = new FormData();
    let sessionId = getSessionId();
    data.append('chunk_len', chunkLen);
    let apiUrl = window.location.origin + "/minuting/" + sessionId + "/set_chunk_len/";
    const request = new Request(apiUrl, {
        method: 'POST',
        body: data,
    });
    fetch(request);
}

async function getState() {
    let sessionId = getSessionId();
    let apiUrl = window.location.origin + "/minuting/" + sessionId + "/get_state/";
    const request = new Request(apiUrl, {
        method: 'GET',
    });
    const response = await fetch(request);
    const json = await response.json();
    if (response.status != 200) {
        throw new Error("Invalid response from the API while getting state");
    }
    return {config: json.config, model_selection: json.model_selection};
}

export default { sendAudioData, setChunkLen, getState };