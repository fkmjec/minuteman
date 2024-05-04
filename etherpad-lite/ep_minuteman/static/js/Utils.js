const Changeset = require('ep_etherpad-lite/static/js/Changeset');

function serializeTrscSeq(seq) {
    return `trsc_${seq}`;
}

function deserializeTrscSeq(str) {
    return parseInt(str.split('_')[1]);
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
