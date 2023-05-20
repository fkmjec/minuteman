import transcribeBlob from "./apiInterface.js";
import { Utterance } from "./transcriptUtils.js";
import { NonRealTimeVAD } from "@ricky0123/vad-web"

// TODO move up in the hierarchy
const VOICE_CHECKING_LEN = 1;

/**
 * A TrackRecorder object holds all the information needed for recording a
 * single JitsiTrack (either remote or local)
 * @param track The JitsiTrack the object is going to hold
 */
 export class TrackRecorder {
    /**
     * @param track The JitsiTrack the object is going to hold
     */
    constructor(track, maxUtteranceLen, fileType) {
        // The JitsiTrack holding the stream
        this.track = track;
        this.fileType = fileType;

        // the name of the person of the JitsiTrack. This can be undefined and/or
        // not unique
        this.name = null;

        // maximum utterance length in seconds, i.e. the longest stored sequence of chunks
        this.maxUtteranceLen = maxUtteranceLen;
        this.audioContext = new AudioContext();

        const originalStream = track.getOriginalStream();
        
        // merge the (usually stereo) audio tracks into one
        this.mergedTracksDestination = new MediaStreamAudioDestinationNode(this.audioContext, { channelCount: 1 });
        this.inNodes = [];
        originalStream.getAudioTracks().forEach(t => {
            let inNode = this.audioContext.createMediaStreamTrackSource(t);
            this.inNodes.push(inNode);
            inNode.connect(this.mergedTracksDestination);
        });
        this.mergedStreamSource = this.audioContext.createMediaStreamSource(this.mergedTracksDestination.stream);
        
        this.audioContext.audioWorklet.addModule("/static/dist/VoiceRecorder.js").then(() => {            
            this.voiceRecorder = new AudioWorkletNode(this.audioContext, "VoiceRecorder", {
                processorOptions: {
                    sampleRate: this.audioContext.sampleRate,
                    voiceCheckingLen: VOICE_CHECKING_LEN,
                    maxSavedLen: this.maxUtteranceLen
                }
            });
            this.voiceRecorder.port.onmessage = (e) => console.log(e.data);
            this.mergedStreamSource.connect(this.voiceRecorder);
        }).catch((e) => console.error(e));
        console.info(this.audioContext.sampleRate);
    }

    /**
     * Estimates whether the chunk contains someone speaking
     * @param chunk - the blob with the audio
     */
    async isActive(chunk) {
        this.analyserNode.getFloatTimeDomainData(this.analyserBuffer);
        let hasSpeech = false;
        if (!this.VAD) {
            this.VAD = await NonRealTimeVAD.new({});
        }
        for await (const {audio, start, end} of this.VAD.run(this.analyserBuffer, this.audioContext.sampleRate)) {
            hasSpeech = true;
        }
        return hasSpeech;
    }

    start() {
        // this.recorder.start(this.timeslice);
        // TODO
        this.startTime = new Date().toISOString();
    }

    stop() {
        // TODO
    }

    encodeData(floatBuffer) {
        // TODO use lamejs
    }

    sendActiveData() {
        // merge the data chunks into a single blob
        // transcribeBlob(blob, this.startTime, this.name);
        // TODO
    }
}


export default { TrackRecorder };
