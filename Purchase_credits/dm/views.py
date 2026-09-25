from django.contrib import messages
from django.db.models import Q
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from shop.models import Subject

from .ai import make_refusal
from .models import Message, Thread


# 自分のトークだけ取り出す（他人のは404）
def get_my_thread(request, pk):
    return get_object_or_404(
        Thread.objects.filter(Q(student=request.user) | Q(professor=request.user)), pk=pk
    )


def thread_list(request):
    threads = Thread.objects.filter(
        Q(student=request.user) | Q(professor=request.user)
    ).select_related("student", "professor")

    for thread in threads:
        thread.partner_user = thread.partner(request.user)
        thread.last_message = thread.messages.last()
        thread.unread = thread.messages.exclude(sender=request.user).filter(read_at=None).count()

    return render(request, "dm/thread_list.html", {"threads": threads})


def thread_detail(request, pk):
    thread = get_my_thread(request, pk)

    # 開いた時点で相手のメッセージを既読にする
    thread.messages.exclude(sender=request.user).filter(read_at=None).update(
        read_at=timezone.now()
    )

    # 科目詳細から来たときは下書きを入れておく
    draft = ""
    subject_id = request.GET.get("subject", "")
    if subject_id.isdigit():
        subject = Subject.objects.filter(pk=subject_id).first()
        if subject:
            draft = f"「{subject.name}」の件でご相談があります。"

    context = {
        "thread": thread,
        "partner": thread.partner(request.user),
        "chat": thread.messages.select_related("sender"),
        "is_professor": request.user == thread.professor,
        "draft": draft,
    }
    return render(request, "dm/thread_detail.html", context)


# 科目詳細の「担当教授に相談する」ボタン
@require_POST
def start(request, pk):
    subject = get_object_or_404(Subject, pk=pk)
    if not request.user.is_student:
        messages.error(request, "学生アカウントからのみ相談できます。")
        return redirect(subject)

    thread, _ = Thread.objects.get_or_create(
        student=request.user, professor=subject.professor
    )
    return redirect(f"{thread.get_absolute_url()}?subject={subject.pk}")


@require_POST
def send(request, pk):
    thread = get_my_thread(request, pk)
    body = request.POST.get("body", "").strip()
    if not body:
        messages.error(request, "本文を入力してください。")
    else:
        Message.objects.create(thread=thread, sender=request.user, body=body)
        thread.save()  # updated_at を更新して一覧の先頭に出す
    return redirect(thread)


@require_POST
def ai_refuse(request, pk):
    thread = get_my_thread(request, pk)
    if request.user != thread.professor:
        return HttpResponseForbidden("担当教授だけが使えます。")

    Message.objects.create(
        thread=thread,
        sender=request.user,
        body=make_refusal(thread.student),
        is_ai=True,
    )
    thread.save()
    return redirect(thread)
