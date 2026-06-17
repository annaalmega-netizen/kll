-- =============================================================================
-- Автоматизация работы оператора грузоперевозок (ж/д транспорт)
-- =============================================================================
-- Назначение файла: проектирование и создание структуры БД.
--
-- Предметная область:
--   * Клиенты (фирмы) заранее бронируют вагоны на грузовых станциях.
--   * Каждая станция может обработать ограниченное число вагонов в сутки.
--   * Бронирование невозможно при превышении суточного лимита станции
--     или при нехватке денежных средств у клиента.
--   * Информация о проведённых операциях сохраняется (таблица bookings).
-- =============================================================================

-- Порядок удаления важен из-за внешних ключей.
DROP TABLE IF EXISTS bookings CASCADE;
DROP TABLE IF EXISTS clients  CASCADE;
DROP TABLE IF EXISTS stations CASCADE;

-- ------------------------------------------------------------------
-- Станции
-- ------------------------------------------------------------------
CREATE TABLE stations (
    id                 SERIAL       PRIMARY KEY,
    name               VARCHAR(50)  NOT NULL,                 -- Наименование
    max_daily_capacity INTEGER      NOT NULL,                 -- Макс. суточный объём работы, ваг.
    cost_per_wagon     INTEGER      NOT NULL,                 -- Стоимость отправки 1 вагона, руб.
    CONSTRAINT stations_capacity_positive CHECK (max_daily_capacity > 0),
    CONSTRAINT stations_cost_positive     CHECK (cost_per_wagon    > 0)
);

-- ------------------------------------------------------------------
-- Клиенты
-- ------------------------------------------------------------------
CREATE TABLE clients (
    id      SERIAL       PRIMARY KEY,
    name    VARCHAR(50)  NOT NULL,                            -- Название
    balance INTEGER      NOT NULL,                            -- Баланс денежных средств, руб.
    CONSTRAINT clients_balance_nonnegative CHECK (balance >= 0)
);

-- ------------------------------------------------------------------
-- Бронирования (журнал проведённых рабочих операций)
-- ------------------------------------------------------------------
-- Хранит историю успешных бронирований. Используется как для контроля
-- суточного лимита станции, так и для построения аналитических отчётов.
CREATE TABLE bookings (
    id           SERIAL  PRIMARY KEY,
    station_id   INTEGER NOT NULL REFERENCES stations(id) ON DELETE CASCADE,
    client_id    INTEGER NOT NULL REFERENCES clients(id)  ON DELETE CASCADE,
    booking_date DATE    NOT NULL,                           -- Дата брони
    wagons       INTEGER NOT NULL,                           -- Кол-во забронированных вагонов
    cost         INTEGER NOT NULL,                           -- Итоговая стоимость, руб.
    CONSTRAINT bookings_wagons_positive CHECK (wagons > 0),
    CONSTRAINT bookings_cost_positive   CHECK (cost   > 0)
);

CREATE INDEX idx_bookings_station_date ON bookings (station_id, booking_date);
CREATE INDEX idx_bookings_client       ON bookings (client_id);
