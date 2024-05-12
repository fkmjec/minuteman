class Utterance {
    utterance;
    timestamp;
    sessionId;
    seq;

    constructor(receivedJsonStr) {
        const receivedJson = JSON.parse(receivedJsonStr)[0];
        this.timestamp = receivedJson.timestamp;
        this.utterance = receivedJson.utterance;
        this.sessionId = receivedJson.session_id;
        this.seq = receivedJson.seq;
    }
};

module.exports = { Utterance };