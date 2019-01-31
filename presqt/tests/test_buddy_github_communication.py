from django.test import TestCase


class BuddyGithubTestCase(TestCase):

    def test_fail_fail_dont_work(self):
        x = 0
        self.assertEqual(x, 0)
        y = 33
        self.assertEqual(y, 33)