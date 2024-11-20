from django.core.exceptions import PermissionDenied
from django.http import HttpResponseBadRequest
from django.http import HttpResponse
import json, os
from django.contrib import messages
from authentication.models import CustomUser
from .utils import load_pdf_file, load_docx_file, load_sitemap_file, load_youtube_file, text_to_speech, \
    extract_and_save_content, generate_sitemap, loads_urls, load_csv_file, load_xlsx_file
from .langchain_mistral import process_langchain_rag, process_langchain_rag_project
from django.utils.text import get_valid_filename
from django.contrib.auth.decorators import login_required
from django.core.serializers.json import DjangoJSONEncoder
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.http import JsonResponse
from django.conf import settings
from .models import Document, ChatMessage, Project
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.http import HttpResponseBadRequest, JsonResponse
from django.conf import settings
from django.contrib import messages
from .models import Document


@login_required
def upload_file(request):
    try:
        if request.method == 'POST':
            # Check file size
            file = request.FILES.get('file')
            if file and file.size > settings.MAX_REQUEST_BODY_SIZE:
                messages.error(request, 'File size exceeds maximum allowed limit.')
                return redirect('upload')

            # Process file
            if file:
                file_name = file.name
                file_type = file_name.split('.')[-1].lower()

                # Validate file type
                allowed_types = ['docx', 'pdf', 'csv', 'xlsx']
                if file_type not in allowed_types:
                    messages.error(request, f'Unsupported file type. Allowed types: {", ".join(allowed_types)}')
                    return redirect('upload')

                # Create document record
                doc = Document.objects.create(
                    file=file,
                    name=file_name,
                    user=request.user,
                    type=file_type
                )

                # Process file content based on type
                content_loader = {
                    'docx': load_docx_file,
                    'pdf': load_pdf_file,
                    'csv': load_csv_file,
                    'xlsx': load_xlsx_file
                }

                try:
                    content = content_loader[file_type](doc.file.path)
                    doc.content = content
                    doc.save()
                    messages.success(request, 'File uploaded and processed successfully.')
                except Exception as e:
                    doc.delete()  # Clean up on failure
                    messages.error(request, f'Error processing file: {str(e)}')
                    return redirect('upload')
            else:
                messages.error(request, 'No file was uploaded.')
                return redirect('upload')

        # Get user's files for display
        files = Document.objects.filter(user=request.user).order_by('-uploaded_at')
        context = {
            'files': files,
            'max_file_size': settings.MAX_REQUEST_BODY_SIZE,
            'allowed_types': ['docx', 'pdf', 'csv', 'xlsx'],
            'url': request.build_absolute_uri()
        }

        return render(request, 'file2.html', context)

    except Exception as e:
        messages.error(request, f'An unexpected error occurred: {str(e)}')
        return redirect('upload')


def create_project(request):
    return render(request, 'create_project.html', {})


def new_project(request):
    if request.method == 'POST':
        data_type = request.POST.get('data_type')
        project_name = request.POST.get('name')

        try:
            if data_type == 'sitemap':
                content = load_sitemap_file(data_type)
                Project.objects.create(name=project_name, user=request.user, is_sitemap=True, content=content,
                                       scope='sitemap')
            elif data_type == 'url':
                url_list = data_type.split(';')
                content = loads_urls(url_list)
                print(content)
                if content:
                    Project.objects.create(name=project_name, user=request.user, is_url=True, content=content,
                                           scope='url')
                else:
                    messages.error(request, 'Failed to fetch content from the URL.')
            elif data_type == 'youtube':
                content = load_youtube_file(data_type)
                Project.objects.create(name=project_name, user=request.user, is_youtube=True, content=content,
                                       scope='youtube')

            projects = Project.objects.filter(user=request.user).order_by('-uploaded_at')

            messages.success(request, 'Project created successfully')
            context = {'projects': projects}
            return render(request, 'my_projects.html', context)
        except Exception as e:
            messages.error(request, f'Error creating project: {e}')
    projects = Project.objects.filter(user=request.user).order_by('-uploaded_at')
    context = {"projects": projects}
    return render(request, 'my_projects.html', context)


@login_required()
def list_files(request):
    files = Document.objects.filter(user=request.user.id).order_by('-uploaded_at')
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
def list_projects(request):
    projects = Project.objects.filter(user=request.user).order_by('-uploaded_at')
    context = {
        'projects':
            projects
    }
    return render(request, 'my_projects.html', context)


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
def my_documents(request):
    docs = Document.objects.filter(user=request.user)
    context = {
        'docs': docs
    }
    return render(request, 'my_documents.html', context)


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
    #   send_simple_download_message.delay(doc.pk, context_json)
    response = HttpResponse(doc, content_type='application/octet-stream')
    response['Content-Disposition'] = f'attachment; filename="{doc.name}"'
    return response


@login_required()
def share_file(request, pk):
    if request.method == 'POST':
        doc = get_object_or_404(Document, pk=pk, user=request.user)
        doc.is_shared = True
        doc.save()

        context_data = {
            'doc_name': doc.name or doc.file.name,
            'file_url': request.build_absolute_uri(reverse('shared_file', args=[doc.pk])),
            'sender_name': request.user.get_full_name() or request.user.username,
            'company_name': getattr(request.user, 'company_name', ''),
        }
        context_json = json.dumps(context_data, cls=DjangoJSONEncoder)

        recipient_email = request.POST.get('recipient_email')
        if recipient_email:
            # task = send_simple_share_message.delay(request.user.pk, recipient_email, context_json)
            # print(task.status)
            return JsonResponse({'success': True, 'message': 'File shared successfully'})
        else:
            return JsonResponse({'success': False, 'message': 'Recipient email is required'})

    return JsonResponse({'success': False, 'message': 'Invalid request method'})


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


# def summarize(request, pk):
#    doc = Document.objects.get(pk=pk)
#    if doc.summary:
#        context = {
#            'doc': doc,
#            'error': 'Please check file again or contact support for issues'
#        }
#
#        #return render(request, 'summarize.html', context)
#    else#:
#        summarize_and_save(doc.pk)#
#
#    context = {
#        'doc': doc,
#        'error': 'Please check file again or contact support for issues'
#    }
#
#    return render(request, 'summarize.html', context)


# def analyze(request, pk):
#    doc = Document.objects.get(pk=pk)
#
#
#    if not doc.summary:
#        analyse_and_save(doc.pk)
#    context = {
#        'doc': doc,
#        'error': 'Please check file again or contact support for issues'
#    }
#
#   return render(request, 'summarize.html', context)


def chatbot(request, pk=None):
    if request.method == 'POST':
        query = request.POST.get('query')
        pk = request.POST.get('document')
        doc = get_object_or_404(Document, pk=pk)
        user_message = ChatMessage.objects.create(document=doc, user=request.user, message=query, is_bot_response=False)
        #   directory_path = doc.file.path
        #   file_type = doc.type
        response = process_langchain_rag(doc.pk, query)
        bot_message = ChatMessage.objects.create(document=doc, user=request.user, message=response,
                                                 is_bot_response=True)

        chat_history = ChatMessage.objects.filter(document=doc, user=request.user).order_by('timestamp')
        audio_file_path = text_to_speech(response)

        # Prepare context for rendering
        context = {
            'chat_history': [user_message, bot_message],
            'audio_file_url': audio_file_path
        }

        # Check if it's an HTMX request
        if request.headers.get('HX-Request'):
            return render(request, 'chatbot_response_partial.html', context)
        else:
            return render(request, 'chatbot.html', context=context)
    else:
        if pk is None:
            return HttpResponse("Document not found", status=404)

        doc = get_object_or_404(Document, pk=pk)
        chat_history = ChatMessage.objects.filter(document=doc, user=request.user).order_by('timestamp')
        context = {
            'document': doc,
            'chat_history': chat_history
        }
        return render(request, 'chatbot.html', context=context)


def proj_chatbot(request, pk=None):
    if request.method == 'POST':
        query = request.POST.get('query')
        pk = request.POST.get('project')
        proj = get_object_or_404(Project, pk=pk)
        user_message = ChatMessage.objects.create(project=proj, user=request.user, message=query, is_bot_response=False)
        response = process_langchain_rag_project(proj.pk, query)
        bot_message = ChatMessage.objects.create(project=proj, user=request.user, message=response,
                                                 is_bot_response=True)

        chat_history = ChatMessage.objects.filter(project=proj, user=request.user).order_by('timestamp')
        audio_file_path = text_to_speech(response)

        # Prepare context for rendering
        context = {
            'chat_history': [user_message, bot_message],
            'audio_file_url': audio_file_path
        }

        # Check if it's an HTMX request
        if request.headers.get('HX-Request'):
            return render(request, 'proj_chatbot_response_partial.html', context)
        else:
            return render(request, 'proj_chatbot.html', context=context)
    else:
        if pk is None:
            return HttpResponse("Document not found", status=404)

        proj = get_object_or_404(Project, pk=pk)
        chat_history = ChatMessage.objects.filter(project=proj, user=request.user).order_by('timestamp')
        context = {
            'project': proj,
            'chat_history': chat_history
        }
        return render(request, 'proj_chatbot.html', context=context)


def process_sitemap_view(request):
    if request.method == 'POST':
        uploaded_file = request.FILES['sitemap']

        try:
            # Sanitize the uploaded file name
            file_name = get_valid_filename(os.path.basename(uploaded_file.name))
            desktop_path = os.path.join(os.path.expanduser("~"), "Desktop", file_name)

            project = Project.objects.create(
                user=request.user,
                scope='Auto-Gen of Sitemap',
                is_sitemap=True,
                name=file_name
            )

            # Save the file securely
            with open(desktop_path, 'wb+') as destination:
                for chunk in uploaded_file.chunks():
                    destination.write(chunk)

            # Read the uploaded file content
            with open(desktop_path, 'r', encoding='utf-8') as file:
                sitemap_xml_content = file.read()

            # Process the sitemap content
            extract_and_save_content(sitemap_xml_content, project.pk)

            messages.success(request, 'Project created successfully')

        except Exception as e:
            # Display any exceptions or errors
            messages.error(request, f"An error occurred: {e}")

        projects = Project.objects.filter(user=request.user).order_by('-uploaded_at')
        return redirect('gen_sitemap')
    return render(request, 'new_sitemap.html', {})


def gen_sitemap(request):
    if request.method == 'POST':
        url = request.POST.get('url_input')
        try:
            sitemap_path = generate_sitemap(url)
            if sitemap_path:
                messages.success(request, 'Sitemap has been successfully generated and saved to your desktop.')
            else:
                messages.error(request, 'Failed to generate or save the sitemap.')
        except Exception as e:
            messages.error(request, f'An error occurred: {str(e)}')

        # Redirect to the page where users can create a new project
        return redirect('create_sitemap')

    # Render the form for generating a sitemap
    return render(request, 'sitemap_new_project.html', {})


def get_messages(request, pk):
    doc = get_object_or_404(Document, pk=pk)
    chat_history = ChatMessage.objects.filter(document=doc, user=request.user).order_by('timestamp')
    response = {
        "messages": list(chat_history.values('message', 'timestamp', 'is_bot_response'))
    }
    return JsonResponse(response)


def get_proj_messages(request, pk):
    proj = get_object_or_404(Project, pk=pk)
    chat_history = ChatMessage.objects.filter(project=proj, user=request.user).order_by('timestamp')
    response = {
        "messages": list(chat_history.values('message', 'timestamp', 'is_bot_response'))
    }
    return JsonResponse(response)
