import asyncio
from .mistral_util import summarize_content, analyze_content
from .models import Document


def get_document(pk):
    return Document.objects.get(pk=pk)


def save_document_summary(doc_id, summary):
    doc = Document.objects.get(id=doc_id)
    doc.summary = summary
    doc.save()


def summarize_and_save(doc_id):
    doc = get_document(doc_id)
    content = doc.content
    summary = summarize_content(content)
    return save_document_summary(doc_id, summary)


def analyse_and_save(doc_id):
    doc = get_document(doc_id)
    content = doc.content
    summary = analyze_content(content)
    return save_document_summary(doc_id, summary)
