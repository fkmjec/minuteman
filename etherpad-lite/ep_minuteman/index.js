const AttributePool = require('ep_etherpad-lite/static/js/AttributePool');
const Changeset = require('ep_etherpad-lite/static/js/Changeset');
const padManager = require('ep_etherpad-lite/node/db/PadManager');
const Pad = require('ep_etherpad-lite/node/db/Pad');
const padMessageHandler = require('ep_etherpad-lite/node/handler/PadMessageHandler');
const readOnlyManager = require('ep_etherpad-lite/node/db/ReadOnlyManager.js');
const apiUtils = require('./ApiUtils');
const { Utterance } = require('./Utterance');
const { SummaryStore } = require('./SummaryStore');
const ChangesetUtils = require('./ChangesetUtils');
const TranscriptUtils = require('./TranscriptUtils');
const logger = require('ep_etherpad-lite/node_modules/log4js').getLogger('ep_etherpad-lite');
const amqplib = require('amqplib');

const TRANSCRIPT_QUEUE = 'transcript_queue';
const SUMMARY_INPUT_QUEUE = 'summary_input_queue';
const RABBITMQ_ADDR = 'amqp://rabbitmq';
MAX_RABBITMQ_RETRIES = 20;

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

exports.collectContentPre = function(hook, context, cb){
    const summary = /(?:^| )(s-[A-Za-z0-9]*)/.exec(context.cls);
    if (summary) {
        context.cc.doAttrib(context.state, `summary::${summary[1]}`);
    }
    cb();
}

async function addUtteranceToPad(utterance) {
    let sessionId = utterance.sessionId;
    sessionId = (await readOnlyManager.getIds(apiUtils.sanitizePadId(sessionId))).padId;
    const trscPadId = sessionId + ".trsc";
    const trscPad = await padManager.getPad(trscPadId);
    const appendChs = ChangesetUtils.getUtteranceAppendChs(trscPad, utterance);
    await trscPad.appendRevision(appendChs);
    padMessageHandler.updatePadClients(trscPad);
}

async function addSummaryToPad(sessionId, summarySeq, text) {
    sessionId = (await readOnlyManager.getIds(apiUtils.sanitizePadId(sessionId))).padId;
    const summPadId = sessionId + ".summ";
    const summPad = await padManager.getPad(summPadId);
    await summPad.appendText(`${summarySeq}: ${text}\n`);
    padMessageHandler.updatePadClients(summPad);
}

async function sendChunkToSummarize(sessionId, summarySeq, text) {
    const chunk = {
        sessionId: sessionId,
        summarySeq: summarySeq,
        text: text
    };
    const channel = await rabbitMQConnection.createChannel();
    await channel.assertQueue(SUMMARY_INPUT_QUEUE);
    await channel.sendToQueue(SUMMARY_INPUT_QUEUE, Buffer.from(JSON.stringify(chunk)));
    channel.close();
}

async function appendTranscript(utterance) {
    let sessionId = utterance.sessionId;
    sessionId = (await readOnlyManager.getIds(apiUtils.sanitizePadId(sessionId))).padId;
    const trscPadId = sessionId + ".trsc";
    const trscPad = await padManager.getPad(trscPadId);
    // create the changeset together with the summary attribute (beware, pool must be passed too)
    // append a newline as this cannot be done in the changeset
    const trscChunk = summaryStore.appendUtterance(utterance);
    await addUtteranceToPad(utterance);
    if (trscChunk) {
        summaryStore.addSummary(utterance.sessionId, trscChunk.seq, trscChunk);
        addSummaryToPad(sessionId, trscChunk.seq, "Summarization in progress");
        const trscText = TranscriptUtils.getTrscSegment(trscPad, trscChunk.start, trscChunk.end);
        sendChunkToSummarize(sessionId, trscChunk.seq, trscText);
    }
}

async function handleTranscriptChange(trscObj) {
    // TODO
    // rabbitMQConnection.sendToQueue(SUMMARY_INPUT_QUEUE, JSON.stringify(trscObj));
}

async function connectToRabbitMQ() {
    let retries = 0;
    console.log("Connecting to rabbitmq server");
    while (true) {
        try {
            let connection = await amqplib.connect(RABBITMQ_ADDR);
            let channel = await connection.createChannel();
            await channel.assertQueue(TRANSCRIPT_QUEUE);
            channel.consume(TRANSCRIPT_QUEUE, (msg) => {
                const trscObj = new Utterance(msg.content);
                appendTranscript(trscObj);
            });
            await channel.assertQueue(SUMMARY_INPUT_QUEUE);
            console.log("Successfully connected to rabbitmq")
            return connection;
        } catch (err) {
            console.error(err);
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
    cb();
}

exports.padUpdate = function(hook, context, cb) {
    // TODO: give info to the minuteman Python API that it should update the summary if the pad is a transcript pad.
    // TODO: how to distinguish summary and transcript pads?
    // only call api if it was a human user who edited the document
    logger.info("padUpdate called!");
    cb(undefined);
}

exports.getLineHTMLForExport = function (hook, context) {
    var header = _analyzeLine(context.attribLine, context.apool);
    logger.info(header);
    if (header) {
        context.lineContent = "<span class=\"summary " + header + "\">" + context.lineContent + "</span>";
    }
    return context.lineContent;
}
