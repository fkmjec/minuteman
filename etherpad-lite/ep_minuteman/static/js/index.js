const { Changeset } = require("ep_etherpad-lite/static/js/Changeset"); 
const Utils = require("./Utils");

exports.aceAttribsToClasses = function(hook, context, cb) {
    if (context.key == "summary_seq") {
        return cb([`summary_seq::${context.value}`]);
    } else if (context.key == "trsc_seq") {
        return cb([`trsc_seq::${context.value}`]);
    }
    return cb();
};

exports.collectContentPre = function (hookName, context, cb) {
    const state = context.state;
    if (context.cls.startsWith("summary_seq::")) {
        context.cc.doAttrib(state, context.cls);
    }
    if (context.cls.startsWith("trsc_seq::")) {
        context.cc.doAttrib(state, context.cls);
    }
    return cb();
};

function sendSummaryRequest(sessionId, start, end) {
    let data = new FormData();
    // FIXME: make this crap readable in a function somewhere
    data.append('start', start);
    data.append('end', end);
    data.append("session_id", sessionId);
    const request = new Request(window.location.origin + "/api/createSumm", {
        method: 'POST',
        body: data,
    });
    fetch(request);
}

function isSummKeyCombo(event) {
    const keyUp = event.type === "keyup";
    const ctrlAlt = event.originalEvent.altKey && event.originalEvent.ctrlKey;
    const isS = event.originalEvent.key === "s";
    return keyUp && ctrlAlt && isS;
}

function getSelectionInSeqNumbers(context) {
    currentSelectionStart = context.rep.selStart;
    currentSelectionEnd = context.rep.selEnd;
    if (context.rep.selStart[0] === context.rep.selEnd[0] && context.rep.selStart[1] === context.rep.selEnd[1]) {
        currentSelectionValid = false;
    }
    const startLine = context.rep.selStart[0];
    const endLine = context.rep.selEnd[0];
    let startTrscSeq = null;
    let endTrscSeq = null;
    let lineNumber = 0;
    for (const attrLine of context.rep.alines) {
        const trscSeq = Utils.getTrscLineSeq(attrLine, context.rep.apool);
        if (trscSeq !== null) {
            if (lineNumber <= startLine) {
                startTrscSeq = trscSeq;
            }
            if (lineNumber >= startLine && lineNumber <= endLine) {
                endTrscSeq = trscSeq;
            }
        }
        lineNumber++;
    }

    return [startTrscSeq, endTrscSeq];
}


exports.aceKeyEvent = (hookName, context, cb) => {
    padId = window.location.pathname.split('/').pop();
    if (isSummKeyCombo(context.evt) && padId.endsWith(".trsc")) {
        const [startTrscSeq, endTrscSeq] = getSelectionInSeqNumbers(context);
        sessionId = padId.slice(0, -5);
        sendSummaryRequest(sessionId, startTrscSeq, endTrscSeq);
    }
    return cb();
};