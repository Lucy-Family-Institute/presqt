from django.test import TestCase


class BuddyGithubTestCase(TestCase):

    def test_fail_fail_dont_work(self):
        y = 4
        self.assertEqual(y, 4)
        y = 3
        self.assertEqual(y, 3)
