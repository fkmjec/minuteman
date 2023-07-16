const AttributePool = require('ep_etherpad-lite/static/js/AttributePool');
const Changeset = require('ep_etherpad-lite/static/js/Changeset');
const padManager = require('ep_etherpad-lite/node/db/PadManager');
const Pad = require('ep_etherpad-lite/node/db/Pad');
const padMessageHandler = require('ep_etherpad-lite/node/handler/PadMessageHandler');
const readOnlyManager = require('ep_etherpad-lite/node/db/ReadOnlyManager.js');
const apiUtils = require('./ApiUtils');
const { Utterance } = require('./Utterance');
const { SummaryStore } = require('./SummaryStore');
const SummaryUtils = require('./SummaryUtils');
const ChangesetUtils = require('./ChangesetUtils');
const TranscriptUtils = require('./TranscriptUtils');
const logger = require('ep_etherpad-lite/node_modules/log4js').getLogger('ep_etherpad-lite');
const amqplib = require('amqplib');
const express = require('express');
const { Formidable } = require('formidable');

const TRANSCRIPT_QUEUE = 'transcript_queue';
const SUMMARY_INPUT_QUEUE = 'summary_input_queue';
const SUMMARY_RESULT_QUEUE = 'summary_result_queue';
const RABBITMQ_ADDR = 'amqp://rabbitmq';
const MAX_RABBITMQ_RETRIES = 20;
const SUMMARY_IN_PROGRESS = "Summarization in progress";

const summaryStore = new SummaryStore();
let rabbitMQConnection = null;

init();
  
function sleep(ms) {
    return new Promise((resolve) => {
        setTimeout(resolve, ms);
    });
}

exports.padCreate = function(hook, context, cb){
    const apool = new AttributePool();
    const builder = Changeset.builder(1, apool);
    context.pad.setText("");
    cb(undefined);
}

async function addUtteranceToPad(trscPad, utterance, isDebug) {
    const appendChs = ChangesetUtils.getUtteranceAppendChs(trscPad, utterance, isDebug);
    await trscPad.appendRevision(appendChs);
    padMessageHandler.updatePadClients(trscPad);
}

async function addSummaryToPad(sessionId, summarySeq, text) {
    sessionId = (await readOnlyManager.getIds(apiUtils.sanitizePadId(sessionId))).padId;
    const summPadId = sessionId + ".summ";
    const summPad = await padManager.getPad(summPadId);
    const appendChs = ChangesetUtils.getSummaryAppendChs(summPad, summarySeq, text + "\n");
    await summPad.appendRevision(appendChs);
    padMessageHandler.updatePadClients(summPad);
}

async function updateSummaryInPad(sessionId, summarySeq, text) {
    sessionId = (await readOnlyManager.getIds(apiUtils.sanitizePadId(sessionId))).padId;
    const summPadId = sessionId + ".summ";
    const summPad = await padManager.getPad(summPadId);
    const updateChs = ChangesetUtils.getSummaryUpdateChs(summPad, summarySeq, text);
    if (!updateChs) {
        return;
    }
    await summPad.appendRevision(updateChs);
    padMessageHandler.updatePadClients(summPad);
}

async function sendChunkToSummarize(sessionId, summarySeq, text, user_edit = false) {
    const model = summaryStore.sessions[sessionId].model;
    const chunk = {
        model: model,
        session_id: sessionId,
        summary_seq: summarySeq,
        text: text,
        user_edit: user_edit
    };
    const channel = await rabbitMQConnection.createChannel();
    await channel.assertQueue(SUMMARY_INPUT_QUEUE);
    await channel.sendToQueue(SUMMARY_INPUT_QUEUE, Buffer.from(JSON.stringify(chunk)));
    channel.close();
}

async function appendTranscript(utterance) {
    let sessionId = utterance.sessionId;
    const isDebug = summaryStore.sessions[sessionId] && summaryStore.sessions[sessionId].debug;
    sessionId = (await readOnlyManager.getIds(apiUtils.sanitizePadId(sessionId))).padId;
    const trscPadId = sessionId + ".trsc";
    const trscPad = await padManager.getPad(trscPadId);
    // create the changeset together with the summary attribute (beware, pool must be passed too)
    // append a newline as this cannot be done in the changeset
    const trscChunk = summaryStore.appendUtterance(utterance, isDebug);
    await addUtteranceToPad(trscPad, utterance, isDebug);
    if (trscChunk) {
        // wait for the summary to be present in the pad so that it can be then asynchronously replaced
        let summaryContent = `${trscChunk.seq}: ${SUMMARY_IN_PROGRESS}`;
        if (isDebug) {
            summaryContent = `${trscChunk.seq} ${trscChunk.start}->${trscChunk.end} || ${SUMMARY_IN_PROGRESS}`;
        }
        await addSummaryToPad(sessionId, trscChunk.seq, summaryContent);
        const trscText = TranscriptUtils.getTrscSegment(trscPad, trscChunk.start, trscChunk.end, isDebug);
        summaryStore.addSummary(utterance.sessionId, trscChunk, summaryContent);
        await sendChunkToSummarize(sessionId, trscChunk.seq, trscText);
    }
}

async function connectToRabbitMQ() {
    let retries = 0;
    console.log("Connecting to rabbitmq server");
    while (true) {
        try {
            let connection = await amqplib.connect(RABBITMQ_ADDR);
            let channel = await connection.createChannel();
            await channel.assertQueue(TRANSCRIPT_QUEUE);
            await channel.assertQueue(SUMMARY_INPUT_QUEUE);
            await channel.assertQueue(SUMMARY_RESULT_QUEUE);
            channel.consume(TRANSCRIPT_QUEUE, (msg) => {
                const trscObj = new Utterance(msg.content);
                appendTranscript(trscObj);
            }, { noAck: true });

            channel.consume(SUMMARY_RESULT_QUEUE, (msg) => {
                const summaryObj = JSON.parse(msg.content);
                const isDebug = summaryStore.sessions[summaryObj.session_id] && summaryStore.sessions[summaryObj.session_id].debug;
                let summaryContent = summaryObj.summary_text;
                if (isDebug) {
                    // TODO: rewrite this mess
                    const summary = summaryStore.sessions[summaryObj.session_id].summaries[summaryObj.summary_seq];
                    const start = summary.trscStart;
                    const end = summary.trscEnd;
                    const seq = summary.seq;
                    summaryContent = ChangesetUtils.prependSummMetadata(summaryContent, seq, start, end);
                }

                summaryStore.updateSummaryContent(summaryObj.session_id, summaryObj.summary_seq, summaryObj.summary_text);
                updateSummaryInPad(summaryObj.session_id, summaryObj.summary_seq, summaryContent);
            }, { noAck: true });
            console.log("Successfully connected to rabbitmq")
            return connection;
        } catch (err) {
            console.error(err.message);
            retries += 1;
            if (retries > MAX_RABBITMQ_RETRIES) {
                console.error("Failed to connect to rabbitmq server");
                throw err;
            }
            await sleep(1000);
        }
    }
}

async function init() {
    // initialize the global connection object for usage
    rabbitMQConnection = await connectToRabbitMQ();
}

// Add api hooks for our summary api extensions
exports.expressCreateServer = function(hook, args, cb) {
    logger.info("Express create server called!");
    args.app.use(express.json());
    args.app.post("/api/createSumm", async (req, res) => {
        const fields = await new Promise((resolve, reject) => {
            new Formidable().parse(req, (err, fields) => err ? reject(err) : resolve(fields));
        });
        const sessionId = fields.session_id;
        const start = fields.start;
        const end = fields.end;
        const pad = await padManager.getPad(sessionId + ".trsc");
        const isDebug = summaryStore.sessions[sessionId] && summaryStore.sessions[sessionId].debug;
        const source = TranscriptUtils.getTrscSegment(pad, start, end, isDebug);
        let summaryInProgressText = `${SUMMARY_IN_PROGRESS}`
        const seq = summaryStore.addUserSelectedSummary(sessionId, start, end, source, summaryInProgressText);
        await addSummaryToPad(sessionId, seq, summaryInProgressText);
        await sendChunkToSummarize(sessionId, seq, source, false);
        res.status(200).send("OK");
    });

    args.app.post("/api/setChunkLen", async (req, res) => {
        const fields = await new Promise((resolve, reject) => {
            new Formidable().parse(req, (err, fields) => err ? reject(err) : resolve(fields));
        });
        const sessionId = fields.session_id;
        const chunkLen = fields.chunk_len;
        if (chunkLen > 0) {
            summaryStore.setChunkLen(sessionId, chunkLen);
            res.status(200).send("OK");
        } else {
            res.status(400).send("Invalid chunk length");
        }
    });

    args.app.post("/api/setSummModel", async (req, res) => {
        const fields = await new Promise((resolve, reject) => {
            new Formidable().parse(req, (err, fields) => err ? reject(err) : resolve(fields));
        });
        const sessionId = fields.session_id;
        const summModel = fields.summ_model;
        summaryStore.setModel(sessionId, summModel);
        res.status(200).send("OK");
    });


    args.app.post("/api/setConnectionStatus", async (req, res) => {
        const fields = await new Promise((resolve, reject) => {
            new Formidable().parse(req, (err, fields) => err ? reject(err) : resolve(fields));
        });
        const sessionId = fields.session_id;
        const chunkLen = fields.chunk_len;
        if (chunkLen > 0) {
            summaryStore.setChunkLen(sessionId, chunkLen);
            res.status(200).send("OK");
        } else {
            res.status(400).send("Invalid chunk length");
        }
    });


    args.app.post("/api/createSessionObject", async (req, res) => {
        let parsed = null;
        let config = null
        try {
            parsed = req.body;
            config = req.body.config;
        } catch (err) {
            logger.error(err.message);
            res.status(400).send("Invalid JSON");
            return;
        }
        const sessionId = parsed.session_id;
        const debug = config.debug;
        console.info(`Creating session object for session ${sessionId} with debug ${debug}`);
        summaryStore.createSession(sessionId, config);
        res.status(200).send("OK");
    });

    args.app.get("/api/sessionConfig", async (req, res) => {
        const sessionId = req.query.session_id;
        if (!summaryStore.sessions[sessionId]) {
            res.status(400).send("Session does not exist");
            return;
        }
        const config = summaryStore.getSessionConfig(sessionId);
        res.status(200).send(config);
    });

    cb();
}

exports.padUpdate = function(hook, context, cb) {
    logger.info("padUpdate called!");
    // edited by the plugin, no action needed
    if (!context.author) {
        cb();
        return;
    }
    if (context.pad.id.slice(-5) === ".trsc") {
        const sessionId = context.pad.id.slice(0, -5); 
        const toSummarize = summaryStore.updateTrsc(sessionId, context.pad);
        for (const summary of toSummarize) {
            sendChunkToSummarize(sessionId, summary.seq, summary.source, true);
        }
    } else if (context.pad.id.slice(-5) === ".summ") {
        const sessionId = context.pad.id.slice(0, -5);
        summaryStore.freezeSummaries(sessionId, context.pad);
    }
    cb();
}
