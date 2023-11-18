from django.core.exceptions import PermissionDenied
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseBadRequest
from file.utils import summarize_doc
from django.http import HttpResponse
from django.http import JsonResponse
from .models import Document
import os, json
from .forms import DocumentForm
from django.contrib import messages
from authentication.models import CustomUser
from django.core.cache import cache
from .tasks import send_simple_download_message, send_simple_share_message
from django.contrib.auth.decorators import login_required
from django.core.serializers.json import DjangoJSONEncoder


@login_required()
def upload_file(request):
    if request.method == 'POST':
        uploaded_file = request.FILES.get('file')
        if uploaded_file is not None and uploaded_file.name:  # Check if the file is not None and has a name
            file_name = uploaded_file.name
            Document.objects.create(file=uploaded_file, name=file_name, user=request.user)
            #   path = default_storage.save(file_name, uploaded_file)
            messages.success(request, 'File uploaded successfully')
            return redirect('files')  # Redirect to the appropriate URL after successful upload
        else:
            messages.error(request, 'No file is uploaded. Please ensure you have uploaded a file.')
            return redirect('upload')  # Redirect back to the upload page if no file is uploaded
    return render(request, 'files.html')


@login_required()
def list_files(request):
    files = Document.objects.filter(user=request.user.id)
    context = {
        'files':
            files
    }
    return render(request, 'my_files.html', context)
    #   if request.user.is_admin:
    #   files = DocumentFilter(request.GET, queryset=Document.objects.all())
    #   return render(request, 'my_files.html', {'files': files})
    #   else:
    #   files = DocumentFilter(request.GET, queryset=Document.objects.filter(user=request.user.id))
    #   return render(request, 'my_files.html', {'files': files})


@login_required()
def filter_documents(request):
    try:
        company_name = request.POST['company']
        file_name = request.POST['name']
    except KeyError:
        return HttpResponseBadRequest('Invalid parameters')

    files = Document.objects.filter(user=request.user, name=file_name).select_related('user')
    context = {
        'files':
            files
    }
    return render(request, 'my_files.html', context)


@login_required()
def download_file(request, pk):
    receiver = CustomUser.objects.get(pk=request.user.pk)
    doc = Document.objects.get(pk=pk)
    #   file_content = default_storage.open(doc.name)
    context_data = {
        'doc_name': doc.name,
        'sender_name': doc.user.get_full_name(),
    }
    context_json = json.dumps(context_data, cls=DjangoJSONEncoder)
    send_simple_download_message.delay(doc.pk, context_json)
    response = HttpResponse(doc, content_type='application/octet-stream')
    response['Content-Disposition'] = f'attachment; filename="{doc.name}"'
    return response


@login_required()
def share_file(request, pk):
    doc = get_object_or_404(Document, pk=pk)
    doc.is_shared = True
    doc.save()
    context_data = {
        'doc_name': doc.name,
        #   'file_url': request.build_absolute_uri(doc.file.url),
        'file_url': 'http://127.0.0.1:8000/shared/{}'.format(doc.pk),
        'sender_name': doc.user.get_full_name(),
        'company_name': doc.user.company_name,
    }
    context_json = json.dumps(context_data, cls=DjangoJSONEncoder)
    if request.method == 'POST':
        response_data = {
            'success': True,
            'message': 'File shared successfully'
        }
        recipient_email = request.POST.get('recipient_email')
        send_simple_share_message.delay(request.user.pk, recipient_email, context_json)
        json_response_data = json.dumps(response_data)
        return JsonResponse(json_response_data, safe=False)
    return JsonResponse({'success': False, 'message': 'Invalid request'})


@login_required()
def all_shared_files(request):
    files = Document.objects.filter(is_shared=True, user=request.user).select_related('user')
    context = {
        'files':
            files}
    return render(request, 'my_files.html', context)


@login_required()
def shared_file(request, pk):
    if request.method == 'GET':
        file = Document.objects.get(pk=pk)
        context = {
            'file': file,
        }
        return render(request, 'shared_file.html', context)
    return PermissionDenied


@login_required()
def summarize(request, pk):
    text = request.GET.get('text', '')
    document = Document.objects.get(pk=pk)
    cache_key = f'summarized_text:{text}'  # Use the text as part of the cache key

    # Try to get summarized text from cache
    summarized_text = cache.get(cache_key)
    print('Gotten from cache....{}'.format(summarized_text))

    if summarized_text is None:
        summarized_text = summarize_doc(document.file)
        # Cache the summarized text for 30 seconds
        cache.set(cache_key, summarized_text, 30)
        print('Gotten from api....{}'.format(summarized_text))

    context = {
        'summarized_text': summarized_text,
    }

    return render(request, 'summarize.html', context)

#   def get_files(request):
#       files = Document.objects.filter(user=request.user)
#       data = []
#       for file in files:
#           data.append({
#               'id': file.id,
#               'name': file.name,
#               'url': file.file.url,
#               'type': file.file.name.split('.')[-1].lower()  # Extract file type (pdf, excel, etc.)
#           })
#    return JsonResponse({'files': data})
