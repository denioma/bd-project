-- Databases - 2020/2021
-- Final Project - Table Setup DDL/SQL

-- Authors:
--   David Valente Pereira Barros Leitão - 2019223148
--   João António Correia Vaz - 2019218159
--   Rodrigo Alexandre da Mota Machado - 2019218299
------------------------------------------------------

DROP TABLE IF EXISTS notifs;
DROP TABLE IF EXISTS history;
DROP TABLE IF EXISTS bid; 
DROP TABLE IF EXISTS mural;
DROP TABLE IF EXISTS auction;
DROP TABLE IF EXISTS db_user;

CREATE TABLE db_user (
	user_id	 	SERIAL,
	username 	VARCHAR(128) UNIQUE NOT NULL,
	email	 	VARCHAR(128) NOT NULL,
	pass	 	BYTEA NOT NULL,
	valid	 	BOOL NOT NULL DEFAULT true,
	admin	 	BOOL NOT NULL DEFAULT false,
	PRIMARY KEY(user_id)
);

CREATE TABLE auction (
	auction_id 		SERIAL,
	item_id			VARCHAR(512) NOT NULL,
	min_price    	NUMERIC(8,2) NOT NULL,
	price			NUMERIC(8,2) NOT NULL,
	title			VARCHAR(128) NOT NULL,
	description		VARCHAR(512),
	ends			TIMESTAMP NOT NULL,
	seller	    	INTEGER NOT NULL,
	last_bidder		INTEGER,
	ongoing			BOOL NOT NULL DEFAULT TRUE,
	cancelled		BOOL NOT NULL DEFAULT false,
	PRIMARY KEY(auction_id)
);

CREATE TABLE bid (
	auction_id		INTEGER,
	bidder 			INTEGER,
	bid_id			INTEGER,
	bid_date		TIMESTAMP NOT NULL,
	price			NUMERIC(8,2) NOT NULL,
	valid			BOOL NOT NULL DEFAULT true,
	PRIMARY KEY(auction_id, bidder, bid_id)
);

CREATE TABLE mural (
	auction_id	INTEGER,
	user_id 	INTEGER,
	m_id      	SERIAL,
	m_date		TIMESTAMP NOT NULL,
	msg			VARCHAR(128) NOT NULL,
	PRIMARY KEY(auction_id, user_id, m_id)
);

CREATE TABLE history (
	auction_id 		INTEGER,
	hist_id	    	INTEGER,
	hist_date		TIMESTAMP NOT NULL,
	title	    	VARCHAR(128) NOT NULL,
	description 	VARCHAR(512) NOT NULL,
	PRIMARY KEY(auction_id, hist_id)
);

CREATE TABLE notifs (
	user_id 	INTEGER,
	n_id		INTEGER,
	n_date		TIMESTAMP NOT NULL,
	msg		    VARCHAR(512) NOT NULL,
	seen		BOOL NOT NULL DEFAULT false,
	PRIMARY KEY(user_id, n_id)
);

ALTER TABLE auction ADD CONSTRAINT auction_seller_fk FOREIGN KEY (seller) REFERENCES db_user(user_id);
ALTER TABLE auction ADD CONSTRAINT auction_last_bidder_fk FOREIGN KEY (last_bidder) REFERENCES db_user(user_id);
ALTER TABLE bid ADD CONSTRAINT bid_auction_id_fk FOREIGN KEY (auction_id) REFERENCES auction(auction_id);
ALTER TABLE bid ADD CONSTRAINT bid_bidder_fk FOREIGN KEY (bidder) REFERENCES db_user(user_id);
ALTER TABLE mural ADD CONSTRAINT mural_auction_id_fk FOREIGN KEY (auction_id) REFERENCES auction(auction_id);
ALTER TABLE mural ADD CONSTRAINT mural_user_id_fk FOREIGN KEY (user_id) REFERENCES db_user(user_id);
ALTER TABLE history ADD CONSTRAINT history_auction_id_fk FOREIGN KEY (auction_id) REFERENCES auction(auction_id);
ALTER TABLE notifs ADD CONSTRAINT notifs_user_id_fk FOREIGN KEY (user_id) REFERENCES db_user(user_id);
