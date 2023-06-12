const TranscriptUtils = require("./TranscriptUtils");
const SummaryUtils = require("./SummaryUtils");

// TODO: move this to config somewhere
MAX_TOKEN_LEN = 512;

class TranscriptChunk {
    constructor (text, len, start, end, seq) {
        this.text = text;
        this.start = start;
        this.end = end;
        this.len = len;
        this.seq = seq;
    }
}

class TranscriptChunker {
    constructor (maxWordLen) {
        this.currentChunk = "";
        this.started = false;
        this.currentLen = 0;
        this.currentStart = 0;
        this.currentEnd = 0;
        this.currentSummSeq = 0;
        this.maxWordLen = maxWordLen;
    }

    append (utterance) {
        const utteranceWordLen = utterance.split(/\s+/).length;
        if (this.currentLen + utteranceWordLen > this.maxWordLen) {
            const returnedChunk = new TranscriptChunk(
                this.currentChunk,
                this.currentLen,
                this.currentStart,
                this.currentEnd,
                this.currentSummSeq
            );
            this.currentSummSeq += 1;
            this.currentChunk = utterance.utterance;
            this.currentLen = utteranceWordLen;
            this.currentStart = utterance.seq;
            this.currentEnd = utterance.seq;
            return returnedChunk;
        } else {
            this.currentChunk += utterance.utterance;
            this.currentLen += utteranceWordLen;
            this.currentEnd = utterance.seq;
            return null;
        }
    }
}

class Summary {
    constructor (seq, trscStart, trscEnd, source, summary) {
        this.seq = seq;
        this.trscStart = trscStart;
        this.trscEnd = trscEnd;
        this.summary = summary;
        this.source = source;
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
        this.currentUserSummSeq = 1000;
    }

    /**
     * Add a summary to the session
     * @param {*} seq the sequence number of the summary
     * @param {*} start the start line seq in the trascript
     * @param {*} end the end line seq in the transcript
     * @param {*} source the source summarized transcript
     * @param {*} summary the generated summary
     */
    addSummary (seq, start, end, source, summary) {
        const summaryObj = new Summary(seq, start, end, source, summary);
        this.summaries[seq] = summaryObj;
    }

    freeze (seq) {
        this.summaries[seq].freeze();
    }

    isFrozen (seq) {
        return this.summaries[seq].frozen;
    }
}

class SummaryStore {
    constructor () {
        this.sessions = {};
        this.startedChunks = {};
    }

    /**
     * Adds an utterance to the corresponding session.
     * @param {*} utterance the utterance to add
     * @returns a transcript chunk if the utterance caused a chunk to be completed, null otherwise
     */
    appendUtterance(utterance) {
        if (!this.startedChunks[utterance.sessionId]) {
            this.startedChunks[utterance.sessionId] = new TranscriptChunker(MAX_TOKEN_LEN);
        }
        const possibleChunk = this.startedChunks[utterance.sessionId].append(utterance);
        return possibleChunk;
    }

    setChunkLen(sessionId, len) {
        if (!this.startedChunks[sessionId]) {
            this.startedChunks[sessionId] = new TranscriptChunker(len);
        }
        this.startedChunks[sessionId].maxWordLen = len;
    }

    /**
     * Adds a summary to the store
     * @param {*} sessionId the session in which the summary was created
     * @param {*} trscChunk the transcript chunk that contains the input transcript segment
     * @param {*} summaryContent the content of the summary
     */
    addSummary (sessionId, trscChunk, summaryContent) {
        if (!this.sessions[sessionId]) {
            this.sessions[sessionId] = new SummarySession();
        }
        const summarySeq = trscChunk.seq;
        this.sessions[sessionId].addSummary(summarySeq, trscChunk.start, trscChunk.end, trscChunk.text, summaryContent);
    }

    addUserSelectedSummary(sessionId, startSeq, endSeq, summarySource, summaryContent) {
        if (!this.sessions[sessionId]) {
            this.sessions[sessionId] = new SummarySession();
        }
        const summId = this.sessions[sessionId].currentUserSummSeq;
        this.sessions[sessionId].currentUserSummSeq += 1;
        this.sessions[sessionId].addSummary(summId, startSeq, endSeq, summarySource, summaryContent);
        return summId;
    }

    /** 
     * Updates the content of a summary. Usually called when a new response comes from the summarizer.
     * @param {*} sessionId the session in which the summary was created
     * @param {*} summarySeq the sequence number of the summary
     * @param {*} summaryContent the new content of the summary
     */
    updateSummaryContent (sessionId, summarySeq, summaryContent) {
        if (!this.sessions[sessionId]) {
            this.sessions[sessionId] = new SummarySession();
        }
        if (!this.sessions[sessionId].summaries[summarySeq]) {
            console.info(`intended to update summary ${summarySeq} but it does not exist`);
            return;
        }
        this.sessions[sessionId].summaries[summarySeq].summary = summaryContent;
    }

    /**
     * Check which segments of the transcript were modified and updates the summaries
     * @param {*} sessionId the session in which the transcript was updated 
     * @param {*} pad the pad that contains the transcript
     * @returns a list of summaries to update
     */
    updateTrsc (sessionId, pad) {
        if (!this.sessions[sessionId]) {
            this.sessions[sessionId] = new SummarySession();
        }
        const session = this.sessions[sessionId];
        const summaries = session.summaries;
        const summariesToUpdate = [];
        for (const [summarySeq, summaryObj] of Object.entries(summaries)) {
            const newText = TranscriptUtils.getTrscSegment(pad, summaryObj.trscStart, summaryObj.trscEnd);
            if (newText !== summaryObj.source && !session.isFrozen(summarySeq)) {
                // update the source so that it is not updated a second time if the transcript is updated again in a different place
                // FIXME: this is not ideal, if the request gets lost, it stops making sense.
                summaryObj.source = newText;
                summariesToUpdate.push(summaryObj);
            }
        }
        return summariesToUpdate;
    }

    /**
     * takes an updated summary pad and checks which summaries were edited by the user.
     * Those are then frozen so that they are not overriden by automatic updates.
     * @param {*} sessionId 
     * @param {*} pad 
     */
    freezeSummaries (sessionId, pad) {
        const summaries = SummaryUtils.getSummariesFromPad(pad);
        for (const [summarySeq, newSumm] of Object.entries(summaries)) {
            const oldSumm = this.sessions[sessionId].summaries[summarySeq].summary;
            if (oldSumm !== newSumm) {
                this.updateSummaryContent(sessionId, summarySeq, newSumm);
                this.freeze(sessionId, summarySeq);
            }
        }
    }

    /**
     * Freezes the summary from further automatic updates (because we do not want to override user input)
     * @param {*} sessionId 
     * @param {*} summarySeq 
     */
    freeze (sessionId, summarySeq) {
        this.sessions[sessionId].freeze(summarySeq);
    }
}

module.exports = { SummaryStore };