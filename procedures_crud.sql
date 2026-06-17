-- =============================================================================
-- Процедуры создания, изменения и удаления объектов
-- =============================================================================
-- Правило: одна процедура выполняет одно действие с одним объектом.
-- О каждой операции сообщается через RAISE INFO.
-- =============================================================================

-- ------------------------------------------------------------------
-- СТАНЦИИ: создание / изменение / удаление
-- ------------------------------------------------------------------

CREATE OR REPLACE PROCEDURE add_station(
    p_name               VARCHAR,
    p_max_daily_capacity INTEGER,
    p_cost_per_wagon     INTEGER
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_id INTEGER;
BEGIN
    INSERT INTO stations (name, max_daily_capacity, cost_per_wagon)
    VALUES (p_name, p_max_daily_capacity, p_cost_per_wagon)
    RETURNING id INTO v_id;

    RAISE INFO 'Добавлена станция [id=%]: "%", суточный лимит=% ваг., стоимость=% руб./ваг.',
        v_id, p_name, p_max_daily_capacity, p_cost_per_wagon;
END;
$$;

CREATE OR REPLACE PROCEDURE update_station(
    p_id                 INTEGER,
    p_name               VARCHAR,
    p_max_daily_capacity INTEGER,
    p_cost_per_wagon     INTEGER
)
LANGUAGE plpgsql
AS $$
BEGIN
    UPDATE stations
       SET name               = p_name,
           max_daily_capacity = p_max_daily_capacity,
           cost_per_wagon     = p_cost_per_wagon
     WHERE id = p_id;

    IF NOT FOUND THEN
        RAISE INFO 'Изменение отменено: станция [id=%] не найдена.', p_id;
        RETURN;
    END IF;

    RAISE INFO 'Изменена станция [id=%]: "%", суточный лимит=% ваг., стоимость=% руб./ваг.',
        p_id, p_name, p_max_daily_capacity, p_cost_per_wagon;
END;
$$;

CREATE OR REPLACE PROCEDURE delete_station(p_id INTEGER)
LANGUAGE plpgsql
AS $$
DECLARE
    v_name stations.name%TYPE;
BEGIN
    DELETE FROM stations
     WHERE id = p_id
    RETURNING name INTO v_name;

    IF NOT FOUND THEN
        RAISE INFO 'Удаление отменено: станция [id=%] не найдена.', p_id;
        RETURN;
    END IF;

    RAISE INFO 'Удалена станция [id=%]: "%".', p_id, v_name;
END;
$$;

-- ------------------------------------------------------------------
-- КЛИЕНТЫ: создание / изменение / удаление
-- ------------------------------------------------------------------

CREATE OR REPLACE PROCEDURE add_client(
    p_name    VARCHAR,
    p_balance INTEGER
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_id INTEGER;
BEGIN
    INSERT INTO clients (name, balance)
    VALUES (p_name, p_balance)
    RETURNING id INTO v_id;

    RAISE INFO 'Добавлен клиент [id=%]: "%", баланс=% руб.',
        v_id, p_name, p_balance;
END;
$$;

CREATE OR REPLACE PROCEDURE update_client(
    p_id      INTEGER,
    p_name    VARCHAR,
    p_balance INTEGER
)
LANGUAGE plpgsql
AS $$
BEGIN
    UPDATE clients
       SET name    = p_name,
           balance = p_balance
     WHERE id = p_id;

    IF NOT FOUND THEN
        RAISE INFO 'Изменение отменено: клиент [id=%] не найден.', p_id;
        RETURN;
    END IF;

    RAISE INFO 'Изменён клиент [id=%]: "%", баланс=% руб.',
        p_id, p_name, p_balance;
END;
$$;

CREATE OR REPLACE PROCEDURE delete_client(p_id INTEGER)
LANGUAGE plpgsql
AS $$
DECLARE
    v_name clients.name%TYPE;
BEGIN
    DELETE FROM clients
     WHERE id = p_id
    RETURNING name INTO v_name;

    IF NOT FOUND THEN
        RAISE INFO 'Удаление отменено: клиент [id=%] не найден.', p_id;
        RETURN;
    END IF;

    RAISE INFO 'Удалён клиент [id=%]: "%".', p_id, v_name;
END;
$$;
