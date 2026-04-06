import asyncio
from datetime import datetime

from sqlalchemy import BigInteger, Column, DateTime, Float, ForeignKey, Integer, JSON, String, Text, Boolean, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.orm import relationship
from config import DATABASE_URL

engine = create_async_engine(DATABASE_URL, echo=False, pool_pre_ping=True)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False)
    phone = Column(String(20), nullable=True)
    full_name = Column(String(100), nullable=True)
    username = Column(String(100), nullable=True)
    language = Column(String(5), default="uz")
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    orders = relationship("Order", back_populates="user")
    cart_items = relationship("CartItem", back_populates="user")
    reviews = relationship("Review", back_populates="user")
    wishlist = relationship("Wishlist", back_populates="user")

class Category(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True)
    name_uz = Column(String(100), nullable=False)
    name_ru = Column(String(100), nullable=False)
    image_url = Column(String(500), nullable=True)
    parent_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)
    products = relationship("Product", back_populates="category")
    children = relationship("Category", backref="parent", remote_side=[id])

class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True)
    title_uz = Column(String(200), nullable=False)
    title_ru = Column(String(200), nullable=False)
    description_uz = Column(Text, nullable=True)
    description_ru = Column(Text, nullable=True)
    price = Column(Float, nullable=False)
    old_price = Column(Float, nullable=True)
    images = Column(JSON, default=list)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    tags = Column(JSON, default=list)
    is_active = Column(Boolean, default=True)
    stock = Column(Integer, default=100)
    created_at = Column(DateTime, default=datetime.utcnow)
    category = relationship("Category", back_populates="products")
    cart_items = relationship("CartItem", back_populates="product")
    order_items = relationship("OrderItem", back_populates="product")
    reviews = relationship("Review", back_populates="product")
    wishlist = relationship("Wishlist", back_populates="product")

class CartItem(Base):
    __tablename__ = "cart_items"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    user = relationship("User", back_populates="cart_items")
    product = relationship("Product", back_populates="cart_items")

class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(String(50), default="pending")
    total_price = Column(Float, nullable=False)
    delivery_price = Column(Float, default=0)
    address = Column(Text, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    distance_km = Column(Float, nullable=True)
    comment = Column(Text, nullable=True)
    coupon_code = Column(String(50), nullable=True)
    discount_amount = Column(Float, default=0)
    group_message_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user = relationship("User", back_populates="orders")
    items = relationship("OrderItem", back_populates="order")

class OrderItem(Base):
    __tablename__ = "order_items"
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)
    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")

class Coupon(Base):
    __tablename__ = "coupons"
    id = Column(Integer, primary_key=True)
    code = Column(String(50), unique=True, nullable=False)
    discount_type = Column(String(20), default="percent")  # percent | fixed
    discount_value = Column(Float, nullable=False)
    min_order_amount = Column(Float, default=0)
    max_uses = Column(Integer, nullable=True)
    used_count = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Review(Base):
    __tablename__ = "reviews"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    rating = Column(Integer, nullable=False)
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    user = relationship("User", back_populates="reviews")
    product = relationship("Product", back_populates="reviews")

class Wishlist(Base):
    __tablename__ = "wishlist"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    user = relationship("User", back_populates="wishlist")
    product = relationship("Product", back_populates="wishlist")

class AdminSession(Base):
    __tablename__ = "admin_sessions"
    id = Column(Integer, primary_key=True)
    token = Column(String(200), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)

class ShopSettings(Base):
    __tablename__ = "shop_settings"
    id = Column(Integer, primary_key=True)
    shop_name_uz = Column(String(200), default="Do'kon")
    shop_name_ru = Column(String(200), default="Магазин")
    all_products_title_uz = Column(String(200), default="Barcha mahsulotlar")
    all_products_title_ru = Column(String(200), default="Все товары")
    logo_url = Column(String(500), nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class BrowserAuthCode(Base):
    __tablename__ = "browser_auth_codes"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    phone = Column(String(20), nullable=False)
    code = Column(String(10), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

async def init_db():
    last_error = None
    for attempt in range(1, 11):
        try:
            async with engine.begin() as conn:
                await conn.execute(text("SELECT 1"))
                await conn.run_sync(Base.metadata.create_all)
            return
        except Exception as exc:
            last_error = exc
            if attempt == 10:
                raise
            await asyncio.sleep(2)

    raise last_error

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
