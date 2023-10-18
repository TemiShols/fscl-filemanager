from django.shortcuts import render
from azure.storage.blob import BlobServiceClient
from django.http import HttpResponse


def upload_file(request):
    if request.method == 'POST' and request.FILES['file']:
        uploaded_file = request.FILES['file']

        # Azure Storage Account details
        account_name = 'your_storage_account_name'
        account_key = 'your_storage_account_key'
        container_name = 'your_container_name'
        blob_name = uploaded_file.name

        # Create a BlobServiceClient
        blob_service_client = BlobServiceClient(account_url=f'https://{account_name}.blob.core.windows.net',
                                                credential=account_key)

        # Get a container client
        container_client = blob_service_client.get_container_client(container_name)

        # Create the container if it doesn't exist
        container_client.create_container()

        # Upload the file to Azure Blob Storage
        with uploaded_file.open() as data:
            blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)
            blob_client.upload_blob(data)

        return render(request, 'upload_success.html', {'message': 'File uploaded successfully'})
    return render(request, 'upload.html')


def download_file(request, file_name):
    # Azure Storage Account details
    account_name = 'your_storage_account_name'
    account_key = 'your_storage_account_key'
    container_name = 'your_container_name'

    # Create a BlobServiceClient
    blob_service_client = BlobServiceClient(account_url=f'https://{account_name}.blob.core.windows.net',
                                            credential=account_key)

    # Get a blob client for the specified file
    blob_client = blob_service_client.get_blob_client(container=container_name, blob=file_name)

    # Download the file content from Azure Blob Storage
    file_content = blob_client.download_blob()

    # Prepare the response with file content and content type
    response = HttpResponse(file_content.readall(), content_type='application/octet-stream')
    response['Content-Disposition'] = f'attachment; filename="{file_name}"'

    return response


def list_files(request):
    # Azure Storage Account details
    account_name = 'your_storage_account_name'
    account_key = 'your_storage_account_key'
    container_name = 'your_container_name'
    user_id = request.user.id

    # Create a BlobServiceClient
    blob_service_client = BlobServiceClient(account_url=f'https://{account_name}.blob.core.windows.net', credential=account_key)

    # Get a container client
    container_client = blob_service_client.get_container_client(container_name)

    # List blobs/files in the container for the current user
    blobs = container_client.list_blobs(name_starts_with=f'user_{user_id}_')

    # Extract blob names
    file_names = [blob.name.split('_')[2] for blob in blobs]

    return render(request, 'file_list.html', {'file_names': file_names})
