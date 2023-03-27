CREATE DATABASE minuteman;

-- the session that is created after the user logs into the webpage
CREATE TABLE minuteman_session {
    id varchar(20) primary key not null,
    creation_time datetime not null,
};

-- the first utterances that were recorded from the meeting, without user editing
CREATE TABLE transcribed_utterance {
    id integer not null,
    author varchar(100) not null,
    utterance varchar(1000) not null,
    time datetime not null,
    minuteman_session_id varchar(20) foreign key references minuteman_session(id),
    primary key id
};