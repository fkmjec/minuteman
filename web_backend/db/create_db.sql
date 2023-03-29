-- the session that is created after the user logs into the webpage
CREATE TABLE minuteman_session (
  id varchar(20) not null,
  creation_time timestamp not null,
  primary key (id)
);

-- the first utterances that were recorded from the meeting, without user editing
CREATE TABLE transcribed_utterance (
  id integer not null,
  author varchar(100) not null,
  utterance varchar(1000) not null,
  time timestamp not null,
  minuteman_session_id varchar(20) references minuteman_session(id),
  primary key (id)
);
