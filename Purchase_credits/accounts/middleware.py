from django.shortcuts import render

# 未ログインでも見せるページ
PUBLIC_PATHS = ["/", "/robots.txt", "/favicon.ico"]


# 未ログインでトップ以外を開いたら 404 にする
class HideSiteMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path
        hidden = path not in PUBLIC_PATHS and not path.startswith("/static/")
        if hidden and not request.user.is_authenticated:
            return render(request, "404.html", status=404)
        return self.get_response(request)
