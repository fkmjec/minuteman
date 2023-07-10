import ApiInterface from "./ApiInterface.js";

// TODO move up in the hierarchy
const SENT_CHUNK_LEN = 1.0; // seconds

/**
 * A TrackRecorder object holds all the information needed for recording a
 * single JitsiTrack (either remote or local)
 * @param track The JitsiTrack the object is going to hold
 */
 export class TrackRecorder {
    /**
     * @param track The JitsiTrack the object is going to hold
     */
    constructor(track, audioContext) {
        // The JitsiTrack holding the stream
        this.track = track;

        // the name of the person of the JitsiTrack. This can be undefined and/or
        // not unique
        this.name = null;

        this.audioContext = audioContext;

        const originalStream = track.getOriginalStream();
        const originalStreamNode = this.audioContext.createMediaStreamSource(originalStream);

        this.audioContext.audioWorklet.addModule("/static/dist/VoiceRecorder.js").then(() => {            
            this.voiceRecorder = new AudioWorkletNode(this.audioContext, "VoiceRecorder", {
                processorOptions: {
                    sampleRate: this.audioContext.sampleRate,
                    targetSampleRate: 16000,
                    sentChunkLen: SENT_CHUNK_LEN,
                }
            });
            this.voiceRecorder.port.onmessage = (e) => this.sendActiveData(e.data);
            originalStreamNode.connect(this.voiceRecorder);
        }).catch((e) => console.error(e));
    }
    
    stop() {
        if (this.voiceRecorder !== undefined) {
            this.voiceRecorder.port.postMessage("stop");
        }
        this.audioContext.close();
    }

    /**
     * @param {data} Float32Array of raw audio 
     */
    sendActiveData(data) {
        const startTime = new Date(Date.now() - SENT_CHUNK_LEN * 1000);
        ApiInterface.sendAudioData(data, startTime, this.name, this.track.getParticipantId());
    }
}


export default { TrackRecorder };
