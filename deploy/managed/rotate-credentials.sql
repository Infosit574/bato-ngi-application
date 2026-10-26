DO $$
BEGIN
  EXECUTE format('ALTER ROLE postgres PASSWORD %L',
                 rtrim(pg_read_file('/run/bato/db-password'), E'\n'));
  EXECUTE format('ALTER ROLE bato_api PASSWORD %L',
                 rtrim(pg_read_file('/run/bato/api-password'), E'\n'));
END
$$;
