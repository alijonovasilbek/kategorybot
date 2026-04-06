from fastapi import FastAPI, HTTPException, Depends, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List
import json, os, shutil, uuid
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from database.crud import *
from database.db import init_db

app = FastAPI(title="KategoryBot API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")
app.mount("/static", StaticFiles(directory="webapp/dist"), name="static")

@app.on_event("startup")
async def startup():
    await init_db()

# ── UPLOAD ────────────────────────────────────────────────────────────────────
@app.post("/api/upload")
async def upload_image(file: UploadFile = File(...)):
    ext = file.filename.split(".")[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    path = os.path.join(UPLOAD_DIR, filename)
    with open(path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    return {"url": f"/uploads/{filename}"}

# ── USERS ─────────────────────────────────────────────────────────────────────
@app.get("/api/users/{telegram_id}")
async def get_user_api(telegram_id: int):
    user = await get_user(telegram_id)
    if not user:
        raise HTTPException(404, "User not found")
    return {
        "id": user.id,
        "telegram_id": user.telegram_id,
        "full_name": user.full_name,
        "username": user.username,
        "phone": user.phone,
        "language": user.language,
        "is_verified": user.is_verified,
    }

@app.put("/api/users/{telegram_id}/language")
async def set_language(telegram_id: int, lang: str):
    await update_user_language(telegram_id, lang)
    return {"ok": True}

# ── CATEGORIES ────────────────────────────────────────────────────────────────
@app.get("/api/categories")
async def list_categories(parent_id: Optional[int] = None):
    cats = await get_categories(parent_id)
    return [{"id": c.id, "name_uz": c.name_uz, "name_ru": c.name_ru, "image_url": c.image_url, "parent_id": c.parent_id} for c in cats]

@app.get("/api/categories/all")
async def list_all_categories():
    cats = await get_all_categories()
    return [{"id": c.id, "name_uz": c.name_uz, "name_ru": c.name_ru, "image_url": c.image_url, "parent_id": c.parent_id, "is_active": c.is_active} for c in cats]

@app.post("/api/categories")
async def create_category_api(name_uz: str = Form(...), name_ru: str = Form(...), parent_id: Optional[int] = Form(None), image: Optional[UploadFile] = File(None)):
    image_url = None
    if image:
        ext = image.filename.split(".")[-1]
        filename = f"{uuid.uuid4()}.{ext}"
        path = os.path.join(UPLOAD_DIR, filename)
        with open(path, "wb") as f:
            shutil.copyfileobj(image.file, f)
        image_url = f"/uploads/{filename}"
    cat = await create_category(name_uz, name_ru, image_url, parent_id)
    return {"id": cat.id, "name_uz": cat.name_uz, "name_ru": cat.name_ru}

@app.put("/api/categories/{cat_id}")
async def update_category_api(cat_id: int, name_uz: str = Form(...), name_ru: str = Form(...), image: Optional[UploadFile] = File(None)):
    data = {"name_uz": name_uz, "name_ru": name_ru}
    if image:
        ext = image.filename.split(".")[-1]
        filename = f"{uuid.uuid4()}.{ext}"
        path = os.path.join(UPLOAD_DIR, filename)
        with open(path, "wb") as f:
            shutil.copyfileobj(image.file, f)
        data["image_url"] = f"/uploads/{filename}"
    await update_category(cat_id, **data)
    return {"ok": True}

@app.delete("/api/categories/{cat_id}")
async def delete_category_api(cat_id: int):
    await delete_category(cat_id)
    return {"ok": True}

# ── PRODUCTS ──────────────────────────────────────────────────────────────────
@app.get("/api/products")
async def list_products(category_id: Optional[int] = None, search: Optional[str] = None, limit: int = 50, offset: int = 0):
    products = await get_products(category_id, search, limit, offset)
    return [_product_dict(p) for p in products]

@app.get("/api/products/all")
async def list_all_products_api():
    products = await get_all_products()
    return [_product_dict(p) for p in products]

@app.get("/api/products/{product_id}")
async def get_product_api(product_id: int):
    p = await get_product(product_id)
    if not p:
        raise HTTPException(404, "Product not found")
    return _product_dict(p)

@app.get("/api/products/{product_id}/similar")
async def similar_products(product_id: int, category_id: int):
    products = await get_similar_products(product_id, category_id)
    return [_product_dict(p) for p in products]

@app.post("/api/products")
async def create_product_api(
    title_uz: str = Form(...), title_ru: str = Form(...),
    description_uz: str = Form(""), description_ru: str = Form(""),
    price: float = Form(...), old_price: Optional[float] = Form(None),
    category_id: int = Form(...), stock: int = Form(100),
    images: List[UploadFile] = File(default=[])
):
    image_urls = []
    for img in images[:4]:
        ext = img.filename.split(".")[-1]
        filename = f"{uuid.uuid4()}.{ext}"
        path = os.path.join(UPLOAD_DIR, filename)
        with open(path, "wb") as f:
            shutil.copyfileobj(img.file, f)
        image_urls.append(f"/uploads/{filename}")
    data = dict(title_uz=title_uz, title_ru=title_ru, description_uz=description_uz,
                description_ru=description_ru, price=price, old_price=old_price,
                category_id=category_id, stock=stock, images=image_urls)
    product = await create_product(data)
    return {"id": product.id}

@app.put("/api/products/{product_id}")
async def update_product_api(
    product_id: int,
    title_uz: str = Form(...), title_ru: str = Form(...),
    description_uz: str = Form(""), description_ru: str = Form(""),
    price: float = Form(...), old_price: Optional[float] = Form(None),
    category_id: int = Form(...), stock: int = Form(100),
    images: List[UploadFile] = File(default=[]),
    existing_images: str = Form("[]")
):
    image_urls = json.loads(existing_images)
    for img in images[:max(0, 4 - len(image_urls))]:
        ext = img.filename.split(".")[-1]
        filename = f"{uuid.uuid4()}.{ext}"
        path = os.path.join(UPLOAD_DIR, filename)
        with open(path, "wb") as f:
            shutil.copyfileobj(img.file, f)
        image_urls.append(f"/uploads/{filename}")
    await update_product(product_id, title_uz=title_uz, title_ru=title_ru,
        description_uz=description_uz, description_ru=description_ru,
        price=price, old_price=old_price, category_id=category_id,
        stock=stock, images=image_urls[:4])
    return {"ok": True}

@app.delete("/api/products/{product_id}")
async def delete_product_api(product_id: int):
    await delete_product(product_id)
    return {"ok": True}

def _product_dict(p):
    return {
        "id": p.id, "title_uz": p.title_uz, "title_ru": p.title_ru,
        "description_uz": p.description_uz, "description_ru": p.description_ru,
        "price": p.price, "old_price": p.old_price, "images": p.images or [],
        "category_id": p.category_id, "stock": p.stock, "is_active": p.is_active,
    }

# ── CART ──────────────────────────────────────────────────────────────────────
class CartRequest(BaseModel):
    user_id: int
    product_id: int
    quantity: int = 1

@app.get("/api/cart/{user_id}")
async def get_cart_api(user_id: int):
    items = await get_cart(user_id)
    return [{"id": i.id, "product_id": i.product_id, "quantity": i.quantity,
             "product": _product_dict(i.product)} for i in items]

@app.post("/api/cart")
async def add_cart(req: CartRequest):
    await add_to_cart(req.user_id, req.product_id, req.quantity)
    return {"ok": True}

@app.put("/api/cart")
async def update_cart(req: CartRequest):
    await update_cart_item(req.user_id, req.product_id, req.quantity)
    return {"ok": True}

@app.delete("/api/cart/{user_id}")
async def clear_cart_api(user_id: int):
    await clear_cart(user_id)
    return {"ok": True}

# ── ORDERS ────────────────────────────────────────────────────────────────────
class OrderRequest(BaseModel):
    user_id: int
    address: str
    latitude: float
    longitude: float
    comment: Optional[str] = None

@app.post("/api/orders")
async def place_order(req: OrderRequest):
    cart_items = await get_cart(req.user_id)
    if not cart_items:
        raise HTTPException(400, "Cart is empty")
    order = await create_order(req.user_id, cart_items, req.address, req.latitude, req.longitude, req.comment)
    await clear_cart(req.user_id)
    return {"id": order.id, "total": order.total_price, "status": order.status}

@app.get("/api/orders/{user_id}")
async def user_orders(user_id: int):
    orders = await get_user_orders(user_id)
    return [_order_dict(o) for o in orders]

@app.get("/api/admin/orders")
async def admin_orders():
    orders = await get_all_orders()
    return [_order_dict(o) for o in orders]

@app.put("/api/admin/orders/{order_id}/status")
async def change_order_status(order_id: int, status: str):
    await update_order_status(order_id, status)
    return {"ok": True}

@app.get("/api/admin/users")
async def admin_users():
    users = await get_all_users()
    return [{"id": u.id, "telegram_id": u.telegram_id, "full_name": u.full_name,
             "phone": u.phone, "language": u.language, "is_verified": u.is_verified} for u in users]

def _order_dict(o):
    return {
        "id": o.id, "status": o.status, "total_price": o.total_price,
        "address": o.address, "latitude": o.latitude, "longitude": o.longitude,
        "comment": o.comment, "created_at": str(o.created_at),
        "user": {"id": o.user.id, "full_name": o.user.full_name, "phone": o.user.phone} if o.user else None,
        "items": [{"product_id": i.product_id, "quantity": i.quantity, "price": i.price,
                   "product_title": i.product.title_uz if i.product else ""} for i in o.items]
    }
