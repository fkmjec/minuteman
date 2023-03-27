import transcribeBlob from "./apiInterface.js";
import { Utterance } from "./transcriptUtils.js";

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

        this.recorder = getTrackMediaRecorder(track, this.fileType);
        // function handling a dataEvent, e.g the stream gets new data
        // FIXME: how to ditch the bind?
        let mediaRecorder = this;
        this.recorder.ondataavailable = function(dataEvent) {
            if (dataEvent.data.size > 0) {
                mediaRecorder.handleData(dataEvent);
            }
        };

        this.data = [];
        this.transcripts = [];

        // the name of the person of the JitsiTrack. This can be undefined and/or
        // not unique
        this.name = null;

        // the time of the start of the recording
        this.startTime = null;
        this.timeslice = timeslice;
        this.newUtteranceCallback = null;
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

    start(newUtteranceCallback) {
        this.recorder.start(this.timeslice);
        this.newUtteranceCallback = newUtteranceCallback;
        this.startTime = new Date();
    }

    stop() {
        this.recorder.stop();
    }

    saveTranscript(transcriptObject, author, time) {
        const utterance = new Utterance(transcriptObject.transcript, this.startTime, this.track);
        this.newUtteranceCallback(utterance);
        this.transcripts.push(utterance);
    }

    sendActiveData() {
        // merge the data chunks into a single blob
        this.recorder.ondataavailable = null;
        const blob = new Blob(this.data, { type: 'audio/webm' });
        transcribeBlob(blob, this.startTime, this.name, this.saveTranscript.bind(this));
        this.getNewRecorder(this.track);
        this.data = [];
        this.start(this.newUtteranceCallback);
    }

    getNewRecorder(track) {
        this.recorder = getTrackMediaRecorder(track, this.fileType);
        // FIXME: how to ditch the bind?        
        let mediaRecorder = this;
        this.recorder.ondataavailable = function(dataEvent) {
            if (dataEvent.data.size > 0) {
                mediaRecorder.handleData(dataEvent);
            }
        }
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
