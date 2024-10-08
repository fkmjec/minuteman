const Changeset = require('ep_etherpad-lite/static/js/Changeset');
const ChangesetUtils = require('./ChangesetUtils');

function getTrscSegmentCached(atext, apool, start, end, isDebug) {
    const textLines = atext.text.slice(0, -1).split('\n');
    const attribLines = Changeset.splitAttributionLines(atext.attribs, atext.text);
    let started = false;
    let trsc = "";
    for (const [attribLine, textLine] of ChangesetUtils.zip(attribLines, textLines)) {
        const seq = ChangesetUtils.getTrscLineSeq(attribLine, apool);
        if (seq) {
            if (seq >= start && !started) {
                started = true;
            } else if (seq > end) {
                break;
            }
        }

        if (started) {
            if (isDebug) {
                trsc += ChangesetUtils.stripTrscSeqNum(textLine) + "\n";
            } else {
                trsc += textLine + "\n";
            }
        }
    }
    return trsc;
}

/**
 * Select the transcript between the given start and end sequence numbers. If
 * the sequence numbers are not found in the transcript, the function takes
 * the smallest seq > start as start and the nearest seq > end as end.
 * @param {*} pad the Pad object to take the transcript from
 * @param {*} start start utterance seq number
 * @param {*} end end utterance seq number
 * @returns the transcript segment as string
 */
exports.getTrscSegment = function (pad, start, end, isDebug) {
    const atext = pad.atext;
    const apool = pad.apool();
    return getTrscSegmentCached(atext, apool, start, end, isDebug);
}