from django.core.exceptions import PermissionDenied
from django.http import HttpResponseBadRequest
from django.http import HttpResponse
import json, os
from django.contrib import messages
from authentication.models import CustomUser
from .utils import load_pdf_file, load_docx_file, load_sitemap_file, load_youtube_file, text_to_speech, \
    extract_and_save_content, generate_sitemap, loads_urls, load_csv_file, load_xlsx_file
from .langchain_mistral import process_langchain_rag, process_langchain_rag_project
from .tasks import send_simple_download_message, send_simple_share_message
from django.utils.text import get_valid_filename
from django.contrib.auth.decorators import login_required
from django.core.serializers.json import DjangoJSONEncoder
from .async_tasks import summarize_and_save, analyse_and_save
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.http import JsonResponse
from django.conf import settings
from .models import Document, ChatMessage, Project


@login_required()
def upload_file(request):
    if request.method == 'POST':
        request_body_size = int(request.META.get('CONTENT_LENGTH', 0))
        if request_body_size > settings.MAX_REQUEST_BODY_SIZE:
            return HttpResponseBadRequest('Request body is too large.')

        uploaded_file = request.FILES.get('file')
        if uploaded_file is not None and uploaded_file.name:
            file_name = uploaded_file.name
            file_type = file_name.split('.')[-1].lower()

            doc = Document.objects.create(file=uploaded_file, name=file_name, user=request.user, type=file_type)

            if file_type in ['docx', 'pdf', 'csv', 'xlsx']:
                content_loader = {
                    'docx': load_docx_file,
                    'pdf': load_pdf_file,
                    'csv': load_csv_file,
                    'xlsx': load_xlsx_file
                }
                content = content_loader[file_type](doc.file.path)
                doc.content = content
                doc.save()
            else:
                messages.error(request, 'Unsupported file type.')
                return HttpResponseBadRequest('Unsupported file type.')

            files = Document.objects.filter(user=request.user.id).order_by('-uploaded_at')

            if request.headers.get('HX-Request'):
                return render(request, 'my_file_partial.html', {'files': files})
            else:
                messages.success(request, 'File uploaded successfully')
                return render(request, 'file2.html', {'files': files})
        else:
            messages.error(request, 'No file is uploaded. Please ensure you have uploaded a file.')
            return HttpResponseBadRequest('No file uploaded.')

    files = Document.objects.filter(user=request.user.id).order_by('-uploaded_at')
    return render(request, 'file2.html', {'files': files})


def create_project(request):
    return render(request, 'create_project.html', {})


def new_project(request):  # should navigate to where to input the sitemap.xml generated to desktop then navigate to
    # projects
    if request.method == 'POST':
        data_type = request.POST.get('data_type')
        project_name = request.POST.get('name')
        url = request.POST.get('url_input')

        try:
            if data_type == 'sitemap':
                content = load_sitemap_file(url)
                Project.objects.create(name=project_name, user=request.user, is_sitemap=True, content=content,
                                       scope=url)
            elif data_type == 'url':
                url_list = url.split(';')
                content = loads_urls(url_list)
                if content:
                    Project.objects.create(name=project_name, user=request.user, is_url=True, content=content,
                                           scope=url)
                else:
                    messages.error(request, 'Failed to fetch content from the URL.')
            elif data_type == 'youtube':
                content = load_youtube_file(url)
                Project.objects.create(name=project_name, user=request.user, is_youtube=True, content=content,
                                       scope=url)

            projects = Project.objects.filter(user=request.user).order_by('-uploaded_at')

            if request.headers.get('HX-Request'):
                return render(request, 'my_project_partial.html', {'projects': projects})
            else:
                messages.success(request, 'Project created successfully')
                context = {'projects': projects}
                return render(request, 'new_project.html', context)
        except Exception as e:
            messages.error(request, f'Error creating project: {e}')
            projects = Project.objects.filter(user=request.user).order_by('-uploaded_at')
            context = {'projects': projects}
            return render(request, 'new_project.html', context)

    projects = Project.objects.filter(user=request.user).order_by('-uploaded_at')
    context = {"projects": projects}
    return render(request, 'new_project.html', context)


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
            task = send_simple_share_message.delay(request.user.pk, recipient_email, context_json)
            print(task.status)
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


def summarize(request, pk):
    doc = Document.objects.get(pk=pk)
    if doc.summary:
        context = {
            'doc': doc,
            'error': 'Please check file again or contact support for issues'
        }

        return render(request, 'summarize.html', context)
    else:
        summarize_and_save(doc.pk)

    context = {
        'doc': doc,
        'error': 'Please check file again or contact support for issues'
    }

    return render(request, 'summarize.html', context)


def analyze(request, pk):
    doc = Document.objects.get(pk=pk)

    if not doc.summary:
        analyse_and_save(doc.pk)
    context = {
        'doc': doc,
        'error': 'Please check file again or contact support for issues'
    }

    return render(request, 'summarize.html', context)


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
        url = request.POST.get('sitemap')
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
