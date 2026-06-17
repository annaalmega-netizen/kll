-- =============================================================================
-- Аналитические функции
-- =============================================================================

-- ------------------------------------------------------------------
-- а) Загруженность станций за период по дням
--    Наименование | Дата | Макс. объём | Факт. объём | % загрузки
-- ------------------------------------------------------------------
CREATE OR REPLACE FUNCTION station_load_by_day(
    p_start DATE,
    p_end   DATE
)
RETURNS TABLE (
    station_name VARCHAR,
    work_date    DATE,
    max_volume   INTEGER,
    fact_volume  BIGINT,
    load_percent NUMERIC
)
LANGUAGE sql
AS $$
    SELECT s.name                                              AS station_name,
           b.booking_date                                      AS work_date,
           s.max_daily_capacity                                AS max_volume,
           SUM(b.wagons)                                       AS fact_volume,
           ROUND(SUM(b.wagons) * 100.0 / s.max_daily_capacity, 2) AS load_percent
      FROM bookings b
      JOIN stations s ON s.id = b.station_id
     WHERE b.booking_date BETWEEN p_start AND p_end
     GROUP BY s.id, s.name, s.max_daily_capacity, b.booking_date
     ORDER BY s.name, b.booking_date;
$$;

-- ------------------------------------------------------------------
-- б) Объём работы по станциям за период
--    Наименование | Макс. объём | Суммированный объём | Средний объём в сутки
-- ------------------------------------------------------------------
-- "Средний объём в сутки" считается по дням, в которые на станции были брони.
CREATE OR REPLACE FUNCTION station_work_volume(
    p_start DATE,
    p_end   DATE
)
RETURNS TABLE (
    station_name  VARCHAR,
    max_volume    INTEGER,
    total_volume  BIGINT,
    avg_per_day   NUMERIC
)
LANGUAGE sql
AS $$
    SELECT s.name                                              AS station_name,
           s.max_daily_capacity                                AS max_volume,
           SUM(b.wagons)                                       AS total_volume,
           ROUND(SUM(b.wagons)::NUMERIC / COUNT(DISTINCT b.booking_date), 2) AS avg_per_day
      FROM bookings b
      JOIN stations s ON s.id = b.station_id
     WHERE b.booking_date BETWEEN p_start AND p_end
     GROUP BY s.id, s.name, s.max_daily_capacity
     ORDER BY total_volume DESC;
$$;

-- ------------------------------------------------------------------
-- в) Рейтинг клиентов по стоимости работы за период
--    Название | Кол-во станций | Суммированный объём | Стоимость | Рейтинг (1 – макс. стоимость)
-- ------------------------------------------------------------------
CREATE OR REPLACE FUNCTION client_rating(
    p_start DATE,
    p_end   DATE
)
RETURNS TABLE (
    client_name    VARCHAR,
    stations_count BIGINT,
    total_volume   BIGINT,
    total_cost     BIGINT,
    rating         BIGINT
)
LANGUAGE sql
AS $$
    SELECT c.name                                       AS client_name,
           COUNT(DISTINCT b.station_id)                 AS stations_count,
           SUM(b.wagons)                                AS total_volume,
           SUM(b.cost)                                  AS total_cost,
           RANK() OVER (ORDER BY SUM(b.cost) DESC)      AS rating
      FROM bookings b
      JOIN clients c ON c.id = b.client_id
     WHERE b.booking_date BETWEEN p_start AND p_end
     GROUP BY c.id, c.name
     ORDER BY rating;
$$;
