-- =============================================================================
-- Рабочие операции: бронирование и пополнение баланса
-- =============================================================================

-- ------------------------------------------------------------------
-- Пополнение баланса клиента
-- ------------------------------------------------------------------
CREATE OR REPLACE PROCEDURE top_up_balance(
    p_client_id INTEGER,
    p_amount    INTEGER
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_name        clients.name%TYPE;
    v_new_balance INTEGER;
BEGIN
    IF p_amount <= 0 THEN
        RAISE INFO 'Пополнение отменено: сумма должна быть положительной (получено %).', p_amount;
        RETURN;
    END IF;

    UPDATE clients
       SET balance = balance + p_amount
     WHERE id = p_client_id
    RETURNING name, balance INTO v_name, v_new_balance;

    IF NOT FOUND THEN
        RAISE INFO 'Пополнение отменено: клиент [id=%] не найден.', p_client_id;
        RETURN;
    END IF;

    RAISE INFO 'Баланс клиента "%" пополнен на % руб. Текущий баланс=% руб.',
        v_name, p_amount, v_new_balance;
END;
$$;

-- ------------------------------------------------------------------
-- Бронирование вагонов на станции
-- ------------------------------------------------------------------
-- Ограничения:
--   1) Суммарный объём броней станции за сутки не должен превышать
--      суточный лимит станции (max_daily_capacity).
--   2) Баланса клиента должно хватать на оплату (wagons * cost_per_wagon).
-- При нарушении любого ограничения операция отменяется с сообщением.
CREATE OR REPLACE PROCEDURE book_capacity(
    p_station_id   INTEGER,
    p_client_id    INTEGER,
    p_wagons       INTEGER,
    p_booking_date DATE DEFAULT CURRENT_DATE
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_station    stations%ROWTYPE;
    v_client     clients%ROWTYPE;
    v_used       INTEGER;
    v_free       INTEGER;
    v_cost       INTEGER;
BEGIN
    IF p_wagons <= 0 THEN
        RAISE INFO 'Бронь отменена: число вагонов должно быть положительным (получено %).', p_wagons;
        RETURN;
    END IF;

    -- Блокируем строки, чтобы корректно посчитать суточный остаток при конкурентном доступе.
    SELECT * INTO v_station FROM stations WHERE id = p_station_id FOR UPDATE;
    IF NOT FOUND THEN
        RAISE INFO 'Бронь отменена: станция [id=%] не найдена.', p_station_id;
        RETURN;
    END IF;

    SELECT * INTO v_client FROM clients WHERE id = p_client_id FOR UPDATE;
    IF NOT FOUND THEN
        RAISE INFO 'Бронь отменена: клиент [id=%] не найден.', p_client_id;
        RETURN;
    END IF;

    -- Ограничение 1: суточный лимит станции.
    SELECT COALESCE(SUM(wagons), 0) INTO v_used
      FROM bookings
     WHERE station_id = p_station_id
       AND booking_date = p_booking_date;

    v_free := v_station.max_daily_capacity - v_used;

    IF p_wagons > v_free THEN
        RAISE INFO 'Бронь отменена: на станции "%" на % осталось % ваг. (запрошено %).',
            v_station.name, p_booking_date, v_free, p_wagons;
        RETURN;
    END IF;

    -- Ограничение 2: баланс клиента.
    v_cost := p_wagons * v_station.cost_per_wagon;

    IF v_cost > v_client.balance THEN
        RAISE INFO 'Бронь отменена: у клиента "%" недостаточно средств (нужно % руб., доступно % руб.).',
            v_client.name, v_cost, v_client.balance;
        RETURN;
    END IF;

    -- Все ограничения выполнены: проводим операцию.
    UPDATE clients SET balance = balance - v_cost WHERE id = p_client_id;

    INSERT INTO bookings (station_id, client_id, booking_date, wagons, cost)
    VALUES (p_station_id, p_client_id, p_booking_date, p_wagons, v_cost);

    RAISE INFO 'Бронь проведена: клиент "%" забронировал % ваг. на станции "%" (%). Стоимость=% руб., остаток баланса=% руб.',
        v_client.name, p_wagons, v_station.name, p_booking_date, v_cost, v_client.balance - v_cost;
END;
$$;
