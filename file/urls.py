from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from . import views

urlpatterns = [
                  path('home/', views.upload_file, name='upload'),
                  path('download/<int:pk>/', views.download_file, name='download'),
                  path('share/<int:pk>/', views.share_file, name='share_file'),
                  path('shared_files/', views.all_shared_files, name='shared_file'),
                  path('search/', views.filter_documents, name='search_file'),
                  path('files/', views.list_files, name='files'),
                  path('projects/', views.list_projects, name='projects'),
                  path('summarize/<int:pk>/', views.summarize, name='summary'),
                  path('shared/<int:pk>/', views.shared_file, name='shared_file'),
                  path('analyze/<int:pk>/', views.analyze, name='analyze'),
                  path('chat/<int:pk>/', views.chatbot, name='chatbot'),
                  path('get-messages/<int:pk>/', views.get_messages, name='messages'),
                  path('get-proj-messages/<int:pk>/', views.get_proj_messages, name='proj_messages'),
                  path('create-project/', views.create_project, name='create_project'),
                  path('new-project/', views.new_project, name='new_project'),
                  path('project-chat/<int:pk>/', views.proj_chatbot, name='proj_chatbot'),
                  path('create-sitemap/', views.process_sitemap_view, name='create_sitemap'),
                  path('generate-sitemap/', views.gen_sitemap, name='gen_sitemap'),
              ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
