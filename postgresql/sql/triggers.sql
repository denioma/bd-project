-- This trigger updates auction with the latest bid
CREATE OR REPLACE FUNCTION last_bid() RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
BEGIN
    UPDATE auction SET price = NEW.price, last_bidder = NEW.bidder
    WHERE auction.item_id = NEW.item_id;
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
    WHERE item_id = NEW.item_id INTO current_price, ends, cancelled;

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

-- This trigger updates history on a auction update
CREATE OR REPLACE FUNCTION hist_update() RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    id history.hist_id%TYPE;
BEGIN
    SELECT COUNT(*) + 1 FROM history 
    WHERE history.item_id = OLD.item_id
    INTO id;

    INSERT INTO history (item_id, hist_id, hist_date, title, description) 
    VALUES (OLD.item_id, id, CURRENT_TIMESTAMP, OLD.title, OLD.description);
    RETURN NEW;
END;
$$; 

DROP TRIGGER IF EXISTS hist_update ON auction;
CREATE TRIGGER hist_update BEFORE UPDATE ON auction
    FOR EACH ROW EXECUTE FUNCTION hist_update();
