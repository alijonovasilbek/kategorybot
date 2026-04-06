"""
seed.py — Demo ma'lumotlar qo'shish skripti
Ishlatish: python seed.py
"""
import asyncio
from database.db import init_db
from database.crud import create_category, create_product, get_categories

CATEGORIES = [
    {"name_uz": "Erkaklar", "name_ru": "Мужское", "image_url": None},
    {"name_uz": "Ayollar",  "name_ru": "Женское",  "image_url": None},
    {"name_uz": "Bolalar",  "name_ru": "Детское",   "image_url": None},
    {"name_uz": "Sport",    "name_ru": "Спорт",      "image_url": None},
]

PRODUCTS = [
    {
        "title_uz": "Erkaklar ko'ylagi",
        "title_ru": "Мужская рубашка",
        "description_uz": "Yuqori sifatli paxta ko'ylak. Barcha o'lchamlarda mavjud.",
        "description_ru": "Хлопковая рубашка высокого качества. Все размеры в наличии.",
        "price": 150000, "old_price": 200000,
        "images": [], "stock": 50, "cat_index": 0,
    },
    {
        "title_uz": "Klassik shim",
        "title_ru": "Классические брюки",
        "description_uz": "Biznes uslubida klassik shim.",
        "description_ru": "Классические брюки делового стиля.",
        "price": 280000, "old_price": None,
        "images": [], "stock": 30, "cat_index": 0,
    },
    {
        "title_uz": "Ayollar ko'ylagi",
        "title_ru": "Женское платье",
        "description_uz": "Yoz uchun yengil ko'ylak.",
        "description_ru": "Лёгкое летнее платье.",
        "price": 320000, "old_price": 400000,
        "images": [], "stock": 25, "cat_index": 1,
    },
    {
        "title_uz": "Bolalar kombinezon",
        "title_ru": "Детский комбинезон",
        "description_uz": "0-3 yoshli bolalar uchun issiq kombinezon.",
        "description_ru": "Тёплый комбинезон для детей 0-3 лет.",
        "price": 180000, "old_price": None,
        "images": [], "stock": 40, "cat_index": 2,
    },
    {
        "title_uz": "Sport krossovka",
        "title_ru": "Спортивные кроссовки",
        "description_uz": "Yugurishga mo'ljallangan engil krossovka.",
        "description_ru": "Лёгкие кроссовки для бега.",
        "price": 450000, "old_price": 550000,
        "images": [], "stock": 20, "cat_index": 3,
    },
    {
        "title_uz": "Sport futbolka",
        "title_ru": "Спортивная футболка",
        "description_uz": "Breathable material, sport uchun ideal.",
        "description_ru": "Дышащий материал, идеально для спорта.",
        "price": 95000, "old_price": None,
        "images": [], "stock": 60, "cat_index": 3,
    },
]

async def seed():
    await init_db()
    print("🌱 Demo ma'lumotlar qo'shilmoqda...")

    # Kategoriyalar
    cats = []
    for c in CATEGORIES:
        cat = await create_category(c["name_uz"], c["name_ru"], c["image_url"])
        cats.append(cat)
        print(f"  ✅ Kategoriya: {cat.name_uz}")

    # Mahsulotlar
    for p in PRODUCTS:
        data = {
            "title_uz": p["title_uz"],
            "title_ru": p["title_ru"],
            "description_uz": p["description_uz"],
            "description_ru": p["description_ru"],
            "price": p["price"],
            "old_price": p["old_price"],
            "images": p["images"],
            "stock": p["stock"],
            "category_id": cats[p["cat_index"]].id,
        }
        product = await create_product(data)
        print(f"  ✅ Mahsulot: {product.title_uz}")

    print("\n🎉 Tayyor! Demo ma'lumotlar qo'shildi.")
    print("   Bot va API ni ishga tushiring: ./start.sh")

if __name__ == "__main__":
    asyncio.run(seed())
