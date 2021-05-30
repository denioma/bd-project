CREATE OR REPLACE PROCEDURE reset_murals()
LANGUAGE plpgsql
AS $$
DECLARE
BEGIN
    TRUNCATE TABLE mural;
    ALTER SEQUENCE mural_m_id_seq RESTART WITH 1;
END;
$$;

CREATE OR REPLACE PROCEDURE clear_notifs()
LANGUAGE plpgsql
AS $$
DECLARE
BEGIN
    TRUNCATE TABLE notifs;
END;
$$;