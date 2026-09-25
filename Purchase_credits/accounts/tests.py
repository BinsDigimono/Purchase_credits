from django.contrib.auth import get_user_model
from django.test import TestCase

User = get_user_model()


class LoginTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="t23cs001", password="pass1234")

    def test_top_page_is_the_login_page(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "メンテナンス")

    def test_login(self):
        response = self.client.post("/", {"username": "t23cs001", "password": "pass1234"})
        self.assertRedirects(response, "/subjects/")

    def test_logout(self):
        self.client.force_login(self.user)
        self.client.post("/logout/")
        self.assertEqual(self.client.get("/subjects/").status_code, 404)


class HideSiteTest(TestCase):
    # 未ログインの画面に出たらまずい言葉
    NG_WORDS = ["単位", "購入", "カート", "教授", "価格", "科目", "出品", "マーケット"]

    def test_protected_pages_are_404_not_redirect(self):
        for path in ["/subjects/", "/subjects/1/", "/cart/", "/orders/", "/messages/"]:
            self.assertEqual(self.client.get(path).status_code, 404)

    def test_admin_is_hidden(self):
        self.assertEqual(self.client.get("/staff-console/").status_code, 404)

    def test_pages_do_not_leak(self):
        for path in ["/", "/subjects/", "/robots.txt"]:
            body = self.client.get(path).content.decode()
            for word in self.NG_WORDS:
                self.assertNotIn(word, body)

    def test_robots_txt_blocks_everything(self):
        response = self.client.get("/robots.txt")
        self.assertContains(response, "Disallow: /")
