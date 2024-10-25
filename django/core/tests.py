from django.test import TestCase
from django.db import connection
from docker import from_env
from psycopg2 import connect, Error
from django.conf import settings
from os import getenv
from re import compile, IGNORECASE


class EnvVariablesTest(TestCase):

    def test_env_variables_loaded(self):
        self.assertTrue(getenv("POSTGRES_PASSWORD"), "POSTGRES_PASSWORD is not set")
        self.assertTrue(getenv("POSTGRES_DB"), "POSTGRES_DB is not set")
        self.assertTrue(
            getenv("PGADMIN_DEFAULT_EMAIL"), "PGADMIN_DEFAULT_EMAIL is not set"
        )
        self.assertTrue(
            getenv("PGADMIN_DEFAULT_PASSWORD"), "PGADMIN_DEFAULT_PASSWORD is not set"
        )


class DockerPostgresTest(TestCase):
    def setUp(self):
        self.client = from_env()

    def test_postgres_container_running(self):
        postgres_container = None
        pattern = compile(r"(postgres|\.?django-db-1)", IGNORECASE)

        for container in self.client.containers.list():
            #print(container.name)
            if pattern.search(container.name):
                postgres_container = container
                break

        self.assertIsNotNone(postgres_container, "Postgres container is not running")
        self.assertTrue(
            postgres_container.status == "running", "Postgres container is not running"
        )

    def test_pgadmin_container_running(self):
        pgadmin_container = None
        pattern = compile(r"(pgadmin|\.?django-pgadmin-1)", IGNORECASE)

        for container in self.client.containers.list():
            #print(container.name)
            if pattern.search(container.name):
                pgadmin_container = container
                break

        self.assertIsNotNone(pgadmin_container, "PgAdmin container is not running")
        self.assertTrue(
            pgadmin_container.status == "running", "PgAdmin container is not running"
        )


class DatabaseConnectionTest(TestCase):

    def test_can_connect_to_database(self):
        try:
            connection.ensure_connection()
            self.assertTrue(connection.is_usable())
        except Exception as e:
            self.fail(f"Database connection failed: {str(e)}")


class PostgresAuthTest(TestCase):

    def test_user_authentication(self):
        try:
            conn = connect(
                dbname=settings.DATABASES["default"]["NAME"],
                user=settings.DATABASES["default"]["USER"],
                password=settings.DATABASES["default"]["PASSWORD"],
                host=settings.DATABASES["default"]["HOST"],
                port=settings.DATABASES["default"]["PORT"],
            )
            conn.close()

        except Error as e:
            self.fail(f"Database connection failed: {str(e)}")

        except Exception as e:
            self.fail(f"Database connection failed, unknown error: {str(e)}")
