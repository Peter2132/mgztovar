# appip/middleware.py
class AdminAccessMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith('/admin-panel/'):
            from django.shortcuts import redirect
            from django.contrib import messages
            
            if not request.session.get('user_id'):
                messages.error(request, 'Требуется авторизация')
                return redirect('login')
            
            
            from .models import Users
            try:
                user = Users.objects.get(id_user=request.session.get('user_id'))
                
                if user.role_id not in [1, 3]:
                    messages.error(request, 'Недостаточно прав для доступа')
                    return redirect('home')
            except Users.DoesNotExist:
                messages.error(request, 'Пользователь не найден')
                return redirect('login')
        
        return self.get_response(request)