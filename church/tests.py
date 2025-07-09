from django.test import TestCase
from church.models import Church

class ChurchModelTest(TestCase):
    def test_church_creation(self):
        church = Church.objects.create(name="Test Church", timezone="Asia/Seoul")
        self.assertEqual(church.name, "Test Church")
        self.assertEqual(church.timezone, "Asia/Seoul")
        self.assertIsNotNone(church.created_at)
        self.assertIsNotNone(church.updated_at)

    def test_church_str_representation(self):
        church = Church.objects.create(name="Another Church")
        self.assertEqual(str(church), "Another Church")