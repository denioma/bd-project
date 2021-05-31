-- Databases - 2020/2021
-- Final Project - Useful procedures in PL/pgSQL

-- Authors:
--   David Valente Pereira Barros Leitão - 2019223148
--   João António Correia Vaz - 2019218159
--   Rodrigo Alexandre da Mota Machado - 2019218299
----------------------------------------------------------------------

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

CREATE OR REPLACE PROCEDURE make_admin(v_user INTEGER)
LANGUAGE plpgsql
AS $$
DECLARE
BEGIN
    UPDATE db_user SET admin = true WHERE user_id = v_user;
END;
$$;