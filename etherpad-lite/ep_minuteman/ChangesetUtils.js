const Changeset = require('ep_etherpad-lite/static/js/Changeset');
const Pad = require('ep_etherpad-lite/node/db/Pad');

/**
 * Create a changeset for appended summary line, analogous to getUtteranceAppendChs
 * @param {*} pad The pad to append to
 * @param {*} summaryText the summary text
 * @param {*} summaryId the summary id that is stored as attribute
 * @returns the appending changeset
 */
exports.getSummaryLineAppendChs = function(pad, summaryText, summaryId) {
    const oldText = Pad.cleanText(pad.text());
    const text = Pad.cleanText(summaryText);
    const attribs = [[ "summary_id", summaryId]];
    const changeset = Changeset.makeSplice(oldText, oldText.length, 0, text, attribs, pad.pool);
    return changeset;
}

/**
 * 
 * @param {*} pad 
 * @param {*} newSummaryText 
 * @param {*} summaryId 
 * @param {*} pool 
 * @returns 
 */
exports.getSummaryLineChangeChs = function(pad, newSummaryText, summaryId, pool) {
    const atext = pad.atext;
    var opIter = Changeset.opIterator(pad.atext.attribs);
    // FIXME: is this cleaning needed?
    let oldText = Pad.cleanText(pad.text());
    const text = Pad.cleanText(newSummaryText);
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

/**
 * Get the utterance changeset together with the utterance seq as attribute
 * @param {*} pad - the Pad object to append to
 * @param {*} utterance - Utterance object to append
 * @returns Changeset to apply to pad
 */
exports.getUtteranceAppendChs = function(pad, utterance) {
    // FIXME: how do I make this atomic? I probably can't
    const oldText = Pad.cleanText(pad.text());
    const text = Pad.cleanText(utterance.utterance);
    const attribs = [[ "trsc_seq", utterance.seq]];
    const changeset = Changeset.makeSplice(oldText, oldText.length, 0, text, attribs, pad.pool);
    return changeset;
}
