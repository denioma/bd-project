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
BEGIN
    SELECT auction.price, auction.ends FROM auction 
    WHERE item_id = NEW.itemid INTO current_price ends;
    
    IF (ends >= CURRENT_TIMESTAMP OR cancelled = false) AND NEW.price > current_price
    THEN
        RETURN NEW;
    ELSE
        RETURN OLD;
    END IF;
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
    WHERE history.hist_id = OLD.item_id
    INTO id;

    INSERT INTO history (item_id, hist_id, hist_date, title, description) 
    VALUES (OLD.item_id, id, CURRENT_TIMESTAMP, OLD.title, OLD.description);
END;
$$; 

DROP TRIGGER IF EXISTS hist_update ON auction;
CREATE TRIGGER hist_update BEFORE UPDATE ON auction
    FOR EACH ROW EXECUTE FUNCTION hist_update();