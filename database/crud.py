from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload
from .db import User, Category, Product, CartItem, Order, OrderItem, AsyncSessionLocal

# ── USER ──────────────────────────────────────────────────────────────────────
async def get_or_create_user(telegram_id: int, full_name: str = None, username: str = None) -> User:
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.telegram_id == telegram_id))
        user = result.scalar_one_or_none()
        if not user:
            user = User(telegram_id=telegram_id, full_name=full_name, username=username)
            db.add(user)
            await db.commit()
            await db.refresh(user)
        return user

async def update_user_phone(telegram_id: int, phone: str):
    async with AsyncSessionLocal() as db:
        await db.execute(update(User).where(User.telegram_id == telegram_id).values(phone=phone, is_verified=True))
        await db.commit()

async def update_user_language(telegram_id: int, lang: str):
    async with AsyncSessionLocal() as db:
        await db.execute(update(User).where(User.telegram_id == telegram_id).values(language=lang))
        await db.commit()

async def get_user(telegram_id: int) -> User:
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.telegram_id == telegram_id))
        return result.scalar_one_or_none()

async def get_all_users():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User))
        return result.scalars().all()

# ── CATEGORIES ────────────────────────────────────────────────────────────────
async def get_categories(parent_id=None):
    async with AsyncSessionLocal() as db:
        q = select(Category).where(Category.is_active == True, Category.parent_id == parent_id).order_by(Category.sort_order)
        result = await db.execute(q)
        return result.scalars().all()

async def get_category(cat_id: int):
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Category).where(Category.id == cat_id))
        return result.scalar_one_or_none()

async def create_category(name_uz: str, name_ru: str, image_url: str = None, parent_id: int = None):
    async with AsyncSessionLocal() as db:
        cat = Category(name_uz=name_uz, name_ru=name_ru, image_url=image_url, parent_id=parent_id)
        db.add(cat)
        await db.commit()
        await db.refresh(cat)
        return cat

async def update_category(cat_id: int, **kwargs):
    async with AsyncSessionLocal() as db:
        await db.execute(update(Category).where(Category.id == cat_id).values(**kwargs))
        await db.commit()

async def delete_category(cat_id: int):
    async with AsyncSessionLocal() as db:
        await db.execute(delete(Category).where(Category.id == cat_id))
        await db.commit()

async def get_all_categories():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Category).order_by(Category.sort_order))
        return result.scalars().all()

# ── PRODUCTS ──────────────────────────────────────────────────────────────────
async def get_products(category_id: int = None, search: str = None, limit: int = 50, offset: int = 0):
    async with AsyncSessionLocal() as db:
        q = select(Product).where(Product.is_active == True)
        if category_id:
            q = q.where(Product.category_id == category_id)
        if search:
            q = q.where(
                (Product.title_uz.ilike(f"%{search}%")) |
                (Product.title_ru.ilike(f"%{search}%")) |
                (Product.description_uz.ilike(f"%{search}%"))
            )
        q = q.offset(offset).limit(limit)
        result = await db.execute(q)
        return result.scalars().all()

async def get_product(product_id: int):
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Product).where(Product.id == product_id))
        return result.scalar_one_or_none()

async def get_similar_products(product_id: int, category_id: int, limit: int = 6):
    async with AsyncSessionLocal() as db:
        q = select(Product).where(
            Product.is_active == True,
            Product.id != product_id,
            Product.category_id == category_id
        ).limit(limit)
        result = await db.execute(q)
        return result.scalars().all()

async def create_product(data: dict):
    async with AsyncSessionLocal() as db:
        product = Product(**data)
        db.add(product)
        await db.commit()
        await db.refresh(product)
        return product

async def update_product(product_id: int, **kwargs):
    async with AsyncSessionLocal() as db:
        await db.execute(update(Product).where(Product.id == product_id).values(**kwargs))
        await db.commit()

async def delete_product(product_id: int):
    async with AsyncSessionLocal() as db:
        await db.execute(delete(Product).where(Product.id == product_id))
        await db.commit()

async def get_all_products():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Product).options(selectinload(Product.category)))
        return result.scalars().all()

# ── CART ──────────────────────────────────────────────────────────────────────
async def get_cart(user_id: int):
    async with AsyncSessionLocal() as db:
        q = select(CartItem).options(selectinload(CartItem.product)).where(CartItem.user_id == user_id)
        result = await db.execute(q)
        return result.scalars().all()

async def add_to_cart(user_id: int, product_id: int, quantity: int = 1):
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(CartItem).where(CartItem.user_id == user_id, CartItem.product_id == product_id)
        )
        item = result.scalar_one_or_none()
        if item:
            item.quantity += quantity
        else:
            item = CartItem(user_id=user_id, product_id=product_id, quantity=quantity)
            db.add(item)
        await db.commit()

async def update_cart_item(user_id: int, product_id: int, quantity: int):
    async with AsyncSessionLocal() as db:
        if quantity <= 0:
            await db.execute(delete(CartItem).where(CartItem.user_id == user_id, CartItem.product_id == product_id))
        else:
            await db.execute(
                update(CartItem).where(CartItem.user_id == user_id, CartItem.product_id == product_id).values(quantity=quantity)
            )
        await db.commit()

async def clear_cart(user_id: int):
    async with AsyncSessionLocal() as db:
        await db.execute(delete(CartItem).where(CartItem.user_id == user_id))
        await db.commit()

# ── ORDERS ────────────────────────────────────────────────────────────────────
async def create_order(user_id: int, cart_items, address: str, latitude: float, longitude: float, comment: str = None):
    async with AsyncSessionLocal() as db:
        total = sum(item.product.price * item.quantity for item in cart_items)
        order = Order(user_id=user_id, total_price=total, address=address, latitude=latitude, longitude=longitude, comment=comment)
        db.add(order)
        await db.flush()
        for item in cart_items:
            oi = OrderItem(order_id=order.id, product_id=item.product_id, quantity=item.quantity, price=item.product.price)
            db.add(oi)
        await db.commit()
        await db.refresh(order)
        return order

async def get_user_orders(user_id: int):
    async with AsyncSessionLocal() as db:
        q = select(Order).options(
            selectinload(Order.items).selectinload(OrderItem.product)
        ).where(Order.user_id == user_id).order_by(Order.created_at.desc())
        result = await db.execute(q)
        return result.scalars().all()

async def get_all_orders():
    async with AsyncSessionLocal() as db:
        q = select(Order).options(
            selectinload(Order.user),
            selectinload(Order.items).selectinload(OrderItem.product)
        ).order_by(Order.created_at.desc())
        result = await db.execute(q)
        return result.scalars().all()

async def update_order_status(order_id: int, status: str):
    async with AsyncSessionLocal() as db:
        await db.execute(update(Order).where(Order.id == order_id).values(status=status))
        await db.commit()
