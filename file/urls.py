from django.urls import path
from . import views

urlpatterns = [
    path('home/', views.upload_file, name='upload'),
    path('download/<int:pk>/', views.download_file, name='download'),
    path('share/<int:pk>/', views.share_file, name='share_file'),
    path('shared_files/', views.all_shared_files, name='shared_file'),
    path('search/', views.filter_documents, name='search_file'),
    path('files/', views.list_files, name='files'),
    path('summarize/<int:pk>/', views.summarize, name='summary'),
    path('shared/<int:pk>/', views.shared_file, name='shared_file'),
    #   path('get_files/', views.get_files, name='all_files'),
]