const Changeset = require('ep_etherpad-lite/static/js/Changeset');
const Pad = require('ep_etherpad-lite/node/db/Pad');

function serializeTrscSeq(seq) {
    return `trsc_${seq}`;
}

function deserializeTrscSeq(str) {
    return parseInt(str.split('_')[1]);
}

function serializeSummSeq(seq) {
    return `summ_${seq}`;
}

function deserializeSummSeq(str) {
    return parseInt(str.split('_')[1]);
}

exports.prependTrscSeqNum = function (text, seq) {
    const paddedSeq = seq.toString().padStart(4, '0');
    const prepended = `${paddedSeq} || ${text}`;
    return prepended;
}

exports.prependSummMetadata = function (text, seq, start, end) {
    const prepended = `${seq} ${start}->${end} || ${text}`;
    return prepended;
}

exports.stripSummMetadata = function (text) {
    const split = text.split(' || ');
    if (split.length > 1) {
        return split[1];
    } else {
        return text;
    }
}

exports.stripTrscSeqNum = function (text) {
    const split = text.split(' || ');
    if (split.length > 1) {
        return split[1];
    } else {
        return text;
    }
}

function appendWithAttribs(pad, text, attribs) {
    const oldText = Pad.cleanText(pad.text());
    const cleanText = Pad.cleanText(text);
    const changeset = Changeset.makeSplice(oldText, oldText.length, 0, cleanText, attribs, pad.pool);
    return changeset;
}

exports.zip = function (a, b) {
    return a.map((k, i) => [k, b[i]]);
}

/**
 * Get an attribute value for a document line
 * @param {*} alineAttrs the document line's attributes
 * @param {*} apool the attribute pool
 * @param {*} attribKey the attribute key to check for
 * @returns the attribute value or null if not found
 */
exports.getLineAttributeValue = function (alineAttrs, apool, attribKey) {
    var header = null;
    if (alineAttrs) {
        var opIter = Changeset.opIterator(alineAttrs);
        if (opIter.hasNext()) {
            var op = opIter.next();
            const newHeader = Changeset.opAttributeValue(op, attribKey, apool);
            if (newHeader) {
                header = newHeader;
            }
        }
    }
    return header;
}

/**
 * Extracts the trsc seq from a given line.
 * @param {*} alineAttrs
 * @param {*} apool
 * @returns the trsc sequence number or null if not found
 */
exports.getTrscLineSeq = function (alineAttrs, apool) {
    const seq = exports.getLineAttributeValue(alineAttrs, apool, "trsc_seq");
    if (seq) {
        return deserializeTrscSeq(seq);
    }
    return null;
}

/**
 * Extracts the summary seq from a given line.
 * @param {*} alineAttrs
 * @param {*} apool
 * @returns the summary sequence number or null if not found
 */
exports.getSummLineSeq = function (alineAttrs, apool) {
    const seq = exports.getLineAttributeValue(alineAttrs, apool, "summary_seq");
    if (seq) {
        return deserializeSummSeq(seq);
    }
    return null;
}

/**
 * Create a changeset for appended summary line, analogous to getUtteranceAppendChs
 * @param {*} pad The pad to append to
 * @param {*} summaryText the summary text
 * @param {*} summarySeq the summary id that is stored as attribute
 * @returns the appending changeset
 */
exports.getSummaryAppendChs = function (pad, summarySeq, summaryText) {
    return appendWithAttribs(pad, summaryText, [["summary_seq", serializeSummSeq(summarySeq)]]);
}

/**
 * Create a changeset for updating a certain summary line
 * @param {*} pad the pad to update the summary line in
 * @param {*} newSummaryText the new summary content
 * @param {*} summarySeq the summary sequence number (the identifier)
 * @returns the changeset that replaces the old summary content with new
 */
exports.getSummaryUpdateChs = function (pad, summarySeq, newSummaryText, appendAll) {
    const atext = pad.atext;
    const apool = pad.apool();
    let oldText = pad.text();
    let charsBefore = 0;
    const textLines = atext.text.slice(0, -1).split('\n');
    const attribLines = Changeset.splitAttributionLines(atext.attribs, atext.text);
    for (const [attribLine, textLine] of exports.zip(attribLines, textLines)) {
        if (appendAll) {
            const charsToRemove = 0;
            charsBefore = oldText.length + 1;
            const attribs = [["summary_seq", serializeSummSeq(summarySeq)]];
            return Changeset.makeSplice(oldText, charsBefore, charsToRemove, "\n" + newSummaryText, attribs, pad.pool);
        }
        const candidateId = exports.getSummLineSeq(attribLine, apool);
        if (candidateId === summarySeq) {
            const charsToRemove = textLine.length;
            const attribs = [["summary_seq", serializeSummSeq(summarySeq)]];
            return Changeset.makeSplice(oldText, charsBefore, charsToRemove, newSummaryText, attribs, pad.pool);
        }
        charsBefore += textLine.length + 1;
    }
    return null;
}

/**
 * Get the utterance changeset together with the utterance seq as attribute
 * @param {*} pad - the Pad object to append to
 * @param {*} utterance - Utterance object to append
 * @returns Changeset to apply to pad
 */
exports.getUtteranceAppendChs = function (pad, utterance, isDebug) {
    let appendedText = utterance.utterance;
    if (isDebug) {
        appendedText = exports.prependTrscSeqNum(appendedText, utterance.seq);
    }
    return appendWithAttribs(pad, appendedText, [["trsc_seq", serializeTrscSeq(utterance.seq)]]);
}
