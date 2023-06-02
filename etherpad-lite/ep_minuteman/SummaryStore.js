// TODO: move this to config somewhere
MAX_TOKEN_LEN = 512;

class TranscriptChunk {
    constructor (text, tokenizedLen, start, end, seq) {
        this.text = text;
        this.start = start;
        this.end = end;
        this.tokenizedLen = tokenizedLen;
        this.seq = seq;
    }
}

class TranscriptChunker {
    constructor (maxTokenLen) {
        this.currentChunk = "";
        this.started = false;
        this.currentLen = 0;
        this.currentStart = 0;
        this.currentEnd = 0;
        this.currentSummSeq = 0;
        this.maxTokenLen = maxTokenLen;
    }

    append (utterance) {
        if (this.currentLen + utterance.tokenizedLen > this.maxTokenLen) {
            const returnedChunk = new TranscriptChunk(
                this.currentChunk,
                this.currentLen,
                this.currentStart,
                this.currentEnd,
                this.currentSummSeq
            );
            this.currentSummSeq += 1;
            this.currentChunk = utterance;
            this.currentLen = utterance.tokenizedLen;
            this.currentStart = utterance.seq;
            this.currentEnd = utterance.seq;
            return returnedChunk;
        } else {
            this.currentChunk += utterance.utterance;
            this.currentLen += utterance.tokenizedLen;
            this.currentEnd = utterance.seq;
            return null;
        }
    }
}

class Summary {
    constructor (id, trscStart, trscEnd, content) {
        this.id = id;
        this.trscStart = trscStart;
        this.trscEnd = trscEnd;
        this.content = content;
        this.frozen = false;
    }

    freeze () {
        this.frozen = true;
    }
}

class SummarySession {
    constructor () {
        // TODO: this will need a persistent backend, but it is not necessary for the prototype
        this.summaries = {};
        this.currentId = 0;
    }

    addSummary (id, summary) {
        const summaryObj = new Summary(id, summary);
        this.summaries[id] = summaryObj;
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
        this.startedChunks = {};
    }

    appendUtterance(utterance) {
        if (!this.startedChunks[utterance.sessionId]) {
            this.startedChunks[utterance.sessionId] = new TranscriptChunker(MAX_TOKEN_LEN);
        }
        const possibleChunk = this.startedChunks[utterance.sessionId].append(utterance);
        return possibleChunk;
    }

    addSummary (sessionId, summarySeq, content) {
        if (!this.sessions[sessionId]) {
            this.sessions[sessionId] = new SummarySession();
        }
        this.sessions[sessionId].addSummary(summarySeq, content);
    }

    freeze (sessionId, summarySeq) {
        this.sessions[sessionId].freeze(summarySeq);
    }

    isFrozen (sessionId, summarySeq) {
        return this.sessions[sessionId].isFrozen(summarySeq);
    }
}

module.exports = { SummaryStore };