from django.test import TestCase


class BuddyGithubTestCase(TestCase):

    def test_fail_fail_dont_work(self):
        x = 4
        self.assertEqual(x, 4)
        y = 3
        self.assertEqual(y, 3)
