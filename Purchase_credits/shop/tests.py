from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase

from .models import CartItem, Order, OrderItem, Subject
from .views import purchase_error

User = get_user_model()


def make_users():
    student = User.objects.create_user(
        username="t23cs001", role="student", display_name="佐藤 次郎"
    )
    professor = User.objects.create_user(
        username="prof.yamada", role="professor", display_name="山田 太郎"
    )
    return student, professor


class ShopTestCase(TestCase):
    def setUp(self):
        self.student, self.professor = make_users()
        self.subject = Subject.objects.create(
            code="TCS101", name="プログラミング基礎", professor=self.professor,
            department="コンピュータ理工学科", price=30000, stock=3,
        )
        self.client.force_login(self.student)


class SubjectModelTest(ShopTestCase):
    def test_str(self):
        self.assertEqual(str(self.subject), "TCS101 プログラミング基礎")


class PurchaseErrorTest(ShopTestCase):
    def test_student_can_buy(self):
        self.assertIsNone(purchase_error(self.student, self.subject))

    def test_cannot_buy_when_unavailable(self):
        self.subject.is_active = False
        self.assertIn("取り扱っていません", purchase_error(self.student, self.subject))
        self.subject.is_active = True
        self.subject.stock = 0
        self.assertIn("残り枠", purchase_error(self.student, self.subject))

    def test_professor_cannot_buy(self):
        self.assertIn("学生アカウント", purchase_error(self.professor, self.subject))

    def test_cannot_buy_own_subject(self):
        self.professor.role = "student"
        self.assertIn("自分の出品", purchase_error(self.professor, self.subject))

    def test_cannot_buy_twice(self):
        order = Order.objects.create(user=self.student)
        OrderItem.objects.create(
            order=order, subject=self.subject, subject_name=self.subject.name, price=30000
        )
        self.assertIn("すでに申し込み済み", purchase_error(self.student, self.subject))


class SubjectViewTest(ShopTestCase):
    def test_list_shows_subjects_on_sale(self):
        Subject.objects.create(code="X1", name="停止中", professor=self.professor,
                               price=1000, stock=5, is_active=False)
        Subject.objects.create(code="X2", name="売り切れ", professor=self.professor,
                               price=1000, stock=0)
        response = self.client.get("/subjects/")
        self.assertEqual(list(response.context["subjects"]), [self.subject])

    def test_search(self):
        Subject.objects.create(code="TCS202", name="計算機アーキテクチャI", professor=self.professor,
                               price=1000, stock=5)
        response = self.client.get("/subjects/", {"q": "アーキ"})
        self.assertEqual([s.code for s in response.context["subjects"]], ["TCS202"])

    def test_detail(self):
        response = self.client.get(self.subject.get_absolute_url())
        self.assertContains(response, "プログラミング基礎")
        self.assertContains(response, "カートに入れる")


class CartTest(ShopTestCase):
    def test_add(self):
        self.client.post(f"/cart/add/{self.subject.pk}/")
        self.assertEqual(CartItem.objects.filter(user=self.student).count(), 1)

    def test_add_twice_keeps_one(self):
        self.client.post(f"/cart/add/{self.subject.pk}/")
        self.client.post(f"/cart/add/{self.subject.pk}/")
        self.assertEqual(CartItem.objects.count(), 1)

    def test_cannot_add_sold_out(self):
        self.subject.stock = 0
        self.subject.save()
        response = self.client.post(f"/cart/add/{self.subject.pk}/", follow=True)
        self.assertEqual(CartItem.objects.count(), 0)
        self.assertContains(response, "残り枠")

    def test_remove(self):
        CartItem.objects.create(user=self.student, subject=self.subject)
        self.client.post(f"/cart/remove/{self.subject.pk}/")
        self.assertEqual(CartItem.objects.count(), 0)

    def test_total(self):
        other = Subject.objects.create(code="TCS202", name="計算機アーキテクチャI",
                                       professor=self.professor, price=12000, stock=1)
        CartItem.objects.create(user=self.student, subject=self.subject)
        CartItem.objects.create(user=self.student, subject=other)
        self.assertEqual(self.client.get("/cart/").context["total"], 42000)


class CheckoutTest(ShopTestCase):
    def test_empty_cart(self):
        response = self.client.post("/checkout/", follow=True)
        self.assertContains(response, "カートが空です")
        self.assertEqual(Order.objects.count(), 0)

    def test_creates_order(self):
        CartItem.objects.create(user=self.student, subject=self.subject)
        self.client.post("/checkout/")
        order = Order.objects.get()
        self.assertEqual(order.user, self.student)
        self.assertEqual(order.total_price, 30000)
        self.assertEqual(order.items.count(), 1)

    def test_reduces_stock_and_empties_cart(self):
        CartItem.objects.create(user=self.student, subject=self.subject)
        self.client.post("/checkout/")
        self.subject.refresh_from_db()
        self.assertEqual(self.subject.stock, 2)
        self.assertEqual(CartItem.objects.count(), 0)

    def test_values_are_copied(self):
        CartItem.objects.create(user=self.student, subject=self.subject)
        self.client.post("/checkout/")
        self.subject.code = "XX999"
        self.subject.name = "改名後"
        self.subject.price = 1
        self.subject.save()
        item = OrderItem.objects.get()
        self.assertEqual(item.subject_code, "TCS101")
        self.assertEqual(item.subject_name, "プログラミング基礎")
        self.assertEqual(item.professor_name, "山田 太郎")
        self.assertEqual(item.price, 30000)

    def test_nothing_happens_when_one_item_is_unavailable(self):
        other = Subject.objects.create(code="TCS202", name="計算機アーキテクチャI",
                                       professor=self.professor, price=12000, stock=2)
        CartItem.objects.create(user=self.student, subject=self.subject)
        CartItem.objects.create(user=self.student, subject=other)
        Subject.objects.filter(pk=other.pk).update(is_active=False)

        self.client.post("/checkout/")

        self.assertEqual(Order.objects.count(), 0)
        self.subject.refresh_from_db()
        self.assertEqual(self.subject.stock, 3)
        self.assertEqual(CartItem.objects.count(), 2)


class OrderViewTest(ShopTestCase):
    def test_list_shows_only_my_orders(self):
        mine = Order.objects.create(user=self.student, total_price=30000)
        Order.objects.create(user=User.objects.create_user("t23cs002"))
        response = self.client.get("/orders/")
        self.assertEqual(list(response.context["orders"]), [mine])

    def test_cannot_open_other_peoples_order(self):
        order = Order.objects.create(user=User.objects.create_user("t23cs002"))
        self.assertEqual(self.client.get(order.get_absolute_url()).status_code, 404)


class AdminTest(TestCase):
    def setUp(self):
        self.student, self.professor = make_users()
        self.other_professor = User.objects.create_user(
            username="prof.suzuki", role="professor", display_name="鈴木 花子"
        )
        for user in [self.professor, self.other_professor]:
            user.is_staff = True
            user.save()
            user.user_permissions.set(
                Permission.objects.filter(content_type__app_label="shop")
            )

        self.mine = Subject.objects.create(code="TCS101", name="プログラミング基礎",
                                           professor=self.professor, price=30000, stock=3)
        self.theirs = Subject.objects.create(code="TCS202", name="計算機アーキテクチャI",
                                             professor=self.other_professor, price=12000, stock=1)

    def test_professor_sees_only_own_subjects(self):
        self.client.force_login(self.other_professor)
        response = self.client.get("/staff-console/shop/subject/")
        self.assertContains(response, "TCS202")
        self.assertNotContains(response, "TCS101")

    def test_professor_sees_only_own_sales(self):
        order = Order.objects.create(user=self.student)
        OrderItem.objects.create(order=order, subject=self.mine,
                                 subject_name=self.mine.name, price=30000)
        OrderItem.objects.create(order=order, subject=self.theirs,
                                 subject_name=self.theirs.name, price=12000)

        self.client.force_login(self.other_professor)
        response = self.client.get("/staff-console/shop/orderitem/")
        self.assertContains(response, "計算機アーキテクチャI")
        self.assertNotContains(response, "プログラミング基礎")

    def test_professor_can_create_subject(self):
        self.client.force_login(self.professor)
        self.client.post("/staff-console/shop/subject/add/", {
            "code": "TCS999", "name": "特別演習", "professor": self.professor.pk,
            "department": "コンピュータ理工学科", "term": "後期", "credits": 2,
            "price": 50000, "stock": 1, "is_active": "on", "description": "",
        })
        self.assertTrue(Subject.objects.filter(code="TCS999").exists())
