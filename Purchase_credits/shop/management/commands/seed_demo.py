# デモデータを入れる: python manage.py seed_demo

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.management.base import BaseCommand

from dm.models import Message, Thread
from shop.models import Subject

PASSWORD = "demo-pass-1234"

DEPARTMENT = "コンピュータ理工学科"

# 名前は適当
PROFESSORS = [
    ("prof.yamada", "山田 太郎", DEPARTMENT),
    ("prof.suzuki", "鈴木 花子", DEPARTMENT),
]

STUDENTS = [
    ("t23cs001", "佐藤 次郎", "t23cs001", DEPARTMENT),
    ("t23cs002", "田中 三郎", "t23cs002", DEPARTMENT),
]

# 科目コード, 科目名, 担当, 開講, 単位数, 価格, 残り枠
SUBJECTS = [
    ("TCS101", "プログラミング基礎", "prof.yamada", "1年次 前期", 2, 24000, 5),
    ("TCS201", "アルゴリズムとデータ構造I", "prof.yamada", "2年次 前期", 2, 38000, 3),
    ("TCS202", "計算機アーキテクチャI", "prof.suzuki", "2年次 前期", 2, 36000, 2),
    ("TCS301", "オペレーティングシステム", "prof.suzuki", "3年次 前期", 2, 52000, 1),
    ("TCS302", "データベース及び演習", "prof.yamada", "3年次 前期", 3, 58000, 0),
    ("TCS303", "形式言語とコンパイラ", "prof.suzuki", "3年次 後期", 2, 64000, 3),
]

# 教授に渡す権限（Order は他の教授の分も見えちゃうので渡さない）
PROFESSOR_PERMISSIONS = [
    "add_subject",
    "change_subject",
    "delete_subject",
    "view_subject",
    "view_orderitem",
]

DEMO_MESSAGES = [
    "鈴木先生\n\n突然のご連絡失礼します。形式言語とコンパイラの件でご相談させてください。",
    "今学期どうしても単位が足りず、なんとかお願いできないでしょうか。",
]


class Command(BaseCommand):
    help = "デモ用のユーザ・科目・メッセージを作る"

    def handle(self, *args, **options):
        User = get_user_model()
        users = {}

        permissions = Permission.objects.filter(
            content_type__app_label="shop", codename__in=PROFESSOR_PERMISSIONS
        )

        for username, name, department in PROFESSORS:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    "role": "professor",
                    "display_name": name,
                    "department": department,
                    "is_staff": True,
                },
            )
            if created:
                user.set_password(PASSWORD)
                user.save()
            user.user_permissions.set(permissions)
            users[username] = user

        for username, name, number, department in STUDENTS:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    "role": "student",
                    "display_name": name,
                    "student_number": number,
                    "department": department,
                },
            )
            if created:
                user.set_password(PASSWORD)
                user.save()
            users[username] = user

        for code, name, owner, term, credits, price, stock in SUBJECTS:
            Subject.objects.update_or_create(
                code=code,
                defaults={
                    "name": name,
                    "professor": users[owner],
                    "department": DEPARTMENT,
                    "term": term,
                    "credits": credits,
                    "price": price,
                    "stock": stock,
                },
            )

        # 「AIで断る」を試す用
        thread, _ = Thread.objects.get_or_create(
            student=users["t23cs001"], professor=users["prof.suzuki"]
        )
        for body in DEMO_MESSAGES:
            Message.objects.get_or_create(thread=thread, sender=thread.student, body=body)

        self.stdout.write(self.style.SUCCESS(f"デモデータを作りました。パスワード: {PASSWORD}"))
