class Utterance {
    utterance;
    timestamp;
    sessionId;
    tokenizedLen;
    seq;

    constructor(receivedJsonStr) {
        console.log("receivedJsonStr: " + receivedJsonStr);
        const receivedJson = JSON.parse(receivedJsonStr);
        this.timestamp = receivedJson.timestamp;
        this.utterance = receivedJson.utterance;
        this.sessionId = receivedJson.session_id;
        this.tokenizedLen = receivedJson.token_count;
        this.seq = receivedJson.seq;
    }
};

module.exports = { Utterance };