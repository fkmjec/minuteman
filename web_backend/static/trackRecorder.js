import transcribeBlob from "./apiInterface.js";
import { Utterance } from "./transcriptUtils.js";

// FIXME: this should somehow be better 
const SAMPLE_RATE = 44100;

function getTrackMediaRecorder(track, fileType) {
    // Create a new stream which only holds the audio track
    const originalStream = track.getOriginalStream();
    const stream = new MediaStream();

    originalStream.getAudioTracks().forEach(t => stream.addTrack(t));

    // Create the MediaRecorder
    let recorder = new MediaRecorder(stream,
        { mimeType: fileType });

    return recorder;
}

/**
 * A TrackRecorder object holds all the information needed for recording a
 * single JitsiTrack (either remote or local)
 * @param track The JitsiTrack the object is going to hold
 */
 export class TrackRecorder {
    /**
     * @param track The JitsiTrack the object is going to hold
     * @param timeslice The timeslice to use for the MediaRecorder
     */
    constructor(track, timeslice, maxUtteranceLen, fileType) {
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
        const stream = new MediaStream();
        originalStream.getAudioTracks().forEach(t => stream.addTrack(t));
    
        
        this.audioStreamSource = this.audioContext.createMediaStreamSource(stream);
        // audioContext.resume();
        this.audioContext.audioWorklet.addModule("/static/VoiceRecorder.js").then(() => {
            this.voiceRecorder = new AudioWorkletNode(this.audioContext, "VoiceRecorder");
            this.voiceRecorder = new AudioWorkletNode(this.audioContext, "VoiceRecorder");
            this.audioStreamSource.connect(this.voiceRecorder);
        }).catch((e) => console.error(e));
        // this.analyserNode = this.audioContext.createAnalyser();
        // this.audioContext.audioWorklet.addModule("./VoiceRecorder.js");

        // this needs to be done after connecting the mediaStreamSource, otherwise it will
        // not adjust to the sample rate of the stream
        // this.analyserNode.fftSize = 32768;
        // this.analyserBuffer = new Float32Array(this.analyserNode.fftSize);
    }

    /**
     * Estimates whether the chunk contains someone speaking
     * @param chunk - the blob with the audio
     */
    async isActive(chunk) {
        this.analyserNode.getFloatTimeDomainData(this.analyserBuffer);        
        let hasSpeech = false;
        if (!this.VAD) {
            this.VAD = await vad.NonRealTimeVAD.new({});
        }
        for await (const {audio, start, end} of this.VAD.run(this.analyserBuffer, this.audioContext.sampleRate)) {
            hasSpeech = true;
        }
        return hasSpeech;
    }

    start(newUtteranceCallback) {
        // this.recorder.start(this.timeslice);
        this.newUtteranceCallback = newUtteranceCallback;
        this.startTime = new Date().toISOString();
    }

    stop() {
        // this.recorder.stop();
    }

    saveTranscript(transcriptObject, author, time) {
        const utterance = new Utterance(time, author, transcriptObject.transcript);
        this.newUtteranceCallback(utterance);
        this.transcripts.push(utterance);
    }

    sendActiveData() {
        // merge the data chunks into a single blob
        // transcribeBlob(blob, this.startTime, this.name);
        // TODO
        this.start(this.newUtteranceCallback);
    }
}


export default { TrackRecorder };
