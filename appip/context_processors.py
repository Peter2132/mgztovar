# appip/context_processors.py
def user_context(request):
    return {
        'user': {
            'id': request.session.get('user_id'),
            'login': request.session.get('user_login'),
            'name': request.session.get('user_name'),
            'role': request.session.get('user_role'),
            'role_id': request.session.get('user_role_id'),
            'is_authenticated': 'user_id' in request.session,
            'is_admin': request.session.get('user_role_id') == 1,
            'is_manager': request.session.get('user_role_id') == 3,
            'is_user': request.session.get('user_role_id') == 2,
        }
    }