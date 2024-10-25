from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
import hashlib
import time
import re
from datetime import datetime


# Função para gerar um nome de arquivo aleatório
def random_filename(instance, filename: str) -> str:
    # Extrai a extensão do arquivo
    ext = filename.split(".")[-1]
    # Usa o timestamp atual e o nome original para gerar o hash simples
    hash_object = hashlib.md5(f"{filename}{time.time()}".encode("utf-8"))
    return f"{hash_object.hexdigest()}.{ext}"


def validate_no_special_characters(value: str):
    print(f"Argumento: {value}")
    # Permitir letras, números, espaços, acentos, e algumas pontuações
    # Adicionei essa função pois um dos testes falhou
    if re.search(r"[<>;]", value):
        print(f"Argumento inválido: {value}")
        raise ValidationError(
            "O campo não deve conter caracteres especiais como '<', '>', ou ';'."
        )
    if not re.match(
        r"^[\w\s!\"#$%&'()*+,-./:;<=>?@[\\\]^\_`{|}~áéíóúãâêîôûäëïöü]+$", value
    ):
        print(f"Argumento inválido: {value}")
        raise ValidationError(
            "O campo só pode conter letras, números, espaços e pontuação comum."
        )


def validate_file_path(value: str):
    print(f"Argumento: {value}")
    if not re.match(r"^[\w\-/\.]+$", value):
        print(f"Argumento inválido: {value}")
        raise ValidationError(
            "O campo vídeo deve conter apenas letras, números, underscores, hífens, barras e pontos."
        )


# Create your models here.
class Video(models.Model):
    title: str = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Título",
        validators=[validate_no_special_characters],
    )
    description: str = models.TextField(
        verbose_name="Descrição", validators=[validate_no_special_characters]
    )
    thumbnail: str = models.ImageField(
        upload_to=random_filename, verbose_name="Thumbnail"
    )
    slug: str = models.SlugField(
        unique=True, validators=[validate_no_special_characters]
    )
    published_at: datetime = models.DateTimeField(
        verbose_name="Publicado em", null=True, editable=False
    )
    is_published: bool = models.BooleanField(default=False, verbose_name="Publicado")
    num_likes: int = models.IntegerField(
        default=0, verbose_name="Likes", editable=False
    )
    num_views: int = models.IntegerField(
        default=0, verbose_name="Visualizações", editable=False
    )
    tags = models.ManyToManyField("Tag", verbose_name="Tags", related_name="videos")
    author = models.ForeignKey(
        "auth.User",
        on_delete=models.PROTECT,
        verbose_name="Autor",
        related_name="videos",
        editable=False,
    )

    def save(
        self,
        force_insert=False,
        force_update=False,
        using=None,
        update_fields=None,
    ):
        if self.is_published and not self.published_at:
            self.published_at = timezone.now()
        return super().save(force_insert, force_update, using, update_fields)

    def clean(self):
        if self.is_published:
            if not hasattr(self, "video_media"):
                raise ValidationError("O vídeo não possui mídia associada.")
            if self.video_media.status != VideoMedia.Status.PROCESS_FINISHED:
                raise ValidationError("O vídeo não foi processado.")

    def get_video_status_display(self):
        if not hasattr(self, "video_media"):
            return "Pendente"
        return self.video_media.get_status_display()

    class Meta:
        verbose_name: str = "Vídeo"
        verbose_name_plural: str = "Vídeos"

    def __str__(self):
        return self.title


class VideoMedia(models.Model):

    class Status(models.TextChoices):
        UPLOADED_STARTED = "UPLOADED_STARTED", "Upload Iniciado"
        PROCESS_STARTED = "PROCESSING_STARTED", "Processamento Iniciado"
        PROCESS_FINISHED = "PROCESSING_FINISHED", "Processamento Finalizado"
        PROCESS_ERROR = "PROCESSING_ERROR", "Erro no Processamento"

    video_path: str = models.CharField(
        max_length=255,
        verbose_name="Vídeo",
        validators=[validate_file_path],
    )
    status: str = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.UPLOADED_STARTED,
        verbose_name="Status",
    )
    video = models.OneToOneField(
        "Video",
        on_delete=models.PROTECT,
        verbose_name="Vídeo",
        related_name="video_media",
    )

    def get_status_display(self):
        return VideoMedia.Status(self.status).label

    class Media:
        verbose_name: str = "Mídia"
        verbose_name_plural: str = "Mídias"


class Tag(models.Model):
    name: str = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Nome",
        validators=[validate_no_special_characters],
    )

    class Meta:
        verbose_name: str = "Tag"
        verbose_name_plural: str = "Tags"

    def __str__(self):
        return self.name
