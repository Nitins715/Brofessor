from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.core"
    label = "core"

    def ready(self):
        """Ensure Postgres-specific indexes don't crash SQLite migrations."""
        try:
            from django.contrib.postgres.indexes import PostgresIndex
            from django.db.backends.ddl_references import Statement

            orig_create_sql = PostgresIndex.create_sql
            orig_remove_sql = PostgresIndex.remove_sql

            def safe_create_sql(self, model, schema_editor, using="", **kwargs):
                if schema_editor.connection.vendor != "postgresql":
                    return Statement("")
                return orig_create_sql(self, model, schema_editor, using=using, **kwargs)

            def safe_remove_sql(self, model, schema_editor, **kwargs):
                if schema_editor.connection.vendor != "postgresql":
                    return Statement("")
                return orig_remove_sql(self, model, schema_editor, **kwargs)

            PostgresIndex.create_sql = safe_create_sql
            PostgresIndex.remove_sql = safe_remove_sql
        except Exception:
            pass

