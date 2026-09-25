from django.contrib.auth import get_user_model
from django.test import TestCase

from shop.models import Subject

from .ai import make_refusal
from .models import Message, Thread

User = get_user_model()


class DmTestCase(TestCase):
    def setUp(self):
        self.student = User.objects.create_user(
            username="t23cs001", role="student", display_name="佐藤 次郎"
        )
        self.professor = User.objects.create_user(
            username="prof.yamada", role="professor", display_name="山田 太郎"
        )
        self.thread = Thread.objects.create(student=self.student, professor=self.professor)


class ThreadModelTest(DmTestCase):
    def test_str(self):
        self.assertEqual(str(self.thread), "佐藤 次郎 - 山田 太郎")

    def test_partner(self):
        self.assertEqual(self.thread.partner(self.student), self.professor)
        self.assertEqual(self.thread.partner(self.professor), self.student)


class AiTest(DmTestCase):
    def test_refusal_contains_the_student_name(self):
        self.assertIn("佐藤 次郎", make_refusal(self.student))


class ThreadViewTest(DmTestCase):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.student)

    def test_list_shows_only_my_threads(self):
        Thread.objects.create(
            student=User.objects.create_user("t23cs002"),
            professor=User.objects.create_user("prof.suzuki", role="professor"),
        )
        response = self.client.get("/messages/")
        self.assertEqual(list(response.context["threads"]), [self.thread])

    def test_list_shows_unread_count(self):
        Message.objects.create(thread=self.thread, sender=self.professor, body="返信です")
        response = self.client.get("/messages/")
        self.assertEqual(response.context["threads"][0].unread, 1)

    def test_detail_shows_messages_and_marks_them_read(self):
        Message.objects.create(thread=self.thread, sender=self.professor, body="返信です")
        response = self.client.get(self.thread.get_absolute_url())
        self.assertContains(response, "返信です")
        self.assertIsNotNone(Message.objects.get().read_at)

    def test_cannot_open_other_peoples_thread(self):
        self.client.force_login(User.objects.create_user("t23cs002"))
        self.assertEqual(self.client.get(self.thread.get_absolute_url()).status_code, 404)


class SendTest(DmTestCase):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.student)

    def test_send(self):
        self.client.post(f"/messages/{self.thread.pk}/send/", {"body": "お願いします。"})
        message = Message.objects.get()
        self.assertEqual(message.sender, self.student)
        self.assertEqual(message.body, "お願いします。")

    def test_empty_body_is_rejected(self):
        response = self.client.post(
            f"/messages/{self.thread.pk}/send/", {"body": "   "}, follow=True
        )
        self.assertEqual(Message.objects.count(), 0)
        self.assertContains(response, "本文を入力")


class StartTest(DmTestCase):
    def setUp(self):
        super().setUp()
        self.subject = Subject.objects.create(
            code="TCS101", name="プログラミング基礎", professor=self.professor, price=30000, stock=3
        )

    def test_student_can_start(self):
        self.thread.delete()
        self.client.force_login(self.student)
        self.client.post(f"/messages/start/{self.subject.pk}/")
        thread = Thread.objects.get()
        self.assertEqual(thread.student, self.student)
        self.assertEqual(thread.professor, self.professor)

    def test_draft_is_filled_in(self):
        self.client.force_login(self.student)
        response = self.client.get(
            self.thread.get_absolute_url(), {"subject": self.subject.pk}
        )
        self.assertIn("プログラミング基礎", response.context["draft"])

    def test_broken_subject_parameter_is_ignored(self):
        self.client.force_login(self.student)
        for value in ["", "abc", "9999"]:
            response = self.client.get(self.thread.get_absolute_url(), {"subject": value})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.context["draft"], "")

    def test_professor_cannot_start(self):
        self.thread.delete()
        self.client.force_login(self.professor)
        response = self.client.post(f"/messages/start/{self.subject.pk}/", follow=True)
        self.assertEqual(Thread.objects.count(), 0)
        self.assertContains(response, "学生アカウント")


class AiRefuseTest(DmTestCase):
    def test_professor_can_refuse(self):
        self.client.force_login(self.professor)
        self.client.post(f"/messages/{self.thread.pk}/refuse/")
        message = Message.objects.get()
        self.assertEqual(message.sender, self.professor)
        self.assertTrue(message.is_ai)
        self.assertIn("佐藤 次郎", message.body)

    def test_student_cannot_refuse(self):
        self.client.force_login(self.student)
        response = self.client.post(f"/messages/{self.thread.pk}/refuse/")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Message.objects.count(), 0)
