"""Abstract building blocks shared by every RMI app.

- TimeStampedModel: created_at / updated_at on everything (D5).
- SoftDeleteModel:  editorial content is archived, never hard-deleted (D6).
"""

from django.db import models
from django.utils import timezone


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class SoftDeleteQuerySet(models.QuerySet):
    def delete(self):
        return self.update(archived_at=timezone.now())

    def hard_delete(self):
        return super().delete()

    def active(self):
        return self.filter(archived_at__isnull=True)

    def archived(self):
        return self.filter(archived_at__isnull=False)


class ActiveManager(models.Manager.from_queryset(SoftDeleteQuerySet)):
    """Default manager: hides archived rows."""

    def get_queryset(self):
        return super().get_queryset().filter(archived_at__isnull=True)


class SoftDeleteModel(models.Model):
    archived_at = models.DateTimeField(null=True, blank=True, db_index=True, editable=False)

    objects = ActiveManager()
    all_objects = models.Manager.from_queryset(SoftDeleteQuerySet)()

    class Meta:
        abstract = True

    @property
    def is_archived(self) -> bool:
        return self.archived_at is not None

    def delete(self, using=None, keep_parents=False):
        self.archived_at = timezone.now()
        self.save(update_fields=["archived_at"])

    def restore(self):
        self.archived_at = None
        self.save(update_fields=["archived_at"])

    def hard_delete(self, using=None, keep_parents=False):
        return super().delete(using=using, keep_parents=keep_parents)
