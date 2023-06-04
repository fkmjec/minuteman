const Changeset = require('ep_etherpad-lite/static/js/Changeset');
const ChangesetUtils = require('./ChangesetUtils');

function getSummaryLines(atext, apool) {
    const summaries = {};
    const textLines = atext.text.slice(0, -1).split('\n');
    const attribLines = Changeset.splitAttributionLines(atext.attribs, atext.text);
    for (const [attribLine, textLine] of ChangesetUtils.zip(attribLines, textLines)) {
        const seq = ChangesetUtils.getSummLineSeq(attribLine, apool);
        if (seq !== null) {
            if (!summaries[seq]) {
                summaries[seq] = textLine;
            } else {
                throw new Error("Multiple summaries with same seq number in one document!");
            }
        }
    }
    return summaries;
}

/**
 * Given the pad, it goes through all lines and returns a list of {seq, summary} pairs
 * corresponding to the summaries found in the document.
 * @param {*} pad the Pad object to take the transcript from
 * @param {*} start start utterance seq number
 * @param {*} end end utterance seq number
 * @returns the transcript segment as string
 */
exports.getSummariesFromPad = function (pad) {
    // FIXME: is this a valid way to acces the atext? Will it always be consistent?
    const atext = pad.atext;
    const apool = pad.apool();
    return getSummaryLines(atext, apool);
}