import transcribeBlob from "./apiInterface.js";

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
    constructor(track, timeslice, maxUtteranceLen) {
        // The JitsiTrack holding the stream
        this.track = track;

        // The MediaRecorder recording the stream
        this.recorder = null;

        // The array of data chunks recorded from the stream
        // acts as a buffer until the data is stored on disk
        this.data = null;

        // the name of the person of the JitsiTrack. This can be undefined and/or
        // not unique
        this.name = null;

        // the time of the start of the recording
        this.startTime = null;
        this.timeslice = timeslice;
        // maximum utterance length in seconds, i.e. the longest stored sequence of chunks
        this.maxUtteranceLen = maxUtteranceLen;
    }

    /**
     * Estimates whether the chunk contains someone speaking
     * @param chunk - the blob with the audio
     */
    isActive(chunk) {
        // TODO
        return true;
    }

    start() {
        this.recorder.start(this.timeslice);
        this.startTime = new Date();
    }

    stop() {
        this.recorder.stop();
    }

    sendActiveData() {
        // merge the data chunks into a single blob
        const blob = new Blob(this.data, { type: 'audio/webm' });
        transcribeBlob(blob);
        this.stop();
        this.start();
        this.data = [];
    }

    /**
     * Handles an incoming data chunk from the MediaRecorder
     * @param event the event containing the data chunk
     */
    handleData(event) {
        // TODO check there is a large enough volume in the 1s chunk
        const chunk = event.data;
        if (!this.isActive(chunk)) {
            // utterance is complete, pack it and send it
            this.sendActiveData();
        } else {
            this.data.push(chunk);
            if (this.data.length * this.timeslice > this.maxUtteranceLen) {
                this.sendActiveData();
            }
        }
    }
}


export default { TrackRecorder };
