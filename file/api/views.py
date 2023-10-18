from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.core.files.storage import default_storage
from django.http import HttpResponse
import os
from ..models import Document


class FileUploadView(APIView):
    def post(self, request, *args, **kwargs):
        uploaded_file = request.FILES.get('file')
        if uploaded_file:
            user_id = request.user.id
            file_name = f'user_{user_id}_{uploaded_file.name}'
            path = default_storage.save(os.path.join('uploads', file_name), uploaded_file)
            Document.objects.create(file=uploaded_file, user_id=user_id)
            return Response({'message': 'File uploaded successfully'}, status=status.HTTP_201_CREATED)
        return Response({'error': 'No file uploaded'}, status=status.HTTP_400_BAD_REQUEST)


class FileDownloadView(APIView):
    def get(self, request, file_name, *args, **kwargs):
        user_id = request.user.id
        path = f'uploads/user_{user_id}/{file_name}'
        file_content = default_storage.open(path).read()
        Document.objects.get(user_id=user_id)
        response = HttpResponse(file_content, content_type='application/octet-stream')
        response['Content-Disposition'] = f'attachment; filename="{file_name}"'
        return response


class FileListView(APIView):
    def get(self, request, *args, **kwargs):
        user_id = request.user.id
        path = f'uploads/user_{user_id}/'
        file_names = default_storage.listdir(path)[1]
        return Response({'file_names': file_names}, status=status.HTTP_200_OK)
