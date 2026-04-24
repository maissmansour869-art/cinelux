from django.db import migrations


def add_postgres_constraints(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")
        cursor.execute("CREATE EXTENSION IF NOT EXISTS btree_gist;")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_movies_title_trgm ON movies USING gin (title gin_trgm_ops);")
        cursor.execute(
            """
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_constraint WHERE conname = 'no_hall_overlap'
                ) THEN
                    ALTER TABLE showtimes
                    ADD CONSTRAINT no_hall_overlap
                    EXCLUDE USING gist (
                        hall_id WITH =,
                        tstzrange(start_time, end_time, '[)') WITH &&
                    ) WHERE (is_active);
                END IF;
            END $$;
            """
        )


def drop_postgres_constraints(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("ALTER TABLE showtimes DROP CONSTRAINT IF EXISTS no_hall_overlap;")
        cursor.execute("DROP INDEX IF EXISTS idx_movies_title_trgm;")


class Migration(migrations.Migration):
    dependencies = [
        ("catalogues", "0002_initial"),
    ]

    operations = [
        migrations.RunPython(add_postgres_constraints, drop_postgres_constraints),
    ]
