/**
 *
 * @param selected
 */
function changeAudioOutput(selected) { // eslint-disable-line no-unused-vars
    JitsiMeetJS.mediaDevices.setAudioOutputDevice(selected.value);
}


function Transcriber() {
    this.confOptions = {
    };
    
    this.connection = null;
    this.isJoined = false;
    this.room = null;
    
    this.localTracks = [];
    this.remoteTracks = {};

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
    
    // JitsiMeetJS.mediaDevices.addEventListener(
    //     JitsiMeetJS.events.mediaDevices.DEVICE_LIST_CHANGED,
    //     this.onDeviceListChanged.bind(this));
    
    connection.connect();
    
    JitsiMeetJS.createLocalTracks({ devices: [ 'audio', 'video' ] })
        .then(this.onLocalTracks.bind(this))
        .catch(error => {
            throw error;
        });
    
    if (JitsiMeetJS.mediaDevices.isDeviceChangeAvailable('output')) {
        JitsiMeetJS.mediaDevices.enumerateDevices(devices => {
            const audioOutputDevices
                = devices.filter(d => d.kind === 'audiooutput');
    
            if (audioOutputDevices.length > 1) {
                $('#audioOutputSelect').html(
                    audioOutputDevices
                        .map(
                            d =>
                                `<option value="${d.deviceId}">${d.label}</option>`)
                        .join('\n'));
    
                $('#audioOutputSelectWrapper').show();
            }
        });
    }
    this.connection = connection;
}

/**
 * That function is called when connection is established successfully
 */
 Transcriber.prototype.onConnectionSuccess = function() {
    console.info(this)
    this.room = this.connection.initJitsiConference(this.options.roomName, this.confOptions);
    this.room.on(JitsiMeetJS.events.conference.TRACK_ADDED, this.onRemoteTrack.bind(this));
    this.room.on(
        JitsiMeetJS.events.conference.CONFERENCE_JOINED,
        this.onConferenceJoined.bind(this));
    this.room.on(JitsiMeetJS.events.conference.USER_JOINED, id => {
        console.log('user join');
        this.remoteTracks[id] = [];
    });
    this.room.on(JitsiMeetJS.events.conference.USER_LEFT, this.onUserLeft.bind(this));
    this.room.join();
}


/**
 * That function is executed when the conference is joined
 */
 Transcriber.prototype.onConferenceJoined = function() {
    console.log('conference joined!');
    this.isJoined = true;
    for (let i = 0; i < this.localTracks.length; i++) {
        this.room.addTrack(this.localTracks[i]);
    }
}

/**
 * Handles remote tracks
 * @param track JitsiTrack object
 */
 Transcriber.prototype.onRemoteTrack = function(track) {
    if (track.isLocal()) {
        return;
    }
    const participant = track.getParticipantId();

    if (!this.remoteTracks[participant]) {
        this.remoteTracks[participant] = [];
    }
    const idx = this.remoteTracks[participant].push(track);

    // track.addEventListener(
    //     JitsiMeetJS.events.track.TRACK_AUDIO_LEVEL_CHANGED,
    //     audioLevel => console.log(`Audio Level remote: ${audioLevel}`));
    // track.addEventListener(
    //     JitsiMeetJS.events.track.TRACK_MUTE_CHANGED,
    //     () => console.log('remote track muted'));
    // track.addEventListener(
    //     JitsiMeetJS.events.track.LOCAL_TRACK_STOPPED,
    //     () => console.log('remote track stoped'));
    // track.addEventListener(JitsiMeetJS.events.track.TRACK_AUDIO_OUTPUT_CHANGED,
    //     deviceId =>
    //         console.log(
    //             `track audio output device was changed to ${deviceId}`));
    const id = participant + track.getType() + idx;
    // FIXME: do I need this?
    if (track.getType() === 'audio') {
        $('body').append(
            `<audio autoplay='1' id='${participant}audio${idx}' />`);
    }
    track.attach($(`#${id}`)[0]);
}

/**
 * Handles local tracks.
 * @param tracks Array with JitsiTrack objects
 */
 Transcriber.prototype.onLocalTracks = function(tracks) {
    this.localTracks = tracks;
    for (let i = 0; i < this.localTracks.length; i++) {
        // localTracks[i].addEventListener(
        //     JitsiMeetJS.events.track.TRACK_AUDIO_LEVEL_CHANGED,
        //     audioLevel => console.log(`Audio Level local: ${audioLevel}`));
        // localTracks[i].addEventListener(
        //     JitsiMeetJS.events.track.TRACK_MUTE_CHANGED,
        //     () => console.log('local track muted'));
        // localTracks[i].addEventListener(
        //     JitsiMeetJS.events.track.LOCAL_TRACK_STOPPED,
        //     () => console.log('local track stoped'));
        // localTracks[i].addEventListener(
        //     JitsiMeetJS.events.track.TRACK_AUDIO_OUTPUT_CHANGED,
        //     deviceId =>
        //         console.log(
        //             `track audio output device was changed to ${deviceId}`));
        if (this.localTracks[i].getType() === 'audio') {
            $('body').append(
                `<audio autoplay='1' muted='true' id='localAudio${i}' />`);
            this.localTracks[i].attach($(`#localAudio${i}`)[0]);
        }
        if (this.isJoined) {
            this.room.addTrack(this.localTracks[i]);
        }
    }
}


/**
 *
 * @param id
 */
 Transcriber.prototype.onUserLeft = function(id) {
    console.log('user left');
    if (!this.remoteTracks[id]) {
        return;
    }
    const tracks = this.remoteTracks[id];

    for (let i = 0; i < tracks.length; i++) {
        tracks[i].detach($(`#${id}${tracks[i].getType()}`));
    }
}

/**
 * This function is called when the connection fail.
 */
Transcriber.prototype.onConnectionFailed = function() {
    console.error('Connection Failed!');
}

/**
 * This function is called when we disconnect.
 */
 Transcriber.prototype.disconnect = function() {
    console.log('disconnect!');
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
    for (let i = 0; i < this.localTracks.length; i++) {
        this.localTracks[i].dispose();
    }
    if (this.room) {
        this.room.leave();
    }
    if (this.connection) {
        this.connection.disconnect();
    }
}


// JitsiMeetJS.setLogLevel(JitsiMeetJS.logLevels.ERROR);
// TODO move to a better location
const initOptions = {
    disableAudioLevels: true
};

let transcriber = new Transcriber();

console.info(transcriber.connection)

transcriber.initJitsi(initOptions);

$(window).bind('beforeunload', transcriber.unload.bind(transcriber));
$(window).bind('unload', transcriber.unload.bind(transcriber));
// transcriber.connect();