# appip/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .views import ProductViewSet, CartViewSet, OrderViewSet


router = DefaultRouter()
router.register(r'api/products', ProductViewSet, basename='product')
router.register(r'api/cart', CartViewSet, basename='cart')
router.register(r'api/orders', OrderViewSet, basename='order')

urlpatterns = [
    # Основные страницы
    path('', views.home, name='home'),
    path('products/', views.products_list, name='products_list'),
    path('product/<int:product_id>/', views.product_detail, name='product_detail'),
    path('search/', views.search_view, name='search'),
    
    # Аутентификация
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('password-recovery/', views.password_recovery, name='password_recovery'),  
    
    # Пользовательский профиль
    path('profile/', views.profile, name='profile'),
    path('profile/update/', views.update_profile, name='update_profile'),
    path('profile/change-password/', views.change_password, name='change_password'),
    
    path('api/sellers/<int:seller_id>/add_review/', views.add_seller_review, name='add_seller_review'),
    path('api/sellers/edit_review/', views.edit_seller_review, name='edit_seller_review'),
    path('api/sellers/delete_review/', views.delete_seller_review, name='delete_seller_review'),
    
    
    # appip/urls.py - добавьте в urlpatterns
    path('admin-panel/roles/', views.admin_roles, name='admin_roles'),
    path('admin-panel/roles/create/', views.create_role, name='create_role'),
    path('admin-panel/roles/edit/<int:role_id>/', views.edit_role, name='edit_role'),
    path('admin-panel/roles/delete/<int:role_id>/', views.delete_role, name='delete_role'),


    # appip/urls.py - добавьте в urlpatterns

    # Чат менеджера
    path('api/manager/users/', views.get_all_users_for_manager, name='get_all_users_for_manager'),
    path('api/manager/start-chat/', views.manager_start_chat, name='manager_start_chat'),
    path('api/manager/chat/<int:chat_id>/messages/', views.get_manager_chat_messages, name='get_manager_chat_messages'),
    path('api/manager/send-message/', views.send_message, name='manager_send_message'),


    # appip/urls.py - добавьте в urlpatterns после admin_logs

    path('admin-panel/data-recovery/', views.admin_data_recovery, name='admin_data_recovery'),
    path('admin-panel/backup/create/', views.admin_create_backup, name='admin_create_backup'),
    path('admin-panel/backup/download/<str:filename>/', views.admin_download_backup, name='admin_download_backup'),
    path('admin-panel/backup/restore/', views.admin_restore_backup, name='admin_restore_backup'),
    path('admin-panel/backup/delete/<str:filename>/', views.admin_delete_backup, name='admin_delete_backup'),
    path('admin-panel/backup/upload/', views.admin_upload_backup, name='admin_upload_backup'),


    # appip/urls.py - добавьте в urlpatterns после admin_roles

    path('admin-panel/users/', views.admin_users, name='admin_users'),
    path('admin-panel/users/create/', views.create_user, name='create_user'),
    path('admin-panel/users/edit/<int:user_id>/', views.edit_user, name='edit_user'),
    path('admin-panel/users/delete/<int:user_id>/', views.delete_user, name='delete_user'),
    path('admin-panel/users/toggle-active/<int:user_id>/', views.toggle_user_active, name='toggle_user_active'),


    # appip/urls.py - добавьте в urlpatterns после admin_users

    path('admin-panel/products/', views.admin_products, name='admin_products'),
    path('admin-panel/products/create/', views.admin_create_product, name='admin_create_product'),
    path('admin-panel/products/edit/<int:product_id>/', views.admin_edit_product, name='admin_edit_product'),
    path('admin-panel/products/delete/<int:product_id>/', views.admin_delete_product, name='admin_delete_product'),
    path('admin-panel/products/toggle-active/<int:product_id>/', views.admin_toggle_product_active, name='admin_toggle_product_active'),
    path('admin-panel/products/tovars/<int:product_id>/', views.admin_product_tovars, name='admin_product_tovars'),
    path('admin-panel/products/delete-tovar/<int:tovar_id>/', views.admin_delete_tovar, name='admin_delete_tovar'),


    # appip/urls.py - добавьте в urlpatterns после admin_products

    path('admin-panel/orders/', views.admin_orders, name='admin_orders'),
    path('admin-panel/orders/<int:order_id>/', views.admin_order_detail, name='admin_order_detail'),
    path('admin-panel/orders/update-status/<int:order_id>/', views.admin_update_order_status, name='admin_update_order_status'),
    path('admin-panel/orders/delete/<int:order_id>/', views.admin_delete_order, name='admin_delete_order'),


    # appip/urls.py - добавьте в urlpatterns после admin_orders

    path('admin-panel/wishlists/', views.admin_wishlists, name='admin_wishlists'),
    path('admin-panel/wishlists/delete/<int:wishlist_id>/', views.admin_delete_wishlist, name='admin_delete_wishlist'),
    # appip/urls.py - добавьте в urlpatterns после admin_wishlists

    path('admin-panel/carts/', views.admin_carts, name='admin_carts'),
    path('admin-panel/carts/delete/<int:cart_id>/', views.admin_delete_cart, name='admin_delete_cart'),

    # appip/urls.py - добавьте в urlpatterns после admin_carts

    path('admin-panel/reviews/', views.admin_reviews, name='admin_reviews'),
    path('admin-panel/reviews/delete-product-review/<int:review_id>/', views.admin_delete_product_review, name='admin_delete_product_review'),
    path('admin-panel/reviews/delete-seller-review/<int:review_id>/', views.admin_delete_seller_review, name='admin_delete_seller_review'),


    # appip/urls.py - добавьте в urlpatterns после admin_reviews

    path('admin-panel/logs/', views.admin_logs, name='admin_logs'),
    path('admin-panel/logs/delete/<int:log_id>/', views.admin_delete_log, name='admin_delete_log'),
    path('admin-panel/logs/clear-all/', views.admin_clear_all_logs, name='admin_clear_all_logs'),

    # Корзина
    path('cart/', views.cart_view, name='cart'),
    path('cart/add/', views.add_to_cart, name='add_to_cart'),
    path('cart/update/<int:item_id>/', views.update_cart_item, name='update_cart_item'),
    path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    
    # Вишлист
    path('wishlist/', views.wishlist_view, name='wishlist'),
    path('wishlist/toggle/', views.toggle_wishlist, name='toggle_wishlist'),


    # appip/urls.py - добавьте в urlpatterns

    # Управление товарами пользователя
    path('profile/products/', views.user_products, name='user_products'),
    path('profile/products/create/', views.create_product, name='create_product'),
    path('profile/products/edit/<int:product_id>/', views.edit_product, name='edit_product'),
    path('profile/products/delete/<int:product_id>/', views.delete_product, name='delete_product'),
    path('profile/products/delete-tovar/', views.delete_tovar, name='delete_tovar'),
    path('profile/products/stats/<int:product_id>/', views.product_stats, name='product_stats'),
    

    # Чат
    path('chat/buyer/', views.chat_buyer, name='chat_buyer'),
    path('chat/buyer/<int:chat_id>/', views.chat_buyer, name='chat_buyer_detail'),
    path('chat/seller/', views.chat_seller, name='chat_seller'),
    path('chat/seller/<int:chat_id>/', views.chat_seller, name='chat_seller_detail'),
    path('api/send-message/', views.send_message, name='send_message'),
    path('api/chat/<int:chat_id>/messages/', views.get_messages, name='get_messages'),
    path('api/close-chat/', views.close_chat, name='close_chat'),

    # Заказы
    path('orders/', views.orders_view, name='orders'),
    path('orders/<int:order_id>/', views.order_detail, name='order_detail'),
    path('orders/create/', views.create_order, name='create_order'),
    path('orders/<int:order_id>/confirm/', views.confirm_order, name='confirm_order'),  # НОВЫЙ МАРШРУТ
    path('orders/receipt/<int:order_id>/', views.download_receipt, name='download_receipt'),
    
    # Админ панель
    path('admin-panel/', views.admin_dashboard, name='admin_dashboard'),
    
    # API эндпоинты
    path('api/categories/', views.api_categories, name='api_categories'),
    path('api/product-types/', views.api_product_types, name='api_product_types'),
    path('api/register/', views.api_register, name='api_register'),
    path('api/login/', views.api_login, name='api_login'),
   

    # Пополнение баланса

    path('profile/deposit/', views.deposit_balance, name='deposit_balance'),
    path('payment/notification/', views.payment_notification, name='payment_notification'),
    path('payment/success/', views.payment_success, name='payment_success'),
    path('payment/fail/', views.payment_fail, name='payment_fail'),
    path('payment/check/<int:transaction_id>/', views.check_payment_status, name='check_payment_status'),

    
    # Включение router'ов
    path('', include(router.urls)),
]