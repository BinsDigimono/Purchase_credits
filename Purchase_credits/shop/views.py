from django.contrib import messages
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .models import CartItem, Order, OrderItem, Subject


# 買えない理由を返す。買えるなら None
def purchase_error(user, subject):
    if not subject.is_active:
        return "現在この科目は取り扱っていません。"
    if subject.is_sold_out:
        return "この科目は残り枠がありません。"
    if not user.is_student:
        return "学生アカウントでのみ申し込めます。"
    if subject.professor_id == user.pk:
        return "自分の出品には申し込めません。"
    if OrderItem.objects.filter(order__user=user, subject=subject).exists():
        return "この科目はすでに申し込み済みです。"
    return None


def subject_list(request):
    subjects = Subject.objects.filter(is_active=True, stock__gt=0).select_related("professor")
    keyword = request.GET.get("q", "")
    if keyword:
        subjects = subjects.filter(
            Q(name__icontains=keyword)
            | Q(code__icontains=keyword)
            | Q(department__icontains=keyword)
            | Q(professor__display_name__icontains=keyword)
        )
    return render(request, "shop/subject_list.html", {"subjects": subjects, "q": keyword})


def subject_detail(request, pk):
    subject = get_object_or_404(Subject, pk=pk)
    context = {
        "subject": subject,
        "error": purchase_error(request.user, subject),
        "in_cart": CartItem.objects.filter(user=request.user, subject=subject).exists(),
    }
    return render(request, "shop/subject_detail.html", context)


def cart(request):
    items = CartItem.objects.filter(user=request.user).select_related("subject")
    total = sum(item.subject.price for item in items)
    return render(request, "shop/cart.html", {"items": items, "total": total})


@require_POST
def cart_add(request, pk):
    subject = get_object_or_404(Subject, pk=pk)
    error = purchase_error(request.user, subject)
    if error:
        messages.error(request, error)
    else:
        CartItem.objects.get_or_create(user=request.user, subject=subject)
        messages.success(request, f"「{subject.name}」をカートに入れました。")
    return redirect("shop:subject_detail", pk=pk)


@require_POST
def cart_remove(request, pk):
    CartItem.objects.filter(user=request.user, subject_id=pk).delete()
    return redirect("shop:cart")


@require_POST
@transaction.atomic
def checkout(request):
    items = list(CartItem.objects.filter(user=request.user).select_related("subject"))
    if not items:
        messages.error(request, "カートが空です。")
        return redirect("shop:cart")

    # 1件でも買えないものがあれば、何もせずカートに戻す
    for item in items:
        error = purchase_error(request.user, item.subject)
        if error:
            messages.error(request, f"{item.subject.name}: {error}")
            return redirect("shop:cart")

    order = Order.objects.create(user=request.user)
    total = 0
    for item in items:
        subject = item.subject
        OrderItem.objects.create(
            order=order,
            subject=subject,
            subject_code=subject.code,
            subject_name=subject.name,
            professor_name=str(subject.professor),
            price=subject.price,
        )
        subject.stock -= 1
        subject.save()
        total += subject.price

    order.total_price = total
    order.save()
    CartItem.objects.filter(user=request.user).delete()

    messages.success(request, "申し込みが完了しました。")
    return redirect("shop:order_detail", pk=order.pk)


def order_list(request):
    orders = Order.objects.filter(user=request.user).prefetch_related("items")
    return render(request, "shop/order_list.html", {"orders": orders})


def order_detail(request, pk):
    # 他人の申込は見られないようにする
    order = get_object_or_404(Order, pk=pk, user=request.user)
    return render(request, "shop/order_detail.html", {"order": order})
