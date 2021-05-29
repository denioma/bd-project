CREATE TABLE db_user (
	username	VARCHAR(128),
	email	 	VARCHAR(128) NOT NULL,
	pass		VARCHAR(128) NOT NULL,
	valid		BOOL NOT NULL DEFAULT true,
	PRIMARY KEY(username)
);

CREATE TABLE auction (
	itemid		 		INTEGER,
	seller				VARCHAR(128) NOT NULL,
	minprice		 	NUMERIC(8,2) NOT NULL,
	price		 		NUMERIC(8,2) NOT NULL,
	title		 		VARCHAR(128) NOT NULL,
	last_bidder 		VARCHAR(128) UNIQUE NOT NULL,
	description	 		VARCHAR(512),
	ends		 		TIMESTAMP NOT NULL,
	cancelled	 		BOOL NOT NULL DEFAULT false,
	PRIMARY KEY(itemid)
);

CREATE TABLE bid (
	itemid	 			INTEGER,
	b_date		 		TIMESTAMP,
	price		 		NUMERIC(8,2) NOT NULL,
	valid		 		BOOL NOT NULL DEFAULT false,
	bidder 				VARCHAR(128),
	PRIMARY KEY(b_date,itemid,bidder)
);

CREATE TABLE mural (
	itemid	 		INTEGER,
	m_user 			VARCHAR(128),
	m_date		 	BIGINT NOT NULL,
	msg		 		VARCHAR(128) NOT NULL,
	PRIMARY KEY(itemid,m_user)
);

CREATE TABLE history (
	changed	 	TIMESTAMP,
	title		VARCHAR(128),
	description	VARCHAR(512),
	itemid		INTEGER,
	PRIMARY KEY(itemid)
);

ALTER TABLE auction ADD CONSTRAINT auction_fk1 FOREIGN KEY (seller) REFERENCES db_user(username);
ALTER TABLE bid ADD CONSTRAINT bid_fk1 FOREIGN KEY (itemid) REFERENCES auction(itemid);
ALTER TABLE bid ADD CONSTRAINT bid_fk2 FOREIGN KEY (bidder) REFERENCES db_user(username);
ALTER TABLE mural ADD CONSTRAINT mural_fk1 FOREIGN KEY (itemid) REFERENCES auction(itemid);
ALTER TABLE mural ADD CONSTRAINT mural_fk2 FOREIGN KEY (m_user) REFERENCES db_user(username);
ALTER TABLE history ADD CONSTRAINT history_fk1 FOREIGN KEY (itemid) REFERENCES auction(itemid);