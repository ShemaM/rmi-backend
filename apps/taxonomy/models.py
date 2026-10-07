from django.db import models

from apps.core.models import ActiveManager, SoftDeleteModel, SoftDeleteQuerySet, TimeStampedModel


class Region(SoftDeleteModel, TimeStampedModel):
    objects = ActiveManager()
    all_objects = models.Manager.from_queryset(SoftDeleteQuerySet)()

    code = models.CharField(max_length=32, unique=True)
    name = models.CharField(max_length=150)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return f"{self.name} ({self.code})"


class Country(SoftDeleteModel, TimeStampedModel):
    objects = ActiveManager()
    all_objects = models.Manager.from_queryset(SoftDeleteQuerySet)()

    code = models.CharField(max_length=2, unique=True)
    name = models.CharField(max_length=150)
    region = models.ForeignKey(
        Region, on_delete=models.PROTECT, related_name="countries"
    )

    class Meta:
        ordering = ["name"]

    def save(self, *args, **kwargs):
        self.code = self.code.upper().strip()
        self.name = self.name.strip()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.name} ({self.code})"


class Theme(SoftDeleteModel, TimeStampedModel):
    objects = ActiveManager()
    all_objects = models.Manager.from_queryset(SoftDeleteQuerySet)()

    slug = models.SlugField(max_length=100, unique=True)
    name_en = models.CharField(max_length=150)
    name_fr = models.CharField(max_length=150, blank=True)
    description_en = models.TextField(blank=True)
    description_fr = models.TextField(blank=True)

    class Meta:
        ordering = ["name_en"]

    def __str__(self) -> str:
        return self.name_en
