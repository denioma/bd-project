CREATE TABLE db_user (
	user_id	 INTEGER,
	username VARCHAR(128) NOT NULL,
	email	 VARCHAR(128) NOT NULL,
	pass	 BYTEA NOT NULL,
	valid	 BOOL NOT NULL DEFAULT true,
	admin	 BOOL NOT NULL DEFAULT false,
	PRIMARY KEY(user_id)
);

CREATE TABLE auction (
	itemid			VARCHAR(512),
	minprice    	NUMERIC(8,2) NOT NULL,
	price			NUMERIC(8,2) NOT NULL,
	title			VARCHAR(128) NOT NULL,
	description		VARCHAR(512),
	ends			TIMESTAMP NOT NULL,
	seller	    	INTEGER NOT NULL,
	last_bidder		INTEGER NOT NULL,
	ongoing			BOOL NOT NULL DEFAULT TRUE,
	cancelled		BOOL NOT NULL DEFAULT false,
	PRIMARY KEY(itemid)
);

CREATE TABLE bid (
	bidder 			INTEGER,
	b_date		    TIMESTAMP,
	item_id			VARCHAR(512),
	price		    NUMERIC(8,2) NOT NULL,
	valid		    BOOL NOT NULL DEFAULT false,
	PRIMARY KEY(b_date,item_id,bidder)
);

CREATE TABLE mural (
	m_id		INTEGER,
	m_date		TIMESTAMP NOT NULL,
	msg			VARCHAR(128) NOT NULL,
	item_id	    VARCHAR(512),
	user_id 	INTEGER,
	PRIMARY KEY(m_id,item_id,user_id)
);

CREATE TABLE history (
	hist_id	    	INTEGER,
	hist_date		TIMESTAMP NOT NULL,
	title	    	VARCHAR(128),
	description 	VARCHAR(512),
	item_itemid 	VARCHAR(512),
	PRIMARY KEY(hist_id,item_itemid)
);

CREATE TABLE notifs (
	n_id		    INTEGER,
	n_date		    TIMESTAMP NOT NULL,
	msg		        VARCHAR(512) NOT NULL,
	seen		    BOOL NOT NULL DEFAULT false,
	db_user_user_id INTEGER,
	PRIMARY KEY(n_id,db_user_user_id)
);

ALTER TABLE auction ADD CONSTRAINT auction_fk1 FOREIGN KEY (db_user_user_id) REFERENCES db_user(user_id);
ALTER TABLE bid ADD CONSTRAINT bid_fk1 FOREIGN KEY (item_itemid) REFERENCES item(itemid);
ALTER TABLE bid ADD CONSTRAINT bid_fk2 FOREIGN KEY (db_user_user_id) REFERENCES db_user(user_id);
ALTER TABLE mural ADD CONSTRAINT mural_fk1 FOREIGN KEY (item_itemid) REFERENCES item(itemid);
ALTER TABLE mural ADD CONSTRAINT mural_fk2 FOREIGN KEY (db_user_user_id) REFERENCES db_user(user_id);
ALTER TABLE history ADD CONSTRAINT history_fk1 FOREIGN KEY (item_itemid) REFERENCES item(itemid);
ALTER TABLE notifs ADD CONSTRAINT notifs_fk1 FOREIGN KEY (db_user_user_id) REFERENCES db_user(user_id);
