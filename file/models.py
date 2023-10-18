from django.db import models
from django.conf import settings


class Document(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    file = models.FileField(upload_to='uploads/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    name = models.CharField(max_length=120, null=True, blank=True)
    is_shared = models.BooleanField(default=False)

    def __str__(self):
        return self.name
