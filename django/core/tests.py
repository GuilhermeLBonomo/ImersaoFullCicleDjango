from django.test import TestCase
from django.db import connection
from django.contrib.auth.models import User
from django.utils.text import slugify
from docker import from_env
from psycopg2 import connect, Error
from django.db.utils import IntegrityError
from django.conf import settings
from os import getenv
from django.urls import reverse
from re import compile, IGNORECASE
from .models import Tag, Video, VideoMedia


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
            # print(container.name)
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
            # print(container.name)
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


class TagCRUDTest(TestCase):
    def setUp(self):
        self.tag = Tag.objects.create(name="Matemática")

    def test_create_tag(self):
        TAMANHO = Tag.objects.all().count()
        tag = Tag.objects.create(name="Tecnologia da Informação")
        self.assertEqual(tag.name, "Tecnologia da Informação")
        self.assertEqual(Tag.objects.all().count(), TAMANHO + 1)

    def test_read_tag(self):
        tag = Tag.objects.get(name="Matemática")
        self.assertEqual(tag.name, "Matemática")

    def test_update_tag(self):
        TAMANHO = Tag.objects.all().count()
        self.tag.name = "Ciência"
        self.tag.save()
        updated_tag = Tag.objects.get(id=self.tag.id)
        self.assertEqual(updated_tag.name, "Ciência")
        self.assertNotEqual(updated_tag.name, "Matemática")
        self.assertEqual(Tag.objects.all().count(), TAMANHO)

    def test_delete_tag(self):
        TAMANHO = Tag.objects.all().count()
        self.tag.delete()
        with self.assertRaises(Tag.DoesNotExist):
            Tag.objects.get(id=self.tag.id)
        self.assertEqual(Tag.objects.all().count(), TAMANHO - 1)

    def tearDown(self):
        Tag.objects.all().delete()


class VideoCRUDTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="Bob", password="SenhaTesteBob123$"
        )
        self.video = Video.objects.create(
            title="Aprendizado de Máquina",
            description="Introdução ao aprendizado de máquina.",
            slug=slugify("Aprendizado de Máquina"),
            author=self.user,
        )

    def test_create_video(self):
        TAMANHO = Video.objects.all().count()
        video = Video.objects.create(
            title="Deep Learning",
            description="Uma introdução ao deep learning.",
            slug=slugify("Deep Learning"),
            author=self.user,
        )
        self.assertEqual(video.title, "Deep Learning")
        self.assertEqual(Video.objects.all().count(), TAMANHO + 1)

    def test_read_video(self):
        video = Video.objects.get(title="Aprendizado de Máquina")
        self.assertEqual(video.description, "Introdução ao aprendizado de máquina.")

    def test_update_video(self):
        TAMANHO = Video.objects.all().count()
        self.video.title = "Machine Learning Avançado"
        self.video.save()
        updated_video = Video.objects.get(id=self.video.id)
        self.assertEqual(updated_video.title, "Machine Learning Avançado")
        self.assertNotEqual(updated_video.title, "Aprendizado de Máquina")
        self.assertEqual(Video.objects.all().count(), TAMANHO)

    def test_delete_video(self):
        TAMANHO = Video.objects.all().count()
        self.video.delete()
        with self.assertRaises(Video.DoesNotExist):
            Video.objects.get(id=self.video.id)
        self.assertEqual(Video.objects.all().count(), TAMANHO - 1)

    def tearDown(self):
        Video.objects.all().delete()
        User.objects.all().delete()


class VideoMediaCRUDTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="autor", password="12345")
        self.video = Video.objects.create(
            title="Data Science",
            description="Introdução à ciência de dados.",
            slug=slugify("Data Science"),
            author=self.user,
        )
        self.video_media = VideoMedia.objects.create(
            video_path=r"videos/datascience.mp4",
            status=VideoMedia.Status.UPLOADED_STARTED,
            video=self.video,
        )

    def test_create_video_media(self):
        TAMANHO = VideoMedia.objects.all().count()
        new_video = Video.objects.create(
            title="Big Data",
            description="Análise de grandes volumes de dados.",
            slug=slugify("Big Data"),
            author=self.user,
        )
        video_media = VideoMedia.objects.create(
            video_path=r"videos/bigdata.mp4",
            status=VideoMedia.Status.PROCESS_FINISHED,
            video=new_video,
        )
        self.assertEqual(video_media.status, VideoMedia.Status.PROCESS_FINISHED)
        self.assertEqual(VideoMedia.objects.all().count(), TAMANHO + 1)

    def test_read_video_media(self):
        video_media = VideoMedia.objects.get(video=self.video)
        self.assertEqual(video_media.video_path, r"videos/datascience.mp4")

    def test_update_video_media(self):
        TAMANHO = VideoMedia.objects.all().count()
        self.video_media.status = VideoMedia.Status.PROCESS_FINISHED
        self.video_media.save()
        updated_media = VideoMedia.objects.get(id=self.video_media.id)
        self.assertEqual(updated_media.status, VideoMedia.Status.PROCESS_FINISHED)
        self.assertNotEqual(updated_media.status, VideoMedia.Status.UPLOADED_STARTED)
        self.assertEqual(VideoMedia.objects.all().count(), TAMANHO)

    def test_delete_video_media(self):
        TAMANHO = VideoMedia.objects.all().count()
        self.video_media.delete()
        with self.assertRaises(VideoMedia.DoesNotExist):
            VideoMedia.objects.get(id=self.video_media.id)
        self.assertEqual(VideoMedia.objects.all().count(), TAMANHO - 1)

    def tearDown(self):
        VideoMedia.objects.all().delete()
        Video.objects.all().delete()
        User.objects.all().delete()


class SQLInjectionTest1(TestCase):

    def test_sql_injection_in_tag_name(self):
        malicious_input = r"Matemática'; DROP TABLE Tag; --"

        try:
            Tag.objects.create(name=malicious_input)
            self.fail(
                "Tag was created despite SQL injection attempt, indicating a vulnerability."
            )
            tag_injected = Tag.objects.get(name=malicious_input)
            self.assertEqual(tag_injected.name, malicious_input)
        except IntegrityError:
            #  A criação da tag deve falhar, o que é esperado
            pass
        except Exception as e:
            self.assertNotIn(
                "DROP TABLE", str(e), "SQL Injection vulnerability detected"
            )
        self.assertTrue(
            Tag.objects.filter(name=malicious_input).exists(),
            f"The original tag '{malicious_input}' does not exist after SQL injection attempt.",
        )

    def tearDown(self):
        # Caso ele crie mas não drope a tabela
        Tag.objects.all().delete()


class SQLInjectionTest2(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="TestUser", password="testpassword35345$!"
        )

    def test_sql_injection_in_video_title(self):
        malicious_input = r"Tutorial de LOL'; SHUTDOWN; --"

        try:
            video = Video.objects.create(
                title=malicious_input,
                description="Uma introdução ao deep learning.",
                slug=slugify("Deep Learning"),
                author=self.user,
            )
            self.fail(
                "Video was created despite SQL injection attempt, indicating a vulnerability."
            )
        except IntegrityError:
            pass
        except Exception as e:
            self.assertNotIn("SHUTDOWN", str(e), "SQL Injection vulnerability detected")

        video_injected = Video.objects.get(title=malicious_input)
        self.assertEqual(video_injected.title, malicious_input)

    def tearDown(self):
        Video.objects.all().delete()

