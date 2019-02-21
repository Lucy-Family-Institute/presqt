from django.test import TestCase


class BuddyGithubTestCase(TestCase):

    def test_fail_fail_dont_work(self):
        y = 3
        self.assertEqual(y, 3)
