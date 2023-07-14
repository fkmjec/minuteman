import MeetingRecorder from "./MeetingRecorder";
import ApiInterface from "./ApiInterface";
import ConfigUtils from "./ConfigUtils";

// JitsiMeetJS.setLogLevel(JitsiMeetJS.logLevels.ERROR);

function onChunkLenSelect() {
    let chunkLen = parseFloat($("#chunkLenSelect").val());
    ApiInterface.setChunkLen(chunkLen);
}

function onModelSelect() {
    let model = $("#modelSelect").val();
    console.info(model);
    ApiInterface.setSummModel(model);
}

let recorder = new MeetingRecorder();


// recorder.initJitsi({});

$(window).bind('beforeunload', recorder.unload.bind(recorder));
$(window).bind('unload', recorder.unload.bind(recorder));
// add transcriber to global scope
window.recorder = recorder;

$(window).bind
window.onChunkLenSelect = onChunkLenSelect;
window.onModelSelect =  onModelSelect;

setInterval(async function() {
    try {
        let response = await ApiInterface.getState();
        ConfigUtils.updateConfigOptions(response.config, response.model_selection);
    } catch (error) {
        console.error(error.message);
    }
}, 1000);