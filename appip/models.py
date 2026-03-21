# appip/models.py
from django.db import models
from django.contrib.auth.hashers import make_password, check_password

class Roles(models.Model):
    id_role = models.AutoField(primary_key=True)
    role_name = models.CharField(max_length=50, unique=True)

    class Meta:
        db_table = 'roles'
        
    def __str__(self):
        return self.role_name


class Users(models.Model):
    id_user = models.AutoField(primary_key=True)
    login = models.EmailField(max_length=50, unique=True)
    password_hash = models.CharField(max_length=255)
    firstname = models.CharField(max_length=100)
    surname = models.CharField(max_length=100)
    role = models.ForeignKey(Roles, on_delete=models.CASCADE, db_column='role_id')
    avatar_url = models.CharField(max_length=500, blank=True, null=True)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    seller_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    registration_date = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'users'
        
    def __str__(self):
        return f"{self.firstname} {self.surname} ({self.login})"
    
    def set_password(self, raw_password):
        self.password_hash = make_password(raw_password)
    
    def check_password(self, raw_password):
        return check_password(raw_password, self.password_hash)


class Categories(models.Model):
    id_category = models.AutoField(primary_key=True)
    category_name = models.CharField(max_length=100, unique=True)
    parent_category = models.ForeignKey('self', on_delete=models.SET_NULL, 
                                        null=True, blank=True, 
                                        db_column='parent_category_id')
    description = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'categories'
        
    def __str__(self):
        return self.category_name


class ProductTypes(models.Model):
    id_producttype = models.AutoField(primary_key=True)
    type_name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'producttypes'
        
    def __str__(self):
        return self.type_name


class Tovars(models.Model):
    """Таблица товаров (ключи, аккаунты, файлы)"""
    id_tovar = models.AutoField(primary_key=True)
    tovar_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_sold = models.BooleanField(default=False)
    sold_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'tovars'
        
    def __str__(self):
        return f"Товар #{self.id_tovar}"


class Products(models.Model):
    id_product = models.AutoField(primary_key=True)
    title = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    seller = models.ForeignKey(Users, on_delete=models.CASCADE, db_column='seller_id')
    category = models.ForeignKey(Categories, on_delete=models.SET_NULL, 
                                null=True, blank=True, db_column='category_id')
    product_type = models.ForeignKey(ProductTypes, on_delete=models.CASCADE, 
                                    db_column='product_type_id')
    main_image_url = models.CharField(max_length=500, blank=True, null=True)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    is_auto_delivery = models.BooleanField(default=False)
    auto_delivery_text = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    # Добавляем связь с товарами
    tovars = models.ManyToManyField(Tovars, through='ProductsTovars', related_name='products')

    class Meta:
        db_table = 'products'
    
    @property
    def image_url(self):
        if self.main_image_url:
            return f'/media/products/{self.main_image_url}'
        return '/media/products/default.jpg'
    
    @property
    def available_tovars_count(self):
        """Количество доступных товаров"""
        return self.tovars.filter(is_sold=False).count()
    
    @property
    def stock_quantity(self):
        """Свойство для обратной совместимости"""
        return self.available_tovars_count

    def __str__(self):
        return self.title


class ProductsTovars(models.Model):
    """Связь продуктов и товаров"""
    id_producttovar = models.AutoField(primary_key=True)
    product = models.ForeignKey(Products, on_delete=models.CASCADE, db_column='product_id')
    tovar = models.ForeignKey(Tovars, on_delete=models.CASCADE, db_column='tovar_id')

    class Meta:
        db_table = 'productstovars'
        unique_together = (('product', 'tovar'),)


class ProductCategories(models.Model):
    id_productcategory = models.AutoField(primary_key=True)
    product = models.ForeignKey(Products, on_delete=models.CASCADE, db_column='product_id')
    category = models.ForeignKey(Categories, on_delete=models.CASCADE, db_column='category_id')

    class Meta:
        db_table = 'productcategories'
        unique_together = (('product', 'category'),)


class ProductItems(models.Model):
    ITEM_TYPES = [
        ('activation_key', 'Ключ активации'),
        ('account', 'Аккаунт (логин:пароль)'),
        ('instruction', 'Инструкция/текст'),
        ('file', 'Файл для скачивания')
    ]
    
    id_productitem = models.AutoField(primary_key=True)
    product = models.ForeignKey(Products, on_delete=models.CASCADE, db_column='product_id')
    item_data = models.TextField()
    item_type = models.CharField(max_length=50, choices=ITEM_TYPES, default='activation_key')
    is_sold = models.BooleanField(default=False)
    sold_at = models.DateTimeField(blank=True, null=True)
    order_item = models.ForeignKey('OrderItems', on_delete=models.SET_NULL, 
                                  null=True, blank=True, db_column='order_item_id')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'productitems'
        
    def __str__(self):
        return f"{self.product.title} - {self.item_type}"


class Orders(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Ожидание получения'),  
        ('completed', 'Завершен'),
        ('cancelled', 'Отменен')
    ]
    
    id_order = models.AutoField(primary_key=True)
    user = models.ForeignKey(Users, on_delete=models.CASCADE, db_column='user_id')
    order_created_at = models.DateTimeField(auto_now_add=True)
    total_cost = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='pending')
    payment_method = models.CharField(max_length=50, blank=True, null=True)
    payment_reference = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        db_table = 'orders'
        
    def __str__(self):
        return f"Заказ #{self.id_order} - {self.user.login}"


class OrderItems(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Ожидание'),
        ('delivered', 'Доставлен'),
        ('cancelled', 'Отменен')
    ]
    
    id_orderitem = models.AutoField(primary_key=True)
    order = models.ForeignKey(Orders, on_delete=models.CASCADE, db_column='order_id')
    product = models.ForeignKey(Products, on_delete=models.CASCADE, db_column='product_id')
    product_item = models.ForeignKey(ProductItems, on_delete=models.SET_NULL, 
                                   null=True, blank=True, db_column='product_item_id')

    tovar = models.ForeignKey(Tovars, on_delete=models.SET_NULL,
                             null=True, blank=True, db_column='tovar_id')
    quantity = models.IntegerField(default=1)
    price_at_time_of_purchase = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='pending')

    class Meta:
        db_table = 'orderitems'
        
    def __str__(self):
        return f"{self.product.title} в заказе #{self.order.id_order}"


class ProductReviews(models.Model):
    id_review = models.AutoField(primary_key=True)
    product = models.ForeignKey(Products, on_delete=models.CASCADE, db_column='product_id')
    user = models.ForeignKey(Users, on_delete=models.CASCADE, db_column='user_id')
    rating = models.IntegerField()
    review_text = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_edited = models.BooleanField(default=False)

    class Meta:
        db_table = 'productreviews'
        unique_together = (('user', 'product'),)
        
    def __str__(self):
        return f"Отзыв от {self.user.login} на {self.product.title}"


class SellerReviews(models.Model):
    id_sellerreview = models.AutoField(primary_key=True)
    seller = models.ForeignKey(Users, on_delete=models.CASCADE, db_column='seller_id', 
                              related_name='seller_reviews')
    buyer = models.ForeignKey(Users, on_delete=models.CASCADE, db_column='buyer_id',
                             related_name='buyer_reviews')
    order = models.ForeignKey(Orders, on_delete=models.SET_NULL, 
                             null=True, blank=True, db_column='order_id')
    rating = models.IntegerField()
    review_text = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'sellerreviews'
        unique_together = (('buyer', 'seller'),)
        
    def __str__(self):
        return f"Отзыв на {self.seller.login} от {self.buyer.login}"


class Wishlists(models.Model):
    id_wishlist = models.AutoField(primary_key=True)
    user = models.ForeignKey(Users, on_delete=models.CASCADE, db_column='user_id')
    product = models.ForeignKey(Products, on_delete=models.CASCADE, db_column='product_id')
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'wishlists'
        unique_together = (('user', 'product'),)


class Cart(models.Model):
    id_cart = models.AutoField(primary_key=True)
    user = models.ForeignKey(Users, on_delete=models.CASCADE, db_column='user_id')
    product = models.ForeignKey(Products, on_delete=models.CASCADE, db_column='product_id')
    quantity = models.IntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'cart'
        unique_together = (('user', 'product'),)




class Chats(models.Model):
    id_chat = models.AutoField(primary_key=True)
    product = models.ForeignKey(Products, on_delete=models.SET_NULL, 
                               null=True, blank=True, db_column='product_id')
    buyer = models.ForeignKey(Users, on_delete=models.CASCADE, db_column='buyer_id',
                             related_name='buyer_chats')
    seller = models.ForeignKey(Users, on_delete=models.CASCADE, db_column='seller_id',
                              related_name='seller_chats')
    order = models.ForeignKey(Orders, on_delete=models.SET_NULL, 
                             null=True, blank=True, db_column='order_id')
    created_at = models.DateTimeField(auto_now_add=True)
    last_message_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    

    class Meta:
        db_table = 'chats'
        unique_together = (('product', 'buyer', 'seller'),)

class Messages(models.Model):
    id_message = models.AutoField(primary_key=True)
    chat = models.ForeignKey(Chats, on_delete=models.CASCADE, db_column='chat_id')
    sender = models.ForeignKey(Users, on_delete=models.CASCADE, db_column='sender_id')
    message_text = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'messages'
        ordering = ['sent_at']

    def __str__(self):
        return f"Сообщение от {self.sender.login}: {self.message_text[:50]}..."


class Transactions(models.Model):
    TYPE_CHOICES = [
        ('deposit', 'Пополнение'),
        ('withdrawal', 'Вывод'),
        ('purchase', 'Покупка'),
        ('sale', 'Продажа'),
        ('refund', 'Возврат')
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Ожидание'),
        ('completed', 'Завершено'),
        ('failed', 'Неудачно'),
        ('cancelled', 'Отменено')
    ]
    
    id_transaction = models.AutoField(primary_key=True)
    user = models.ForeignKey(Users, on_delete=models.CASCADE, db_column='user_id')
    order = models.ForeignKey(Orders, on_delete=models.SET_NULL, 
                             null=True, blank=True, db_column='order_id')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_type = models.CharField(max_length=50, choices=TYPE_CHOICES)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    reference = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        db_table = 'transactions'
        
    def __str__(self):
        return f"{self.transaction_type} - {self.amount} - {self.user.login}"


class UserActivityLog(models.Model):
    ACTION_CHOICES = [
        ('login', 'Вход в систему'),
        ('logout', 'Выход из системы'),
        ('register', 'Регистрация'),
        ('view_product', 'Просмотр товара'),
        ('add_to_cart', 'Добавление в корзину'),
        ('remove_from_cart', 'Удаление из корзины'),
        ('add_to_wishlist', 'Добавление в вишлист'),
        ('remove_from_wishlist', 'Удаление из вишлиста'),
        ('create_order', 'Создание заказа'),
        ('add_review', 'Добавление отзыва'),
        ('edit_review', 'Редактирование отзыва'),
        ('delete_review', 'Удаление отзыва'),
        ('update_profile', 'Обновление профиля'),
        ('change_password', 'Смена пароля'),
        ('download_receipt', 'Скачивание чека'),
        ('search', 'Поиск'),
        ('add_product', 'Добавление товара'),
        ('edit_product', 'Редактирование товара'),
        ('delete_product', 'Удаление товара'),
        ('send_message', 'Отправка сообщения'),
        ('deposit', 'Пополнение баланса'),
        ('withdrawal', 'Вывод средств'),
        ('admin_action', 'Действие администратора'),
        ('manager_action', 'Действие менеджера'),
    ]

    id_log = models.AutoField(primary_key=True)
    user = models.ForeignKey(Users, on_delete=models.CASCADE, db_column='user_id', null=True, blank=True)
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    description = models.TextField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    additional_data = models.JSONField(null=True, blank=True)

    class Meta:
        db_table = 'useractivitylogs'
        ordering = ['-created_at']

    def __str__(self):
        username = self.user.login if self.user else 'Анонимный пользователь'
        return f"{username} - {self.get_action_display()} - {self.created_at}"




class ManagerChats(models.Model):
    """Чаты менеджера с пользователями"""
    id_manager_chat = models.AutoField(primary_key=True)
    manager = models.ForeignKey(Users, on_delete=models.CASCADE, 
                               db_column='manager_id',
                               related_name='manager_chats')
    user = models.ForeignKey(Users, on_delete=models.CASCADE, 
                            db_column='user_id',
                            related_name='user_manager_chats')
    chat = models.ForeignKey(Chats, on_delete=models.SET_NULL,
                            null=True, blank=True, db_column='chat_id')
    created_at = models.DateTimeField(auto_now_add=True)
    last_message_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'managerchats'
        unique_together = (('manager', 'user'),)
        verbose_name = 'Чат менеджера'
        verbose_name_plural = 'Чаты менеджера'
    
    def __str__(self):
        return f"Чат менеджера {self.manager.login} с {self.user.login}"




class TelegramManager(models.Model):
    """Связь менеджера с Telegram и VK чатами"""
    id = models.AutoField(primary_key=True)
    manager = models.ForeignKey(Users, on_delete=models.CASCADE, related_name='messenger_connections')
    
    # Telegram
    telegram_chat_id = models.CharField(max_length=100, blank=True, null=True)
    telegram_username = models.CharField(max_length=100, blank=True)
    
    # VK
    vk_peer_id = models.BigIntegerField(blank=True, null=True) 
    vk_username = models.CharField(max_length=100, blank=True)
    
    # Общие поля
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'messenger_managers'
        verbose_name = 'Менеджер мессенджера'
        verbose_name_plural = 'Менеджеры мессенджеров'

    def __str__(self):
        tg = f"TG: {self.telegram_username}" if self.telegram_username else "TG: нет"
        vk = f"VK: {self.vk_username}" if self.vk_username else "VK: нет"
        return f"{self.manager.login} ({tg}, {vk})"

class ChatSync(models.Model):
    """Синхронизация между чатами сайта и Telegram"""
    id = models.AutoField(primary_key=True)
    site_chat = models.ForeignKey(Chats, on_delete=models.CASCADE, related_name='telegram_syncs')
    telegram_message_id = models.CharField(max_length=100, blank=True, null=True)
    last_sync_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'chat_sync'
        verbose_name = 'Синхронизация чата'
        verbose_name_plural = 'Синхронизации чатов'

    def __str__(self):
        return f"Чат #{self.site_chat.id_chat}"