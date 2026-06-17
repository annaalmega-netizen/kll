-- =============================================================================
-- Главный скрипт: разворачивает всё решение и запускает демонстрацию.
-- Запуск:  psql -d <база> -f run_all.sql
-- =============================================================================

\i schema.sql
\i procedures_crud.sql
\i procedures_work.sql
\i procedures_initdb_makejob.sql
\i functions_analytics.sql

-- 1. Первоначальное заполнение базы.
CALL initdb();

-- 2. Имитация рабочих операций.
CALL makejob();

-- 3. Аналитические отчёты за период имитации.
\echo '\n=== (а) Загруженность станций по дням ==='
SELECT * FROM station_load_by_day(CURRENT_DATE - 4, CURRENT_DATE);

\echo '\n=== (б) Объём работы по станциям за период ==='
SELECT * FROM station_work_volume(CURRENT_DATE - 4, CURRENT_DATE);

\echo '\n=== (в) Рейтинг клиентов по стоимости работы за период ==='
SELECT * FROM client_rating(CURRENT_DATE - 4, CURRENT_DATE);
