class Utterance {
    author;
    utterance;
    timestamp;
    sessionId;

    constructor(receivedJsonStr) {
        console.log("receivedJsonStr: " + receivedJsonStr);
        const receivedJson = JSON.parse(receivedJsonStr);
        this.author = receivedJson.author;
        this.timestamp = receivedJson.timestamp;
        this.utterance = receivedJson.utterance;
        this.sessionId = receivedJson.session_id;
    }
};

module.exports = { Utterance };