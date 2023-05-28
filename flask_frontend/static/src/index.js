import Transcriber from "./transcriber";

// JitsiMeetJS.setLogLevel(JitsiMeetJS.logLevels.ERROR);
// TODO move to a separate file
const initOptions = {
    disableAudioLevels: true
}; 
let transcriber = new Transcriber();


transcriber.initJitsi(initOptions);

$(window).bind('beforeunload', transcriber.unload.bind(transcriber));
$(window).bind('unload', transcriber.unload.bind(transcriber));
// add transcriber to global scope
window.transcriber = transcriber;
