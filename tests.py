from django.test import TestCase
from rest_framework.test import APITestCase

class ScoringAppTest(APITestCase):

    def setUp(self):
        """"""

    def test_dataset(self):
        self.client()