const TranscriptUtils = require("./TranscriptUtils");
const SummaryUtils = require("./SummaryUtils");

// TODO: move this to config somewhere
MAX_WORD_LEN = 512;

class TranscriptChunk {
    constructor(text, len, start, end, seq) {
        this.text = text;
        this.start = start;
        this.end = end;
        this.len = len;
        this.seq = seq;
    }
}

class TranscriptChunker {
    constructor(maxWordLen) {
        this.currentChunk = "";
        this.started = false;
        this.currentLen = 0;
        this.currentStart = 0;
        this.currentEnd = 0;
        this.currentSummSeq = 0;
        this.maxWordLen = maxWordLen;
    }

    append(utterance) {
        const utteranceWordLen = utterance.utterance.split(/\s+/).length;
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
    constructor(seq, trscStart, trscEnd, source, summary) {
        this.seq = seq;
        this.trscStart = trscStart;
        this.trscEnd = trscEnd;
        this.summary = summary;
        this.source = source;
        this.frozen = false;
    }

    freeze() {
        this.frozen = true;
    }
}

class SummarySession {
    /**
     * @param {*} debug whether the session is in debug mode or not
     */
    constructor(debug) {
        // TODO: this will need a persistent backend, but it is not necessary for the prototype
        this.summaries = {};
        this.currentUserSummSeq = 1000;
        this.debug = debug
        this.summaryModel = "bart";
        this.connected = false;
    }

    /**
     * Add a summary to the session
     * @param {*} seq the sequence number of the summary
     * @param {*} start the start line seq in the transcript
     * @param {*} end the end line seq in the transcript
     * @param {*} source the source summarized transcript
     * @param {*} summary the generated summary
     */
    addSummary(seq, start, end, source, summary) {
        const summaryObj = new Summary(seq, start, end, source, summary);
        this.summaries[seq] = summaryObj;
    }

    freeze(seq) {
        this.summaries[seq].freeze();
    }

    isFrozen(seq) {
        return this.summaries[seq].frozen;
    }
}

class SummaryStore {
    constructor() {
        this.sessions = {};
        this.startedChunks = {};
    }

    /**
     * Creates a new session
     * @param {*} sessionId the id of the session
     * @param {*} debug whether the session is in debug mode or not
     */
    createSession(sessionId, config) {
        this.sessions[sessionId] = new SummarySession(config.debug);
        this.startedChunks[sessionId] = new TranscriptChunker(config.chunk_len);
        this.sessions[sessionId].connected = config.connected;
        this.sessions[sessionId].model = config.summ_model_id;
    }

    /**
     * Adds an utterance to the corresponding session.
     * @param {*} utterance the utterance to add
     * @returns a transcript chunk if the utterance caused a chunk to be completed, null otherwise
     */
    appendUtterance(utterance) {
        let sessionId = utterance.sessionId.split("_")[0];
        if (!this.startedChunks[sessionId]) {
            console.error(`[appendUtterance] Session ${sessionId} not found!, ${JSON.stringify(this.sessions, null, 2)}`);
            return;
        }
        const possibleChunk = this.startedChunks[sessionId].append(utterance);
        return possibleChunk;
    }

    setChunkLen(sessionId, len) {
        sessionId = sessionId.split("_")[0];
        if (!this.sessions[sessionId]) {
            console.error(`[setChunkLen] Session ${sessionId} not found!, ${JSON.stringify(this.sessions, null, 2)}`);
            return;
        }

        this.startedChunks[sessionId].maxWordLen = len;
    }

    setModel(sessionId, summModel) {
        sessionId = sessionId.split("_")[0];
        if (!this.startedChunks[sessionId]) {
            console.error(`[setModel] Session ${sessionId} not found!, ${JSON.stringify(this.sessions, null, 2)}`);
            return;
        }
        this.sessions[sessionId].model = summModel;
    }

    /**
     * Adds a summary to the store
     * @param {*} sessionId the session in which the summary was created
     * @param {*} trscChunk the transcript chunk that contains the input transcript segment
     * @param {*} summaryContent the content of the summary
     */
    addSummary(sessionId, trscChunk, summaryContent) {
        sessionId = sessionId.split("_")[0];
        if (!this.sessions[sessionId]) {
            console.error(`[addSummary] Session ${sessionId} not found!, ${JSON.stringify(this.sessions, null, 2)}`);
            return;
        }
        const summarySeq = trscChunk.seq;
        this.sessions[sessionId].addSummary(summarySeq, trscChunk.start, trscChunk.end, trscChunk.text, summaryContent);
    }

    addUserSelectedSummary(sessionId, startSeq, endSeq, summarySource, summaryContent) {
        sessionId = sessionId.split("_")[0];
        if (!this.sessions[sessionId]) {
            console.error(`[addUserSelectedSummary] Session ${sessionId} not found!, ${JSON.stringify(this.sessions, null, 2)}`);
            return;
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
    updateSummaryContent(sessionId, summarySeq, summaryContent) {
        sessionId = sessionId.split("_")[0];
        if (!this.sessions[sessionId]) {
            console.error(`[updateSummaryContent] Session ${sessionId} not found!, ${JSON.stringify(this.sessions, null, 2)}`);
            return;
        }
        if (!this.sessions[sessionId].summaries[summarySeq]) {
            console.error(`intended to update summary ${summarySeq} but it does not exist`);
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
    updateTrsc(sessionId, pad) {
        sessionId = sessionId.split("_")[0];
        if (!this.sessions[sessionId]) {
            console.error(`[updateTrsc] Session ${sessionId} not found!, ${JSON.stringify(this.sessions, null, 2)}`);
            return;
        }
        const session = this.sessions[sessionId];
        const summaries = session.summaries;
        const summariesToUpdate = [];
        for (const [summarySeq, summaryObj] of Object.entries(summaries)) {
            const isDebug = session.debug;
            const newText = TranscriptUtils.getTrscSegment(pad, summaryObj.trscStart, summaryObj.trscEnd, isDebug);
            if (newText !== summaryObj.source && !session.isFrozen(summarySeq)) {
                summaryObj.source = newText;
                summariesToUpdate.push(summaryObj);
            }
        }
        return summariesToUpdate;
    }

    /**
     * takes an updated summary pad and checks which summaries were edited by the user.
     * Those are then frozen so that they are not overridden by automatic updates.
     * @param {*} sessionId
     * @param {*} pad
     */
    freezeSummaries(sessionId, pad) {
        sessionId = sessionId.split("_")[0];
        if (!this.sessions[sessionId]) {
            console.error(`[freezeSummaries] Session ${sessionId} not found!, ${JSON.stringify(this.sessions, null, 2)}`);
            return;
        }
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
    freeze(sessionId, summarySeq) {
        sessionId = sessionId.split("_")[0];
        if (!this.sessions[sessionId]) {
            console.error(`[freeze] Session ${sessionId} not found!, ${JSON.stringify(this.sessions, null, 2)}`);
            return;
        }
        this.sessions[sessionId].freeze(summarySeq);
    }

    /**
     * Gets the session configuration for synchronization between clients
     * @param {*} sessionId
     * @returns the session configuration
     */
    getSessionConfig(sessionId) {
        sessionId = sessionId.split("_")[0];
        const session = this.sessions[sessionId];
        return {
            debug: session.debug,
            chunkLen: this.startedChunks[sessionId].maxWordLen,
            summModel: session.model,
            connected: session.connected
        }
    }
}

module.exports = { SummaryStore };