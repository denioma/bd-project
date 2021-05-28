CREATE OR REPLACE FUNCTION last_bid() RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
BEGIN
    INSERT INTO bid (itemid, b_date, price, bidder) VALUES (
        v_itemid,
        current_timestamp,
        v_price,
        v_bidder
    );
    RETURN NULL;
END;
$$;

DROP TRIGGER IF EXISTS last_bid ON bid;
CREATE TRIGGER last_bid AFTER INSERT ON bid EXECUTE FUNCTION last_bid();

CREATE OR REPLACE FUNCTION bid_open() RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    ends auction.ends%TYPE;
BEGIN
    SELECT auction.ends FROM auction WHERE itemid = NEW.itemid INTO ends;
    IF ends >= CURRENT_TIMESTAMP THEN
        RETURN NEW;
    ELSE
        UPDATE auction SET ongoing = FALSE 
        WHERE auction.itemid = NEW.itemid;
        RETURN OLD;
    END IF;
END;
$$;

DROP TRIGGER IF EXISTS bid_open ON bid;
CREATE TRIGGER bid_open BEFORE INSERT ON bid EXECUTE FUNCTION bid_open();