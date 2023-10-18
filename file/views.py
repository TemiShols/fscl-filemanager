from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseBadRequest
from django.core.files.storage import default_storage
from django.db.models import Q
from django.http import HttpResponse
from django.http import JsonResponse
from .models import Document
from django.core.exceptions import PermissionDenied
import os
from django.contrib import messages
from authentication.models import CustomUser
from .tasks import share_file_task, file_share, new_share, share, share_brevo, share_brevo2


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


def download_file(request, pk):
    doc = Document.objects.get(pk=pk)
    file_content = default_storage.open(doc.name)
    response = HttpResponse(file_content, content_type='application/octet-stream')
    response['Content-Disposition'] = f'attachment; filename="{doc.name}"'
    return response


def download_file1(request, pk):
    document = get_object_or_404(Document, id=pk)

    # Check if the user has permission to download this file
    if document.user != request.user:
        raise PermissionDenied

    # Create a Download record
    Document.objects.create(document=document)

    # Open the file and create an HttpResponse with the file content
    file_content = document.file.read()
    response = HttpResponse(file_content, content_type='application/octet-stream')
    response['Content-Disposition'] = f'attachment; filename="{document.name}"'
    return response


def share_file(request, pk):
    doc = get_object_or_404(Document, pk=pk)
    #   print('I got here')
    #   print(doc.name)
    doc.is_shared = True
    doc.save()
    if request.method == 'POST':
        recipient_email = request.POST.get('recipient_email')
        #   subject = 'A file has been shared with you by {}'.format(request.user.company_name)
        #   message = 'You have been shared a file via File Sharing App. Click the link below to download:'
        #   download_link = request.build_absolute_uri(document.file.url)
        #   html_message = render_to_string('email_template.html', {'download_link': download_link})
        #   recipient = CustomUser.objects.get(email=recipient_email)
        #   result = share_file_task.delay(request.user.pk, recipient_email) # smtplib
        #   result = file_share.delay(request.user.pk, recipient_email) # elasticemail
        #   result = share.delay(doc.pk, request.user.pk, recipient_email)  # EmailMessage
        #   result = new_share.delay(request.user.pk, recipient_email) # elasticemail
        #   result = share_brevo2.delay(doc.pk, request.user.pk, recipient_email)  # brevo {"code":"missing_parameter","message":"One of sender email or sender ID is mandatory"}
        result = share_brevo.delay(doc.pk, request.user.pk, recipient_email)  # brevo error 503
        if result.state == "success":
            return JsonResponse({'success': True, 'message': 'File sent successfully to {}.'.format(recipient_email),
                                 'status': result.status, 'email_result': result.result})

        elif result.state == "Failure":
            return JsonResponse({'success': False, 'message': 'Task to send message is {}.'.format(result.state)})
        else:
            return JsonResponse({'success': False, 'message': 'Task to send message is {}.'.format(result.state)})
    return JsonResponse({'success': False, 'message': 'Invalid request'})


def all_shared_files(request):
    files = Document.objects.filter(is_shared=True, user=request.user).select_related('user')
    context = {
        'files':
            files}
    return render(request, 'my_files.html', context)

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
