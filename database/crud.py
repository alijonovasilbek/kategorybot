from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, and_
from sqlalchemy.orm import selectinload
from datetime import datetime, date
from .db import (User, Category, Product, CartItem, Order, OrderItem,
                 Coupon, Review, Wishlist, AdminSession, AsyncSessionLocal)

# USER
async def get_or_create_user(telegram_id, full_name=None, username=None):
    async with AsyncSessionLocal() as db:
        r = await db.execute(select(User).where(User.telegram_id == telegram_id))
        user = r.scalar_one_or_none()
        if not user:
            user = User(telegram_id=telegram_id, full_name=full_name, username=username)
            db.add(user); await db.commit(); await db.refresh(user)
        return user

async def update_user_phone(telegram_id, phone):
    async with AsyncSessionLocal() as db:
        await db.execute(update(User).where(User.telegram_id == telegram_id).values(phone=phone, is_verified=True))
        await db.commit()

async def update_user_language(telegram_id, lang):
    async with AsyncSessionLocal() as db:
        await db.execute(update(User).where(User.telegram_id == telegram_id).values(language=lang))
        await db.commit()

async def get_user(telegram_id):
    async with AsyncSessionLocal() as db:
        r = await db.execute(select(User).where(User.telegram_id == telegram_id))
        return r.scalar_one_or_none()

async def get_user_by_id(user_id):
    async with AsyncSessionLocal() as db:
        r = await db.execute(select(User).where(User.id == user_id))
        return r.scalar_one_or_none()

async def get_all_users():
    async with AsyncSessionLocal() as db:
        return (await db.execute(select(User))).scalars().all()

# CATEGORIES
async def get_categories(parent_id=None):
    async with AsyncSessionLocal() as db:
        q = select(Category).where(Category.is_active == True, Category.parent_id == parent_id).order_by(Category.sort_order)
        return (await db.execute(q)).scalars().all()

async def get_category(cat_id):
    async with AsyncSessionLocal() as db:
        return (await db.execute(select(Category).where(Category.id == cat_id))).scalar_one_or_none()

async def create_category(name_uz, name_ru, image_url=None, parent_id=None):
    async with AsyncSessionLocal() as db:
        cat = Category(name_uz=name_uz, name_ru=name_ru, image_url=image_url, parent_id=parent_id)
        db.add(cat); await db.commit(); await db.refresh(cat)
        return cat

async def update_category(cat_id, **kwargs):
    async with AsyncSessionLocal() as db:
        await db.execute(update(Category).where(Category.id == cat_id).values(**kwargs))
        await db.commit()

async def delete_category(cat_id):
    async with AsyncSessionLocal() as db:
        await db.execute(delete(Category).where(Category.id == cat_id))
        await db.commit()

async def get_all_categories():
    async with AsyncSessionLocal() as db:
        return (await db.execute(select(Category).order_by(Category.sort_order))).scalars().all()

# PRODUCTS
async def get_products(category_id=None, search=None, limit=50, offset=0):
    async with AsyncSessionLocal() as db:
        q = select(Product).where(Product.is_active == True)
        if category_id:
            q = q.where(Product.category_id == category_id)
        if search:
            q = q.where((Product.title_uz.ilike(f"%{search}%")) | (Product.title_ru.ilike(f"%{search}%")))
        return (await db.execute(q.offset(offset).limit(limit))).scalars().all()

async def get_product(product_id):
    async with AsyncSessionLocal() as db:
        return (await db.execute(select(Product).where(Product.id == product_id))).scalar_one_or_none()

async def get_similar_products(product_id, category_id, limit=6):
    async with AsyncSessionLocal() as db:
        q = select(Product).where(Product.is_active == True, Product.id != product_id, Product.category_id == category_id).limit(limit)
        return (await db.execute(q)).scalars().all()

async def create_product(data):
    async with AsyncSessionLocal() as db:
        p = Product(**data); db.add(p); await db.commit(); await db.refresh(p)
        return p

async def update_product(product_id, **kwargs):
    async with AsyncSessionLocal() as db:
        await db.execute(update(Product).where(Product.id == product_id).values(**kwargs))
        await db.commit()

async def delete_product(product_id):
    async with AsyncSessionLocal() as db:
        await db.execute(delete(Product).where(Product.id == product_id))
        await db.commit()

async def get_all_products():
    async with AsyncSessionLocal() as db:
        return (await db.execute(select(Product).options(selectinload(Product.category)))).scalars().all()

# CART
async def get_cart(user_id):
    async with AsyncSessionLocal() as db:
        q = select(CartItem).options(selectinload(CartItem.product)).where(CartItem.user_id == user_id)
        return (await db.execute(q)).scalars().all()

async def add_to_cart(user_id, product_id, quantity=1):
    async with AsyncSessionLocal() as db:
        r = await db.execute(select(CartItem).where(CartItem.user_id == user_id, CartItem.product_id == product_id))
        item = r.scalar_one_or_none()
        if item:
            item.quantity += quantity
        else:
            item = CartItem(user_id=user_id, product_id=product_id, quantity=quantity)
            db.add(item)
        await db.commit()

async def update_cart_item(user_id, product_id, quantity):
    async with AsyncSessionLocal() as db:
        if quantity <= 0:
            await db.execute(delete(CartItem).where(CartItem.user_id == user_id, CartItem.product_id == product_id))
        else:
            await db.execute(update(CartItem).where(CartItem.user_id == user_id, CartItem.product_id == product_id).values(quantity=quantity))
        await db.commit()

async def clear_cart(user_id):
    async with AsyncSessionLocal() as db:
        await db.execute(delete(CartItem).where(CartItem.user_id == user_id))
        await db.commit()

# ORDERS
async def create_order(user_id, cart_items, address, latitude, longitude,
                       comment=None, coupon_code=None, discount_amount=0,
                       delivery_price=0, distance_km=0):
    async with AsyncSessionLocal() as db:
        total = sum(i.product.price * i.quantity for i in cart_items)
        order = Order(
            user_id=user_id, total_price=total, delivery_price=delivery_price,
            address=address, latitude=latitude, longitude=longitude,
            distance_km=distance_km, comment=comment,
            coupon_code=coupon_code, discount_amount=discount_amount
        )
        db.add(order); await db.flush()
        for item in cart_items:
            db.add(OrderItem(order_id=order.id, product_id=item.product_id,
                             quantity=item.quantity, price=item.product.price))
        await db.commit(); await db.refresh(order)
        return order

async def get_user_orders(user_id):
    async with AsyncSessionLocal() as db:
        q = select(Order).options(selectinload(Order.items).selectinload(OrderItem.product)).where(Order.user_id == user_id).order_by(Order.created_at.desc())
        return (await db.execute(q)).scalars().all()

async def get_all_orders(date_from=None, date_to=None, status=None):
    async with AsyncSessionLocal() as db:
        q = select(Order).options(
            selectinload(Order.user),
            selectinload(Order.items).selectinload(OrderItem.product)
        ).order_by(Order.created_at.desc())
        if date_from:
            q = q.where(Order.created_at >= date_from)
        if date_to:
            q = q.where(Order.created_at <= date_to)
        if status:
            q = q.where(Order.status == status)
        return (await db.execute(q)).scalars().all()

async def get_order(order_id):
    async with AsyncSessionLocal() as db:
        q = select(Order).options(
            selectinload(Order.user),
            selectinload(Order.items).selectinload(OrderItem.product)
        ).where(Order.id == order_id)
        return (await db.execute(q)).scalar_one_or_none()

async def update_order_status(order_id, status):
    async with AsyncSessionLocal() as db:
        await db.execute(update(Order).where(Order.id == order_id).values(status=status, updated_at=datetime.utcnow()))
        await db.commit()

async def update_order_group_message(order_id, message_id):
    async with AsyncSessionLocal() as db:
        await db.execute(update(Order).where(Order.id == order_id).values(group_message_id=message_id))
        await db.commit()

# COUPONS
async def get_coupon(code):
    async with AsyncSessionLocal() as db:
        r = await db.execute(select(Coupon).where(Coupon.code == code.upper(), Coupon.is_active == True))
        c = r.scalar_one_or_none()
        if not c: return None
        if c.expires_at and c.expires_at < datetime.utcnow(): return None
        if c.max_uses and c.used_count >= c.max_uses: return None
        return c

async def use_coupon(code):
    async with AsyncSessionLocal() as db:
        await db.execute(update(Coupon).where(Coupon.code == code.upper()).values(used_count=Coupon.used_count + 1))
        await db.commit()

async def get_all_coupons():
    async with AsyncSessionLocal() as db:
        return (await db.execute(select(Coupon).order_by(Coupon.created_at.desc()))).scalars().all()

async def create_coupon(code, discount_type, discount_value, min_order_amount=0, max_uses=None, expires_at=None):
    async with AsyncSessionLocal() as db:
        c = Coupon(code=code.upper(), discount_type=discount_type, discount_value=discount_value,
                   min_order_amount=min_order_amount, max_uses=max_uses, expires_at=expires_at)
        db.add(c); await db.commit(); await db.refresh(c)
        return c

async def update_coupon(coupon_id, **kwargs):
    async with AsyncSessionLocal() as db:
        await db.execute(update(Coupon).where(Coupon.id == coupon_id).values(**kwargs))
        await db.commit()

async def delete_coupon(coupon_id):
    async with AsyncSessionLocal() as db:
        await db.execute(delete(Coupon).where(Coupon.id == coupon_id))
        await db.commit()

# REVIEWS
async def get_product_reviews(product_id):
    async with AsyncSessionLocal() as db:
        q = select(Review).options(selectinload(Review.user)).where(Review.product_id == product_id).order_by(Review.created_at.desc())
        return (await db.execute(q)).scalars().all()

async def get_product_rating(product_id):
    async with AsyncSessionLocal() as db:
        r = await db.execute(select(func.avg(Review.rating), func.count(Review.id)).where(Review.product_id == product_id))
        avg, count = r.one()
        return round(avg or 0, 1), count or 0

async def add_review(user_id, product_id, rating, comment=None):
    async with AsyncSessionLocal() as db:
        await db.execute(delete(Review).where(Review.user_id == user_id, Review.product_id == product_id))
        db.add(Review(user_id=user_id, product_id=product_id, rating=rating, comment=comment))
        await db.commit()

async def delete_review(review_id):
    async with AsyncSessionLocal() as db:
        await db.execute(delete(Review).where(Review.id == review_id))
        await db.commit()

async def get_all_reviews():
    async with AsyncSessionLocal() as db:
        q = select(Review).options(selectinload(Review.user), selectinload(Review.product)).order_by(Review.created_at.desc())
        return (await db.execute(q)).scalars().all()

# WISHLIST
async def get_wishlist(user_id):
    async with AsyncSessionLocal() as db:
        q = select(Wishlist).options(selectinload(Wishlist.product)).where(Wishlist.user_id == user_id)
        return (await db.execute(q)).scalars().all()

async def toggle_wishlist(user_id, product_id):
    async with AsyncSessionLocal() as db:
        r = await db.execute(select(Wishlist).where(Wishlist.user_id == user_id, Wishlist.product_id == product_id))
        item = r.scalar_one_or_none()
        if item:
            await db.execute(delete(Wishlist).where(Wishlist.user_id == user_id, Wishlist.product_id == product_id))
            await db.commit(); return False
        else:
            db.add(Wishlist(user_id=user_id, product_id=product_id))
            await db.commit(); return True

async def is_in_wishlist(user_id, product_id):
    async with AsyncSessionLocal() as db:
        r = await db.execute(select(Wishlist).where(Wishlist.user_id == user_id, Wishlist.product_id == product_id))
        return r.scalar_one_or_none() is not None

# ADMIN SESSION
async def create_admin_session(token, expires_at):
    async with AsyncSessionLocal() as db:
        db.add(AdminSession(token=token, expires_at=expires_at))
        await db.commit()

async def check_admin_session(token):
    async with AsyncSessionLocal() as db:
        r = await db.execute(select(AdminSession).where(AdminSession.token == token, AdminSession.expires_at > datetime.utcnow()))
        return r.scalar_one_or_none() is not None

async def delete_admin_session(token):
    async with AsyncSessionLocal() as db:
        await db.execute(delete(AdminSession).where(AdminSession.token == token))
        await db.commit()

# STATS
async def get_stats():
    async with AsyncSessionLocal() as db:
        users = (await db.execute(select(func.count(User.id)))).scalar()
        products = (await db.execute(select(func.count(Product.id)).where(Product.is_active == True))).scalar()
        orders = (await db.execute(select(func.count(Order.id)))).scalar()
        revenue = (await db.execute(select(func.sum(Order.total_price)).where(Order.status == 'delivered'))).scalar() or 0
        today = date.today()
        today_orders = (await db.execute(select(func.count(Order.id)).where(func.date(Order.created_at) == today))).scalar()
        today_revenue = (await db.execute(select(func.sum(Order.total_price)).where(
            func.date(Order.created_at) == today, Order.status != 'cancelled'
        ))).scalar() or 0
        from sqlalchemy import text
        daily = (await db.execute(text(
            "SELECT date(created_at) as d, COUNT(*) as cnt, SUM(total_price) as total "
            "FROM orders WHERE created_at >= date('now','-7 days') "
            "GROUP BY date(created_at) ORDER BY d"
        ))).all()
        return {
            "users": users, "products": products, "orders": orders, "revenue": revenue,
            "today_orders": today_orders, "today_revenue": today_revenue,
            "daily": [{"date": str(r[0]), "orders": r[1], "revenue": r[2] or 0} for r in daily]
        }
