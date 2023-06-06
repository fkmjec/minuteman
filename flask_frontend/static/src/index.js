import MeetingRecorder from "./MeetingRecorder";

// JitsiMeetJS.setLogLevel(JitsiMeetJS.logLevels.ERROR);
// TODO move to a separate file
const initOptions = {
    disableAudioLevels: true
}; 
let recorder = new MeetingRecorder();


recorder.initJitsi(initOptions);

$(window).bind('beforeunload', recorder.unload.bind(recorder));
$(window).bind('unload', recorder.unload.bind(recorder));
// add transcriber to global scope
window.recorder = recorder;
