import transcribeBlob from './apiInterface.js';
import { TrackRecorder } from './trackRecorder.js';


/**
 * Possible audio formats MIME types
 */
const AUDIO_WEBM = 'audio/webm'; // Supported in chrome
const AUDIO_OGG = 'audio/ogg'; // Supported in firefox


/**
 * Determines which kind of audio recording the browser supports
 * chrome supports "audio/webm" and firefox supports "audio/ogg"
 */
function determineCorrectFileType() {
    if (MediaRecorder.isTypeSupported(AUDIO_WEBM)) {
        return AUDIO_WEBM;
    } else if (MediaRecorder.isTypeSupported(AUDIO_OGG)) {
        return AUDIO_OGG;
    }
    throw new Error(
        'unable to create a MediaRecorder with the right mimetype!');
}

/**
 * main exported object of the file, holding all
 * relevant functions and variables for the outside world
 * @param jitsiConference the jitsiConference which this object
 * is going to record
 */
function AudioRecorder(jitsiConference, timeslice, maxUtteranceLen) {
    // array of TrackRecorders, where each trackRecorder
    // holds the JitsiTrack, MediaRecorder and recorder data
    this.recorders = [];

    // get which file type is supported by the current browser
    this.fileType = determineCorrectFileType();

    // boolean flag for active recording
    this.isRecording = false;

    // the timeslice after which we get data from the MediaRecorders
    this.timeslice = timeslice;
    this.maxUtteranceLen = maxUtteranceLen;

    // the jitsiconference the object is recording
    this.jitsiConference = jitsiConference;
}

/**
 * Add the exported module so that it can be accessed by other files
 */
AudioRecorder.determineCorrectFileType = determineCorrectFileType;

/**
 * Adds a new TrackRecorder object to the array.
 *
 * @param track the track potentially holding an audio stream
 */
AudioRecorder.prototype.addTrack = function(track) {
    if (track.isAudioTrack()) {
        // create the track recorder
        const trackRecorder = this.instantiateTrackRecorder(track);

        // push it to the local array of all recorders

        this.recorders.push(trackRecorder);

        // update the name of the trackRecorders
        this.updateNames();

        // If we're already recording, immediately start recording this new
        // track.
        if (this.isRecording) {
            trackRecorder.start();
        }
    }
};

/**
 * Creates a TrackRecorder object. Also creates the MediaRecorder and
 * data array for the trackRecorder.
 * @param track the JitsiTrack holding the audio MediaStream(s)
 */
AudioRecorder.prototype.instantiateTrackRecorder = function(track) {
    const trackRecorder = new TrackRecorder(track, this.timeslice, this.maxUtteranceLen);

    // Create a new stream which only holds the audio track
    const originalStream = trackRecorder.track.getOriginalStream();
    const stream = new MediaStream();

    originalStream.getAudioTracks().forEach(t => stream.addTrack(t));

    // Create the MediaRecorder
    trackRecorder.recorder = new MediaRecorder(stream,
        { mimeType: this.fileType });

    // array for holding the recorder data. Resets it when
    // audio already has been recorder once
    trackRecorder.data = [];

    // function handling a dataEvent, e.g the stream gets new data
    trackRecorder.recorder.ondataavailable = function(dataEvent) {
        if (dataEvent.data.size > 0) {
            trackRecorder.handleData(dataEvent);
        }
    };

    return trackRecorder;
};

/**
 * Notifies the module that a specific track has stopped, e.g participant left
 * the conference.
 * if the recording has not started yet, the TrackRecorder will be removed from
 * the array. If the recording has started, the recorder will stop recording
 * but not removed from the array so that the recorded stream can still be
 * accessed
 *
 * @param {JitsiTrack} track the JitsiTrack to remove from the recording session
 */
AudioRecorder.prototype.removeTrack = function(track) {
    if (track.isVideoTrack()) {
        return;
    }

    const array = this.recorders;
    let i;

    for (i = 0; i < array.length; i++) {
        if (array[i].track.getParticipantId() === track.getParticipantId()) {
            const recorderToRemove = array[i];

            if (this.isRecording) {
                recorderToRemove.stop();
            } else {
                // remove the TrackRecorder from the array
                array.splice(i, 1);
            }
        }
    }

    // make sure the names are up to date
    this.updateNames();
};

/**
 * Tries to update the name value of all TrackRecorder in the array.
 * If it hasn't changed,it will keep the exiting name. If it changes to a
 * undefined value, the old value will also be kept.
 */
AudioRecorder.prototype.updateNames = function() {
    const conference = this.jitsiConference;

    this.recorders.forEach(trackRecorder => {
        if (trackRecorder.track.isLocal()) {
            trackRecorder.name = 'Minuteman';
        } else {
            const id = trackRecorder.track.getParticipantId();
            const participant = conference.getParticipantById(id);
            const newName = participant.getDisplayName();

            if (newName !== 'undefined') {
                trackRecorder.name = newName;
            }
        }
    });
};

/**
 * Starts the audio recording of every local and remote track
 */
AudioRecorder.prototype.start = function() {
    if (this.isRecording) {
        throw new Error('audiorecorder is already recording');
    }

    // set boolean isRecording flag to true so if new participants join the
    // conference, that track can instantly start recording as well
    this.isRecording = true;

    // start all the mediaRecorders
    this.recorders.forEach(trackRecorder => trackRecorder.start());

    // log that recording has started
    console.log(
        `Started the recording of the audio. There are currently ${
            this.recorders.length} recorders active.`);
};

/**
 * Stops the audio recording of every local and remote track
 */
AudioRecorder.prototype.stop = function() {
    // set the boolean flag to false
    this.isRecording = false;

    // stop all recorders
    this.recorders.forEach(trackRecorder => trackRecorder.stop());
    console.log('stopped recording');
};


/**
 * Gets the mime type of the recorder audio
 * @returns {String} the mime type of the recorder audio
 */
AudioRecorder.prototype.getFileType = function() {
    return this.fileType;
};

/**
 * export the main object AudioRecorder
 */
export default AudioRecorder;
