from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import Document
from authentication.models import CustomUser

User = get_user_model()


class FileSharingAppTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            email='test@example.com',
            password='testpassword',
        )
        self.client.login(email='test@example.com', password='testpassword')
        self.file = Document.objects.create(name='file.txt', user=self.user)

    def test_upload_file_view(self):
        response = self.client.get(reverse('upload'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'files.html')

        with open('C:/Users/tpsol/Downloads/filemanager/uploads/file.txt', 'rb') as file_data:
            response = self.client.post(reverse('upload'), {'file': file_data})

        self.assertEqual(response.status_code, 302)  # Check if the file upload redirects to 'files' page

    def test_list_files_view(self):
        response = self.client.get(reverse('files'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'my_files.html')
        self.assertContains(response, 'file.txt')

    def test_filter_documents_view(self):
        response = self.client.post(reverse('search_file'), {'company': 'testcompany', 'name': 'file.txt'})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'my_files.html')
        self.assertContains(response, 'file.txt')

    def test_download_file_view(self):
        response = self.client.get(reverse('download', args=[self.file.pk]))
        self.assertEqual(response.status_code, 200)

    # def test_share_file_view(self):  # awaiting for email services so can configure the email settings. response =
    # self.client.post(reverse('share_file', args=[self.file.id]), {'recipient_email': 'test@example.com'})
    # self.assertEqual(response.status_code, 200)

    def test_all_shared_files_view(self):
        response = self.client.get(reverse('shared_file'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'my_files.html')
