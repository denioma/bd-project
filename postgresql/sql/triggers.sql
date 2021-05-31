-- Databases - 2020/2021
-- Final Project - Procedures, functions and triggers in PL/pgSQL

-- Authors:
--   David Valente Pereira Barros Leitão - 2019223148
--   João António Correia Vaz - 2019218159
--   Rodrigo Alexandre da Mota Machado - 2019218299

-- Not a trigger, but useful to many of them
CREATE OR REPLACE PROCEDURE notify(v_user INTEGER, v_date TIMESTAMP, v_msg VARCHAR)
LANGUAGE plpgsql
AS $$
DECLARE
    id INTEGER;
BEGIN
    SELECT COUNT(*)+1 INTO id FROM notifs WHERE user_id = v_user;
    
    INSERT INTO notifs (user_id, n_id, n_date, msg) 
    VALUES (v_user, id, v_date, v_msg); 
END;
$$;

-- Close an auction
CREATE OR REPLACE PROCEDURE close_auctions()
LANGUAGE plpgsql
AS $$
DECLARE
    cur CURSOR FOR
        SELECT auction_id, seller, last_bidder as winner, username as name_winner, ends 
        FROM auction JOIN db_user ON auction.last_bidder = db_user.user_id
        WHERE ongoing;
    bid_row RECORD;
    close_stamp TIMESTAMP := CURRENT_TIMESTAMP;
BEGIN
    FOR row IN cur LOOP
        IF row.ends < close_stamp THEN
            UPDATE auction SET ongoing = false WHERE auction_id = row.auction_id;
            CALL notify(row.winner, close_stamp,
                '[System] You won auction #' || row.auction_id ||'.'
            );

            CALL notify(row.seller, close_stamp,
                '[System] Your auction (' || row.auction_id || ') is now closed. The winner was ' 
                    || row.name_winner || '.'
            );

            FOR bid_row IN 
            SELECT bidder FROM bid WHERE bidder != row.winner LOOP
                CALL notify(bid_row.bidder, close_stamp, 
                    '[System] Auction #' || row.auction_id || ' is now closed. The winner was ' 
                    || row.name_winner || '.'
                );
            END LOOP;
        END IF;
    END LOOP;
END;
$$;

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

-- This trigger updates history on a auction's title or description insert/update
CREATE OR REPLACE FUNCTION hist_update() RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    id INTEGER;
BEGIN
    SELECT COUNT(*)+1 FROM history WHERE auction_id = NEW.auction_id
    INTO id;

    INSERT INTO history (auction_id, hist_id, hist_date, title, description) 
    VALUES (NEW.auction_id, id, CURRENT_TIMESTAMP, NEW.title, NEW.description);
    RETURN NEW;
END;
$$; 

DROP TRIGGER IF EXISTS hist_update ON auction;
CREATE TRIGGER hist_update AFTER INSERT OR UPDATE OF title, description ON auction
    FOR EACH ROW EXECUTE FUNCTION hist_update();

-- This trigger notifies the outbidded user
CREATE OR REPLACE FUNCTION outbidded() RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    new_bidder db_user.username%TYPE;
    id notifs.n_id%TYPE;
BEGIN
    IF old.last_bidder is NULL OR old.last_bidder = new.last_bidder THEN
        RETURN NEW;
    END IF;
    
    SELECT COUNT(*)+1 FROM notifs
    WHERE user_id = old.last_bidder
    INTO id;

    SELECT username FROM db_user
    WHERE user_id = new.last_bidder
    INTO new_bidder;

    INSERT INTO notifs (user_id, n_id, n_date, msg) VALUES (
        old.last_bidder, id, CURRENT_TIMESTAMP, 
        'User ' || new_bidder || ' outbid you in auction ' || new.auction_id
    );

    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS outbidded ON auction;
CREATE TRIGGER outbidded BEFORE UPDATE OF last_bidder ON auction
    FOR EACH ROW EXECUTE FUNCTION outbidded(); 

-- This trigger notifies seller and bidders when auction is cancelled
CREATE OR REPLACE FUNCTION cancelled() RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    cur CURSOR FOR
        SELECT DISTINCT bidder FROM bid
        WHERE auction_id = old.auction_id;
    auction_seller INTEGER;
    notify_date TIMESTAMP := CURRENT_TIMESTAMP;
BEGIN
    IF new.cancelled = false THEN
        RETURN NULL;
    END IF;

    SELECT seller INTO STRICT auction_seller FROM auction
    WHERE auction_id = new.auction_id;

    CALL notify(auction_seller, notify_date,
        '[System] Auction ' || old.auction_id || ' has been cancelled. Sorry for any inconvenience.'
    );

    FOR row IN cur LOOP
        IF row.bidder != auction_seller THEN
            CALL notify(row.bidder, notify_date,
                '[System] Auction ' || old.auction_id || ' has been cancelled. Sorry for any inconvenience.'
            );  
        END IF;
    END LOOP;

    RETURN NULL;
END;
$$;

DROP TRIGGER IF EXISTS cancelled on auction;
CREATE TRIGGER cancelled AFTER UPDATE OF cancelled ON auction
    FOR EACH ROW EXECUTE FUNCTION cancelled();

-- This trigger notifies users of new mural messages
CREATE OR REPLACE FUNCTION mural_notify() RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    cur CURSOR FOR
        SELECT DISTINCT user_id FROM mural
        WHERE auction_id = new.auction_id;
    auction_seller INTEGER;
    mural_user db_user.username%TYPE;
    notify_date TIMESTAMP := CURRENT_TIMESTAMP;
BEGIN
    SELECT seller INTO STRICT auction_seller FROM auction
    WHERE auction_id = new.auction_id;

    SELECT username INTO STRICT mural_user FROM db_user
    WHERE user_id = new.user_id;

    IF NOT auction_seller = new.user_id THEN
        CALL notify(auction_seller, notify_date,
            '[Auction # ' || new.auction_id || '] ' || mural_user || ': ' || new.msg
        );
    END IF;

    FOR row IN cur LOOP
        IF NOT row.user_id = auction_seller AND NOT row.user_id = new.user_id THEN 
            CALL notify(row.user_id, notify_date,
                '[Auction #' || new.auction_id || '] ' || mural_user || ': ' || new.msg
            );  
        END IF;
    END LOOP;

    RETURN NULL;
END;
$$;

DROP TRIGGER IF EXISTS  mural_notify ON mural;
CREATE TRIGGER mural_notify AFTER INSERT ON mural
    FOR EACH ROW EXECUTE FUNCTION mural_notify();
