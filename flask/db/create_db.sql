-- the session that is created after the user logs into the webpage
CREATE TABLE minuteman_session (
  id varchar(20) not null,
  creation_time timestamp not null,
  primary key (id)
);
