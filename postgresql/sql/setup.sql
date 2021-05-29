DROP TABLE IF EXISTS notifs;
DROP TABLE IF EXISTS history;
DROP TABLE IF EXISTS bid; 
DROP TABLE IF EXISTS mural;
DROP TABLE IF EXISTS auction;
DROP TABLE IF EXISTS db_user;
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
	item_id			VARCHAR(512),
	min_price    	NUMERIC(8,2) NOT NULL,
	price			NUMERIC(8,2) NOT NULL,
	title			VARCHAR(128) NOT NULL,
	description		VARCHAR(512),
	ends			TIMESTAMP NOT NULL,
	seller	    	INTEGER NOT NULL,
	last_bidder		INTEGER NOT NULL,
	ongoing			BOOL NOT NULL DEFAULT TRUE,
	cancelled		BOOL NOT NULL DEFAULT false,
	PRIMARY KEY(item_id)
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
	user_id 	INTEGER,
	item_id	    VARCHAR(512),
	m_id		INTEGER,
	m_date		TIMESTAMP NOT NULL,
	msg			VARCHAR(128) NOT NULL,
	PRIMARY KEY(user_id,item_id,m_id)
);

CREATE TABLE history (
	item_id 	VARCHAR(512),
	hist_id	    	INTEGER,
	hist_date		TIMESTAMP NOT NULL,
	title	    	VARCHAR(128),
	description 	VARCHAR(512),
	PRIMARY KEY(hist_id,item_id)
);

CREATE TABLE notifs (
	user_id 	INTEGER,
	n_id		INTEGER,
	n_date		TIMESTAMP NOT NULL,
	msg		    VARCHAR(512) NOT NULL,
	seen		BOOL NOT NULL DEFAULT false,
	PRIMARY KEY(n_id,user_id)
);

ALTER TABLE auction ADD CONSTRAINT auction_seller_fk FOREIGN KEY (seller) REFERENCES db_user(user_id);
ALTER TABLE auction ADD CONSTRAINT auction_last_bidder_fk FOREIGN KEY (last_bidder) REFERENCES db_user(user_id);
ALTER TABLE bid ADD CONSTRAINT bid_item_id_fk FOREIGN KEY (item_id) REFERENCES auction(item_id);
ALTER TABLE bid ADD CONSTRAINT bid_bidder_fk FOREIGN KEY (bidder) REFERENCES db_user(user_id);
ALTER TABLE mural ADD CONSTRAINT mural_item_id_fk FOREIGN KEY (item_id) REFERENCES auction(item_id);
ALTER TABLE mural ADD CONSTRAINT mural_user_id_fk FOREIGN KEY (user_id) REFERENCES db_user(user_id);
ALTER TABLE history ADD CONSTRAINT history_item_id_fk FOREIGN KEY (item_id) REFERENCES auction(item_id);
ALTER TABLE notifs ADD CONSTRAINT notifs_user_id_fk FOREIGN KEY (user_id) REFERENCES db_user(user_id);
