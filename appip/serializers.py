# appip/serializers.py
from rest_framework import serializers
from .models import *
from django.contrib.auth.hashers import make_password

class RolesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Roles
        fields = '__all__'

class UsersSerializer(serializers.ModelSerializer):
    role_name = serializers.CharField(source='role.role_name', read_only=True)
    password = serializers.CharField(write_only=True, required=False)
    
    class Meta:
        model = Users
        fields = [
            'id_user', 'login', 'firstname', 'surname', 'role', 'role_name',
            'avatar_url', 'balance', 'seller_rating', 'registration_date',
            'last_login', 'is_active', 'password'
        ]
        extra_kwargs = {
            'password_hash': {'write_only': True, 'required': False}
        }
    
    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = Users(**validated_data)
        if password:
            user.set_password(password)
        user.save()
        return user
    
    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance

class CategoriesSerializer(serializers.ModelSerializer):
    parent_category_name = serializers.CharField(source='parent_category.category_name', read_only=True, allow_null=True)
    
    class Meta:
        model = Categories
        fields = '__all__'

class ProductTypesSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductTypes
        fields = '__all__'

class TovarsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tovars
        fields = ['id_tovar', 'tovar_text', 'created_at', 'is_sold', 'sold_at']
        read_only_fields = ['is_sold', 'sold_at']

class ProductsTovarsSerializer(serializers.ModelSerializer):
    tovar_text = serializers.CharField(source='tovar.tovar_text', read_only=True)
    tovar_is_sold = serializers.BooleanField(source='tovar.is_sold', read_only=True)
    
    class Meta:
        model = ProductsTovars
        fields = ['id_producttovar', 'product', 'tovar', 'tovar_text', 'tovar_is_sold']

class ProductsSerializer(serializers.ModelSerializer):
    seller_name = serializers.CharField(source='seller.login', read_only=True)
    category_name = serializers.CharField(source='category.category_name', read_only=True, allow_null=True)
    product_type_name = serializers.CharField(source='product_type.type_name', read_only=True)
    
    # Статистика по товарам
    available_tovars_count = serializers.IntegerField(read_only=True)
    total_tovars_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Products
        fields = [
            'id_product', 'title', 'description', 'price', 'seller', 'seller_name',
            'category', 'category_name', 'product_type', 'product_type_name',
            'main_image_url', 'rating', 'is_auto_delivery',
            'auto_delivery_text', 'created_at', 'updated_at', 'is_active',
            'available_tovars_count', 'total_tovars_count'
        ]
    
    def get_total_tovars_count(self, obj):
        return obj.tovars.count()

class ProductCategoriesSerializer(serializers.ModelSerializer):
    product_title = serializers.CharField(source='product.title', read_only=True)
    category_name = serializers.CharField(source='category.category_name', read_only=True)
    
    class Meta:
        model = ProductCategories
        fields = '__all__'

class ProductItemsSerializer(serializers.ModelSerializer):
    product_title = serializers.CharField(source='product.title', read_only=True)
    
    class Meta:
        model = ProductItems
        fields = [
            'id_productitem', 'product', 'product_title', 'item_data', 
            'item_type', 'is_sold', 'sold_at', 'order_item', 'created_at'
        ]
        extra_kwargs = {
            'item_data': {'write_only': True}
        }

class OrdersSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.login', read_only=True)
    
    class Meta:
        model = Orders
        fields = '__all__'

class OrderItemsSerializer(serializers.ModelSerializer):
    product_title = serializers.CharField(source='product.title', read_only=True)
    order_number = serializers.CharField(source='order.id_order', read_only=True)
    
    class Meta:
        model = OrderItems
        fields = '__all__'

class ProductReviewsSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.login', read_only=True)
    product_title = serializers.CharField(source='product.title', read_only=True)
    
    class Meta:
        model = ProductReviews
        fields = '__all__'

class SellerReviewsSerializer(serializers.ModelSerializer):
    seller_name = serializers.CharField(source='seller.login', read_only=True)
    buyer_name = serializers.CharField(source='buyer.login', read_only=True)
    
    class Meta:
        model = SellerReviews
        fields = '__all__'

class WishlistsSerializer(serializers.ModelSerializer):
    product_title = serializers.CharField(source='product.title', read_only=True)
    product_price = serializers.DecimalField(source='product.price', read_only=True, max_digits=10, decimal_places=2)
    product_image = serializers.CharField(source='product.main_image_url', read_only=True)
    
    class Meta:
        model = Wishlists
        fields = '__all__'

class CartSerializer(serializers.ModelSerializer):
    product_title = serializers.CharField(source='product.title', read_only=True)
    product_price = serializers.DecimalField(source='product.price', read_only=True, max_digits=10, decimal_places=2)
    product_image = serializers.CharField(source='product.main_image_url', read_only=True)
    available_tovars_count = serializers.IntegerField(source='product.available_tovars_count', read_only=True)
    total_price = serializers.SerializerMethodField()
    
    class Meta:
        model = Cart
        fields = [
            'id_cart', 'user', 'product', 'product_title', 'product_price',
            'product_image', 'quantity', 'added_at', 'total_price', 'available_tovars_count'
        ]
    
    def get_total_price(self, obj):
        return obj.product.price * obj.quantity

# appip/serializers.py - добавьте в конец

class ChatsSerializer(serializers.ModelSerializer):
    buyer_name = serializers.CharField(source='buyer.login', read_only=True)
    seller_name = serializers.CharField(source='seller.login', read_only=True)
    product_title = serializers.CharField(source='product.title', read_only=True, allow_null=True)
    last_message = serializers.SerializerMethodField()
    
    class Meta:
        model = Chats
        fields = [
            'id_chat', 'product', 'product_title', 'buyer', 'buyer_name',
            'seller', 'seller_name', 'order', 'created_at', 'last_message_at',
            'is_active', 'last_message'
        ]
    
    def get_last_message(self, obj):
        last_message = obj.messages_set.last()
        if last_message:
            return {
                'text': last_message.message_text[:100],
                'sender': last_message.sender.login,
                'time': last_message.sent_at
            }
        return None

class MessagesSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source='sender.login', read_only=True)
    sender_avatar = serializers.CharField(source='sender.avatar_url', read_only=True)
    
    class Meta:
        model = Messages
        fields = [
            'id_message', 'chat', 'sender', 'sender_name', 'sender_avatar',
            'message_text', 'sent_at', 'is_read', 'read_at'
        ]
        read_only_fields = ['sent_at', 'is_read', 'read_at']




class TransactionsSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.login', read_only=True)
    
    class Meta:
        model = Transactions
        fields = '__all__'

class UserActivityLogSerializer(serializers.ModelSerializer):
    user_login = serializers.CharField(source='user.login', read_only=True)
    user_name = serializers.SerializerMethodField()
    action_display = serializers.CharField(source='get_action_display', read_only=True)

    class Meta:
        model = UserActivityLog
        fields = [
            'id_log', 'user', 'user_login', 'user_name', 'action', 'action_display',
            'description', 'ip_address', 'user_agent', 'created_at', 'additional_data'
        ]

    def get_user_name(self, obj):
        if obj.user:
            return f"{obj.user.firstname} {obj.user.surname}"
        return 'Анонимный пользователь'



class PromoCodesSerializer(serializers.ModelSerializer):
    status_display = serializers.SerializerMethodField()
    is_valid = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = PromoCodes
        fields = [
            'id_promocode', 'code', 'discount_percent', 'is_active',
            'created_at', 'expires_at', 'usage_limit', 'used_count',
            'status_display', 'is_valid'
        ]
    
    def get_status_display(self, obj):
        if obj.is_active and (not obj.expires_at or obj.expires_at > timezone.now()):
            return 'Активен'
        elif not obj.is_active:
            return 'Неактивен'
        else:
            return 'Истек'