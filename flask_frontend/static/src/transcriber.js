import MeetingRecorder from './recorder.js'

const AUDIO_RECORD_SLICE = 1000;
const MAX_UTTERANCE_LEN = 10000;

// /**
//  *
//  * @param selected
//  */
// function changeAudioOutput(selected) { // eslint-disable-line no-unused-vars
//     JitsiMeetJS.mediaDevices.setAudioOutputDevice(selected.value);
// }


function Transcriber() {
    this.confOptions = {
    };

    this.meetingRecorder = null;
    
    this.connection = null;
    this.isJoined = false;
    this.room = null;
    
    this.tracks = {};

    // TODO: transfer this to init constants somewhere
    this.options = {
        hosts: {
            domain: 'meet.jit.si',
            muc: 'conference.meet.jit.si'
        },
        roomName: '',
        bosh: ''
    };
}

Transcriber.prototype.initJitsi = function(initOptions) {
    JitsiMeetJS.init(initOptions);
}

Transcriber.prototype.connect = function() {
    let connection = new JitsiMeetJS.JitsiConnection(null, null, this.options);

    connection.addEventListener(
        JitsiMeetJS.events.connection.CONNECTION_ESTABLISHED,
        this.onConnectionSuccess.bind(this));
    connection.addEventListener(
        JitsiMeetJS.events.connection.CONNECTION_FAILED,
        this.onConnectionFailed.bind(this));
    connection.addEventListener(
        JitsiMeetJS.events.connection.CONNECTION_DISCONNECTED,
        this.disconnect.bind(this));
        
    connection.connect();
    this.connection = connection;
}

/**
 * That function is called when connection is established successfully
 */
 Transcriber.prototype.onConnectionSuccess = function() {
    this.room = this.connection.initJitsiConference(this.options.roomName, this.confOptions);
    this.room.setDisplayName("Minuteman")
    this.room.on(JitsiMeetJS.events.conference.TRACK_ADDED, this.onRemoteTrack.bind(this));
    // TODO: stop recording on removed tracks?
    this.room.on(JitsiMeetJS.events.conference.TRACK_REMOVED, track => {
        console.info(`track removed!!!${track}`);
        this.onRemoveRemoteTrack(track);
    });
    this.room.on(
        JitsiMeetJS.events.conference.CONFERENCE_JOINED,
        this.onConferenceJoined.bind(this));
    this.room.on(JitsiMeetJS.events.conference.USER_JOINED, id => {
        console.info('user join');
        this.tracks[id] = [];
    });
    this.room.on(JitsiMeetJS.events.conference.USER_LEFT, this.onUserLeft.bind(this));
    this.room.join();
    this.meetingRecorder = new MeetingRecorder(this.room, MAX_UTTERANCE_LEN);
}


/**
 * That function is executed when the conference is joined
 */
 Transcriber.prototype.onConferenceJoined = function() {
    console.info('conference joined!');
    this.isJoined = true;
}

/**
 * Handles remote tracks
 * @param track JitsiTrack object
 */
 Transcriber.prototype.onRemoteTrack = function(track) {
    console.info("remote track added");
    if (track.isLocal() || track.type === 'video') {
        // only record outside and audio tracks
        return;
    }
    this.meetingRecorder.addTrack(track);
}

Transcriber.prototype.onRemoveRemoteTrack = function(track) {
    console.info("remote track removed")
    this.meetingRecorder.removeTrack(track);
}


/**
 *
 * @param id
 */
 Transcriber.prototype.onUserLeft = function(id) {
    console.info('user left');
    if (!this.tracks[id]) {
        return;
    }
    const tracks = this.tracks[id];
}

/**
 * This function is called when the connection fails
 */
Transcriber.prototype.onConnectionFailed = function() {
    console.error('Connection Failed!');
}

/**
 * This function is called when we disconnect.
 */
 Transcriber.prototype.disconnect = function() {
    this.connection.removeEventListener(
        JitsiMeetJS.events.connection.CONNECTION_ESTABLISHED,
        // FIXME: does this make sense?
        this.onConnectionSuccess.bind(this));
    this.connection.removeEventListener(
        JitsiMeetJS.events.connection.CONNECTION_FAILED,
        // FIXME: does this make sense?
        this.onConnectionFailed.bind(this));
    this.connection.removeEventListener(
        JitsiMeetJS.events.connection.CONNECTION_DISCONNECTED,
        // FIXME: does this make sense?
        this.disconnect.bind(this));
    // TODO remove all references to audio recording
    this.meetingRecorder.stop();
    this.meetingRecorder = null;
}

Transcriber.prototype.onRoomSelect = function() {
    // get the input value from the roomSelect element
    let value = document.getElementById("roomSelect").value;
    // FIXME: inserting unsanitized values
    if (this.connection != null) {
        this.connection.disconnect();
    }
    this.options.bosh = 'https://meet.jit.si/http-bind?room=' + value;
    this.options.roomName = value;
    this.connect(this.options);
}


/**
 *
 */
 Transcriber.prototype.unload = function() {
    if (this.room) {
        this.room.leave();
    }
    if (this.connection) {
        this.connection.disconnect();
    }
}


export default Transcriber;
