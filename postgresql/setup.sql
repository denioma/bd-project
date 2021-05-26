CREATE TABLE auction (
	itemid		 NUMERIC(13,0),
	minprice		 NUMERIC(8,2) NOT NULL,
	price		 NUMERIC(8,2) NOT NULL,
	title		 VARCHAR(64) NOT NULL,
	description		 VARCHAR(512),
	ends			 TIMESTAMP NOT NULL,
	cancelled		 BOOL NOT NULL DEFAULT false,
	seller_db_user_userid INTEGER NOT NULL,
	PRIMARY KEY(itemid)
);

CREATE TABLE db_user (
	email	 VARCHAR(512) NOT NULL,
	userid INTEGER NOT NULL,
	banned BOOL NOT NULL DEFAULT false,
	PRIMARY KEY(userid)
);

CREATE TABLE seller (
	db_user_userid INTEGER NOT NULL,
	PRIMARY KEY(db_user_userid)
);

CREATE TABLE buyer (
	won		 INTEGER,
	db_user_userid INTEGER NOT NULL,
	PRIMARY KEY(db_user_userid)
);

CREATE TABLE comment (
	c_date	 TIMESTAMP NOT NULL,
	c_text	 VARCHAR(280) NOT NULL,
	auction_itemid NUMERIC(13,0),
	PRIMARY KEY(auction_itemid)
);

CREATE TABLE bid (
	bid_date		 TIMESTAMP,
	price		 INTEGER NOT NULL,
	valid		 BOOL NOT NULL DEFAULT true,
	buyer_db_user_userid	 INTEGER,
	auction_itemid	 NUMERIC(13,0),
	buyer_db_user_userid1 INTEGER NOT NULL,
	PRIMARY KEY(bid_date,buyer_db_user_userid,auction_itemid)
);

CREATE TABLE history (
	h_date	 TIMESTAMP,
	title		 VARCHAR(512),
	description	 VARCHAR(512),
	auction_itemid NUMERIC(13,0),
	PRIMARY KEY(auction_itemid)
);

ALTER TABLE auction ADD CONSTRAINT auction_fk1 FOREIGN KEY (seller_db_user_userid) REFERENCES seller(db_user_userid);
ALTER TABLE seller ADD CONSTRAINT seller_fk1 FOREIGN KEY (db_user_userid) REFERENCES db_user(userid);
ALTER TABLE buyer ADD CONSTRAINT buyer_fk1 FOREIGN KEY (db_user_userid) REFERENCES db_user(userid);
ALTER TABLE comment ADD CONSTRAINT comment_fk1 FOREIGN KEY (auction_itemid) REFERENCES auction(itemid);
ALTER TABLE bid ADD CONSTRAINT bid_fk1 FOREIGN KEY (buyer_db_user_userid) REFERENCES buyer(db_user_userid);
ALTER TABLE bid ADD CONSTRAINT bid_fk2 FOREIGN KEY (auction_itemid) REFERENCES auction(itemid);
ALTER TABLE bid ADD CONSTRAINT bid_fk3 FOREIGN KEY (buyer_db_user_userid1) REFERENCES buyer(db_user_userid);
ALTER TABLE history ADD CONSTRAINT history_fk1 FOREIGN KEY (auction_itemid) REFERENCES auction(itemid);
