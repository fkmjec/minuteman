const AttributePool = require('ep_etherpad-lite/static/js/AttributePool');
const Changeset = require('ep_etherpad-lite/static/js/Changeset');
const {Formidable} = require('formidable');
const padManager = require('ep_etherpad-lite/node/db/PadManager');
const Pad = require('ep_etherpad-lite/node/db/Pad');
const padMessageHandler = require('ep_etherpad-lite/node/handler/PadMessageHandler');
const readOnlyManager = require('ep_etherpad-lite/node/db/ReadOnlyManager.js');
const fetch = require('node-fetch');
const apiUtils = require('./apiUtils');
const logger = require('ep_etherpad-lite/node_modules/log4js').getLogger('ep_etherpad-lite'); 

// generate a changeset for a summary line. This includes saving the proper
// attributes. We presume the text has been cleaned before.
function getSummaryLineAppendChs(pad, newText, summaryId) {
    const oldText = Pad.cleanText(pad.text());
    const text = Pad.cleanText(newText);
    const attribs = [[ "summary", summaryId]];
    const changeset = Changeset.makeSplice(oldText, oldText.length, 0, text, attribs, pad.pool);
    return changeset;
}

function getSummaryLineChangeChs(pad, newText, summaryId, pool) {
    const atext = pad.atext;
    var opIter = Changeset.opIterator(pad.atext.attribs);
    // FIXME: is this needed?
    let oldText = Pad.cleanText(pad.text());
    const text = Pad.cleanText(newText);
    let charsBefore = 0;

    while (opIter.hasNext()) {
        // we can use the opIterator to get attributes for each line, but can we get where the revision starts and ends?
        // get line contents for iterator
        var op = opIter.next();
        header = Changeset.opAttributeValue(op, 'summary', pad.pool);
        if (header === summaryId) {
            let attribs = [[ "summary", summaryId]];
            // logger.info(f`chars before: ${op.charsBefore} chars for point${logger.chars}`);
            let changeset = Changeset.makeSplice(oldText, charsBefore, op.chars, text, attribs, pad.pool);
            changeset.app
            return changeset;
        } else {
            charsBefore += op.chars;
        }
    }
    throw new Error("Summary point not found!");
}

exports.padCreate = function(hook, context, cb){
    const apool = new AttributePool();
    const builder = Changeset.builder(1, apool);
    builder.insert('Hello World!');
    const changeset = builder.toString();
    logger.info("made changes, yaay");
    context.pad.setText("This works, thanks!");
    cb(undefined);
}

exports.collectContentPre = function(hook, context, cb){
    logger.info("Collect content pre called!");
    logger.info(context);
    logger.info(context.cls);
    const summary = /(?:^| )(s-[A-Za-z0-9]*)/.exec(context.cls);
    if (summary) {
        logger.info(summary);
        context.cc.doAttrib(context.state, `summary::${summary[1]}`);
    }
    cb();
}

// Add api hooks for our summary api extensions
exports.expressCreateServer = function(hook, args, cb) {
    logger.info("Express create server called!");
    args.app.post("/api/appendSumm", async (req, res) => {
        const fields = await new Promise((resolve, reject) => {
            new Formidable().parse(req, (err, fields) => err ? reject(err) : resolve(fields));
        });
        logger.info("appendSumm called!");

        if (!apiUtils.validateApiKey(fields, res)) return;
        // sanitize pad id before continuing
        const padIdReceived = (await readOnlyManager.getIds(apiUtils.sanitizePadId(fields.padID))).padId;
        let data;
        try {
            logger.info(fields);
            data = JSON.parse(fields.data);
        } catch (err) {
            logger.error(err);
            res.json({ code:1 , message: "data must be in JSON format"});
            return;
        }
        logger.info(padIdReceived);
        logger.info(data);
        const pad = await padManager.getPad(padIdReceived);
        
        // create the changeset together with the summary attribute (beware, pool must be passed too)
        // append a newline as this cannot be done in the changeset
        await pad.appendText("\n");
        const changeset = getSummaryLineAppendChs(pad, data.text, data.id);
        await pad.appendRevision(changeset);

        logger.info(pad);
        padMessageHandler.updatePadClients(pad);
        res.json({ code: 0, message: "Success!"});
    });

    args.app.get("/api/getSummPoints", async (req, res) => {
        const fields = req.query;

        logger.info(fields);

        if (!apiUtils.validateApiKey(fields, res)) return;
        // sanitize pad id before continuing
        // TODO: get padId from fields
        const padIdReceived = (await readOnlyManager.getIds(apiUtils.sanitizePadId(fields.padID))).padId;
        logger.info(padIdReceived);
        const pad = await padManager.getPad(padIdReceived);
        // TODO: go through all lines and get the ones where summary attributes are set
        

        res.json({ code: 0, message: "TODO!"});
    });

    args.app.post("/api/updateSumm", async (req, res) => {
        const fields = await new Promise((resolve, reject) => {
            new Formidable().parse(req, (err, fields) => err ? reject(err) : resolve(fields));
        });

        logger.info(fields);

        if (!apiUtils.validateApiKey(fields, res)) return;
        // sanitize pad id before continuing
        const padIdReceived = (await readOnlyManager.getIds(apiUtils.sanitizePadId(fields.padID))).padId;
        let data;
        try {
            data = JSON.parse(fields.data);
        } catch (err) {
            res.json({ code:1 , message: "data must be in JSON format"});
            return;
        }
        const pad = await padManager.getPad(padIdReceived);
        // TODO: update summary field with the given id
        // TODO: probably create a changeset for the exact attributed line
        try {
            const changeset = getSummaryLineChangeChs(pad, data.text, data.id);
            await pad.appendRevision(changeset);
            padMessageHandler.updatePadClients(pad);
        } catch (err) {
            logger.error(err);
            res.json({ code: 1, message: err.message});
            return;
        }
        res.json({ code: 0, message: "Success!"});
    });

    cb();
}

exports.padUpdate = function(hook, context, cb) {
    // TODO: give info to the minuteman Python API that it should update the summary if the pad is a transcript pad.
    // TODO: how to distinguish summary and transcript pads?
    logger.info(process.env.MINUTEMAN_API_URL);
    // make a POST request to the minuteman API at process.env.MINUTEMAN_API_URL
    // with the pad id
    let apiUrl = process.env.MINUTEMAN_API_URL + "pad_change/" + context.pad.id;
    logger.info(apiUrl);
    fetch(apiUrl, {
        method: "POST",
    })
    logger.info("padUpdate called!");
    cb(undefined);
}

exports.getLineHTMLForExport = function (hook, context) {
    var header = _analyzeLine(context.attribLine, context.apool);
    logger.info(header);
    if (header) {
        context.lineContent = "<span class=\"summary " + header + "\">" + context.lineContent + "</span>";
    } /* else {
        context.lineContent = "<span class=\"summary user\">" + context.lineContent + "</span>";
    } */
    return context.lineContent;
  }
  
  function _analyzeLine(alineAttrs, apool) {
    var header = null;
    if (alineAttrs) {
        var opIter = Changeset.opIterator(alineAttrs);
        if (opIter.hasNext()) {
            var op = opIter.next();
            logger.info(op);
            header = Changeset.opAttributeValue(op, 'summary', apool);
            logger.info(header);
        }
    }
    return header;
  }