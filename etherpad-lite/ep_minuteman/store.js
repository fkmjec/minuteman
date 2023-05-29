class TranscriptChunk {
    constructor () {
        this.content = "";
        this.len = 0;
    }

    append (utterance, tokenizedLen) {
        this.content += utterance + "\n";
        this.len += tokenizedLen;
    }
}

class Summary {
    constructor (id, content) {
        this.id = id;
        this.content = content;
        this.frozen = false;
    }

    freeze () {
        this.frozen = true;
    }
}

class Session {
    constructor () {
        // TODO: this will need a persistent backend, but it is not necessary for the prototype
        this.summaries = {};
        this.currentId = 0;
    }

    addSummary (id, summary) {
        const summaryObj = new Summary(id, content);
        this.summaries[summary.id] = summaryObj;
    }

    freeze (id) {
        this.summaries[id].freeze();
    }

    isFrozen (id) {
        return this.summaries[id].frozen;
    }
}

class SummaryStore {
    constructor () {
        this.sessions = {};
    }

    addSummary (sessionId, summaryId, content) {
        if (!this.sessions[sessionId]) {
            this.sessions[sessionId] = new Session();
        }
        this.sessions[sessionId].addSummary(summaryId, content);
    }

    freeze (sessionId, summaryId) {
        this.sessions[sessionId].freeze(summaryId);
    }

    isFrozen (sessionId, summaryId) {
        return this.sessions[sessionId].isFrozen(summaryId);
    }
}

exports = { SummaryStore, TranscriptChunk };