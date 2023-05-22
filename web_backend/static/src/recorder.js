import { TrackRecorder } from './trackRecorder.js';


/**
 * main exported object of the file, holding all
 * relevant functions and variables for the outside world
 * @param jitsiConference the jitsiConference which this object
 * is going to record
 */
function MeetingRecorder(jitsiConference, timeslice, maxUtteranceLen) {
    // array of TrackRecorders, where each trackRecorder
    // holds the JitsiTrack, MediaRecorder and recorder data
    this.recorders = [];

    // get which file type is supported by the current browser

    // the timeslice after which we get data from the MediaRecorders
    this.timeslice = timeslice;
    this.maxUtteranceLen = maxUtteranceLen;

    // the jitsiconference the object is recording
    this.jitsiConference = jitsiConference;
}


/**
 * Adds a new TrackRecorder object to the array.
 *
 * @param track the track potentially holding an audio stream
 */
MeetingRecorder.prototype.addTrack = function(track) {
    if (track.isAudioTrack()) {
        // create the track recorder
        const trackRecorder = new TrackRecorder(track, this.maxUtteranceLen);

        // push it to the local array of all recorders

        this.recorders.push(trackRecorder);

        // update the name of the trackRecorders
        this.updateNames();
    }
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
MeetingRecorder.prototype.removeTrack = function(track) {
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
MeetingRecorder.prototype.updateNames = function() {
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

MeetingRecorder.prototype.stop = function() {
    // set the boolean flag to false
    this.isRecording = false;

    // stop all recorders
    this.recorders.forEach(trackRecorder => trackRecorder.stop());
};


/**
 * export the main object AudioRecorder
 */
export default MeetingRecorder;
