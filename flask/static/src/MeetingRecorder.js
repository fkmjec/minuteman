import { TrackRecorder } from './TrackRecorder.js';


function cleanRoomName(roomName) {
    return roomName.toLowerCase();
}

/**
 * main exported object of the file, holding all
 * relevant functions and variables for the outside world
 */
function MeetingRecorder() {
    // array of TrackRecorders, where each trackRecorder
    // holds the JitsiTrack and a VoiceRecorder
    this.recorders = [];


    this.confOptions = {
        startSilent: false,

        p2p: {
            enabled: false
        }
    };
    
    this.connection = null;
    this.isJoined = false;
    this.room = null;
    
    // TODO: transfer this to init constants somewhere
    this.options = {
        hosts: {
            domain: 'meet.jit.si',
            muc: 'conference.meet.jit.si'
        },
        roomName: '',
        serviceUrl: '',
    };
}


/**
 * Adds a new TrackRecorder object to the array.
 *
 * @param track the track potentially holding an audio stream
 */
MeetingRecorder.prototype.addTrack = function(track) {
    console.info("Adding track in MeetingRecorder");
    if (track.isAudioTrack()) {
        // create the track recorder
        const trackRecorder = new TrackRecorder(track, this.audioContext);

        // push it to the local array of all recorders
        this.recorders.push(trackRecorder);
        let participant = track.getParticipantId();

        // update the name of the trackRecorders
        this.updateNames();

        // add a silent audio playing element because of damned Chrome-based browsers
        $('body').append(
            `<audio autoplay='1' muted='true' id='${participant}audio' />`);
        track.attach($(`#${participant}audio`)[0]);
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
    console.info("Removing track in MeetingRecorder");
    if (track.isVideoTrack()) {
        return;
    }

    const array = this.recorders;
    let i;

    for (i = 0; i < array.length; i++) {
        if (array[i].track.getParticipantId() === track.getParticipantId()) {
            const recorderToRemove = array[i];
            recorderToRemove.stop();
            array.splice(i, 1);
        }
    }

    // remove silent element from background
    const element = document.getElementById(track.getParticipantId() + "audio");
    if (element) {
        element.outerHTML = "";
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
    const conference = this.room;

    this.recorders.forEach(trackRecorder => {
        if (trackRecorder.track.isLocal()) {
            trackRecorder.name = 'Minuteman';
        } else {
            const id = trackRecorder.track.getParticipantId();
            console.info(id);
            const participant = conference.getParticipantById(id);
            console.info(participant);
            const newName = participant.getDisplayName();
            console.info(newName);

            if (newName !== 'undefined') {
                trackRecorder.name = newName;
            }
        }
    });
};

MeetingRecorder.prototype.stop = function() {
    // stop all recorders
    this.recorders.forEach(trackRecorder => trackRecorder.stop());
};

MeetingRecorder.prototype.initJitsi = function(initOptions) {
    JitsiMeetJS.init(initOptions);
}

MeetingRecorder.prototype.connect = function() {
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
 MeetingRecorder.prototype.onConnectionSuccess = function() {
    this.room = this.connection.initJitsiConference(this.options.roomName, this.confOptions);
    this.room.setDisplayName("Minuteman")
    this.room.on(JitsiMeetJS.events.conference.TRACK_ADDED, this.onRemoteTrack.bind(this));
    this.room.on(JitsiMeetJS.events.conference.TRACK_REMOVED, track => {
        console.info(`track removed!!!${track}`);
        this.onRemoveRemoteTrack(track);
    });
    this.room.on(
        JitsiMeetJS.events.conference.CONFERENCE_JOINED,
        this.onConferenceJoined.bind(this));
    this.room.on(JitsiMeetJS.events.conference.USER_JOINED, id => {
        console.info('user join');
    });
    this.room.on(JitsiMeetJS.events.conference.USER_LEFT, this.onUserLeft.bind(this));
    this.room.join();
}


/**
 * That function is executed when the conference is joined
 */
 MeetingRecorder.prototype.onConferenceJoined = function() {
    console.info('conference joined!');
    this.isJoined = true;
}

/**
 * Handles remote tracks
 * @param track JitsiTrack object
 */
 MeetingRecorder.prototype.onRemoteTrack = function(track) {
    console.info("remote track added");
    if (track.isLocal() || track.type === 'video') {
        // only record outside and audio tracks
        return;
    }

    this.addTrack(track);
}

MeetingRecorder.prototype.onRemoveRemoteTrack = function(track) {
    console.info("remote track removed")
    this.removeTrack(track);
}


/**
 *
 * @param id
 */
 MeetingRecorder.prototype.onUserLeft = function(id) {
    console.info('user left');
}

/**
 * This function is called when the connection fails
 */
MeetingRecorder.prototype.onConnectionFailed = function() {
    console.error('Connection Failed!');
}

/**
 * This function is called when we disconnect.
 */
 MeetingRecorder.prototype.disconnect = function() {
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
    this.stop();
}

MeetingRecorder.prototype.onRoomSelect = function() {
    const initOptions = {
        disableAudioLevels: true
    };
    this.initJitsi(initOptions);
    // get the input value from the roomSelect element
    let value = document.getElementById("roomSelect").value;
    let roomName = cleanRoomName(value);
    if (this.connection != null) {
        this.connection.disconnect();
    }
    this.options.serviceUrl = 'wss://meet.jit.si/xmpp-websocket?room=' + roomName;
    this.options.roomName = roomName;
    this.audioContext = new AudioContext();
    this.connect(this.options);
}


/**
 *
 */
 MeetingRecorder.prototype.unload = function() {
    if (this.room) {
        this.room.leave();
    }
    if (this.connection) {
        this.connection.disconnect();
    }
}



/**
 * export the main object AudioRecorder
 */
export default MeetingRecorder;
