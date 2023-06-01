const Changeset = require('ep_etherpad-lite/static/js/Changeset');

function zip(a, b) {
    return a.map((k, i) => [k, b[i]]);
}

function getTrscSeqNum(alineAttrs, apool) {
    var header = null;
    if (alineAttrs) {
        var opIter = Changeset.opIterator(alineAttrs);
        if (opIter.hasNext()) {
            var op = opIter.next();
            header = Changeset.opAttributeValue(op, 'trsc_seq', apool);
        }
    }
    return header;
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
exports.getTrscSegment = function (pad, start, end) {
    // FIXME: is this a valid way to acces the atext? Will it always be consistent?
    const atext = pad.atext;
    const apool = pad.apool();
    const textLines = atext.text.slice(0, -1).split('\n');
    const attribLines = Changeset.splitAttributionLines(atext.attribs, atext.text);
    let started = false;
    let trsc = "";
    for (const [attribLine, textLine] of zip(attribLines, textLines)) {
        const seq = parseInt(getTrscSeqNum(attribLine, apool));
        if (seq >= start) {
            started = true;
        } else if (seq > end) {
            break;
        }
        if (started) {
            trsc += textLine;
        }
    }
    return trsc;
}