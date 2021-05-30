-- This trigger updates auction with the latest bid
CREATE OR REPLACE FUNCTION last_bid() RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
BEGIN
    UPDATE auction SET price = NEW.price, last_bidder = NEW.bidder
    WHERE auction.auction_id = NEW.auction_id;
    RETURN NULL;
END;
$$;

DROP TRIGGER IF EXISTS last_bid ON bid;
CREATE TRIGGER last_bid AFTER INSERT ON bid 
    FOR EACH ROW EXECUTE FUNCTION last_bid();


-- This trigger prevents any insertions into bid for a closed auction or a lower bid
CREATE OR REPLACE FUNCTION bid_open() RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    current_price auction.price%TYPE;
    ends auction.ends%TYPE;
    cancelled auction.cancelled%TYPE;
BEGIN
    SELECT auction.price, auction.ends, auction.cancelled FROM auction 
    WHERE auction_id = NEW.auction_id INTO current_price, ends, cancelled;

    IF ends < CURRENT_TIMESTAMP THEN
        RAISE EXCEPTION 'Auction is closed';
    ELSIF cancelled = true  THEN
        RAISE EXCEPTION 'Auction is cancelled';
    ELSIF current_price >= NEW.price THEN
        RAISE EXCEPTION 'Bid is not higher than current price';
    ELSE
        RETURN NEW;
    END IF;
    RETURN OLD;
END;
$$;

DROP TRIGGER IF EXISTS bid_open ON bid;
CREATE TRIGGER bid_open BEFORE INSERT ON bid 
    FOR EACH ROW EXECUTE FUNCTION bid_open();

-- This trigger updates history on a auction's title or description update
CREATE OR REPLACE FUNCTION hist_update() RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    id history.hist_id%TYPE;
BEGIN
    SELECT COUNT(*) + 1 FROM history 
    WHERE history.auction_id = OLD.auction_id
    INTO id;

    INSERT INTO history (auction_id, hist_id, hist_date, title, description) 
    VALUES (OLD.auction_id, id, CURRENT_TIMESTAMP, OLD.title, OLD.description);
    RETURN NEW;
END;
$$; 

DROP TRIGGER IF EXISTS hist_update ON auction;
CREATE TRIGGER hist_update BEFORE UPDATE OF title, description ON auction
    FOR EACH ROW EXECUTE FUNCTION hist_update();

-- This trigger notifies the outbidded user
# TODO Test this
CREATE OR REPLACE FUNCTION outbidded() RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    old_bidder alias for old.last_bidder;
    new_bidder db_user.username%TYPE;
    id notifs.n_id%TYPE;
BEGIN
    SELECT COUNT(*)+1 FROM notifs
    WHERE user_id = old_bidder
    INTO id;

    SELECT username FROM db_user
    WHERE user_id = new.last_bidder
    INTO new_bidder;

    INSERT INTO notifs (user_id, n_id, n_date, msg) VALUES (
        old_bidder, id, CURRENT_TIMESTAMP, 
        'User ' || new_bidder || ' outbid you in auction ' || new.auction_id
    );
END;
$$;

DROP TRIGGER IF EXISTS outbidded ON auction;
CREATE TRIGGER outbidded BEFOR UPDATE OF last_bidder ON auction
    FOR EACH ROW EXECUTE FUNCTION outbidded(); 
