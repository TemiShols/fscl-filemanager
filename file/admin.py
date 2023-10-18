from django.contrib import admin
from .models import Document


class DocumentAdmin(admin.ModelAdmin):
    list_display = ('uploaded_at', 'file', 'user')


admin.site.register(Document, DocumentAdmin)



