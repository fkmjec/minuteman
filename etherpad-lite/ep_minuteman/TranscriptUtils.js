const Changeset = require('ep_etherpad-lite/static/js/Changeset');

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
    console.info(attribLines);
    for (const line of attribLines) {
        console.info(line);
    }
    return "TODO not implemented hehe"
}