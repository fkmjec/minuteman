import MeetingRecorder from "./MeetingRecorder";
import ApiInterface from "./ApiInterface";

// JitsiMeetJS.setLogLevel(JitsiMeetJS.logLevels.ERROR);

function onChunkLenSelect() {
    let chunkLen = parseFloat($("#chunkLenSelect").val());
    ApiInterface.setChunkLen(chunkLen);
}

let recorder = new MeetingRecorder();


// recorder.initJitsi({});

$(window).bind('beforeunload', recorder.unload.bind(recorder));
$(window).bind('unload', recorder.unload.bind(recorder));
// add transcriber to global scope
window.recorder = recorder;

$(window).bind
window.onChunkLenSelect = onChunkLenSelect;
