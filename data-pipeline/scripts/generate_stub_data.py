#!/usr/bin/env python3
"""Generate stub data files for Shopee and TikTok with 200 items each.

Run once:  python _generate_stub_data.py

Matching strategy:
- Items 1-50: EXACT matches across platforms (same brand + same spec)
- Items 51-80: VARIANT matches (same brand, different spec)
- Items 81-120: SIMILAR but different products
- Items 121-200: UNIQUE to each platform
"""

import json
import os
import random

random.seed(42)

# ─── Brand + product templates ──────────────────────────────────────────────

BRANDS = [
    {"en": "Dove", "th": "โดฟ"},
    {"en": "Nivea", "th": "นีเวีย"},
    {"en": "Garnier", "th": "การ์นิเอร์"},
    {"en": "Pantene", "th": "แพนทีน"},
    {"en": "Sunsilk", "th": "ซันซิล"},
    {"en": "Head & Shoulders", "th": "เฮดแอนด์โชว์เดอร์"},
    {"en": "Lux", "th": "ลักซ์"},
    {"en": "Lifebuoy", "th": "ไลฟ์บอย"},
    {"en": "Pond's", "th": "พอนด์ส"},
    {"en": "Olay", "th": "โอเลย์"},
    {"en": "Cetaphil", "th": "เซตาฟิล"},
    {"en": "Bioderma", "th": "ไบโอเดอร์มา"},
    {"en": "Vaseline", "th": "วาสลีน"},
    {"en": "Johnson's", "th": "จอห์นสัน"},
    {"en": "Palmolive", "th": "ปาล์มโอลีฟ"},
    {"en": "Clear", "th": "เคลียร์"},
    {"en": "TRESemmé", "th": "เทรซาเม่"},
    {"en": "L'Oréal", "th": "ลอรีอัล"},
    {"en": "Bioré", "th": "บิโอเร"},
    {"en": "Senka", "th": "เซนกะ"},
]

PRODUCT_TYPES = [
    {"en": "Body Wash", "th": "บอดี้วอช"},
    {"en": "Shampoo", "th": "แชมพู"},
    {"en": "Conditioner", "th": "ครีมนวดผม"},
    {"en": "Face Wash", "th": "เจลล้างหน้า"},
    {"en": "Facial Foam", "th": "โฟมล้างหน้า"},
    {"en": "Body Lotion", "th": "โลชั่นบำรุงผิว"},
    {"en": "Sunscreen", "th": "กันแดด"},
    {"en": "Micellar Water", "th": "ไมเซลลาร์ วอเตอร์"},
    {"en": "Hand Cream", "th": "ครีมทามือ"},
    {"en": "Lip Balm", "th": "ลิปบาล์ม"},
    {"en": "Deodorant", "th": "โรลออน"},
    {"en": "Hair Serum", "th": "เซรั่มบำรุงผม"},
    {"en": "Shower Cream", "th": "ครีมอาบน้ำ"},
    {"en": "Moisturizer", "th": "มอยเจอร์ไรเซอร์"},
    {"en": "Toner", "th": "โทนเนอร์"},
]

VARIANTS_EN = [
    "Deeply Nourishing", "Ultra Repair", "Intensive Care", "Total Effects",
    "Anti-Dandruff", "Cool Menthol", "Smooth & Manageable", "Damage Care",
    "Color Protect", "Volume Boost", "Oil Control", "Whitening",
    "Gentle Clean", "Deep Cleansing", "Hydrating", "Anti-Aging",
    "Fresh Active", "Natural Glow", "Sensitive Skin", "Extra Moisture",
    "Pro-V", "Men Deep Clean", "Botanicals", "Perfect White",
]

VARIANTS_TH = [
    "สูตรบำรุงล้ำลึก", "สูตรซ่อมแซมผม", "สูตรเข้มข้น", "สูตรครบวงจร",
    "ขจัดรังแค", "สูตรเย็นสดชื่น", "สลวยจัดทรงง่าย", "ฟื้นฟูผมเสีย",
    "ปกป้องสีผม", "เพิ่มวอลลุ่ม", "คุมมัน", "ผิวขาวกระจ่างใส",
    "ทำความสะอาดอ่อนโยน", "ล้างลึก", "เติมความชุ่มชื้น", "ต่อต้านริ้วรอย",
    "สดชื่นทั้งวัน", "เปล่งประกายเป็นธรรมชาติ", "สำหรับผิวแพ้ง่าย", "เพิ่มความชุ่มชื้นพิเศษ",
    "โปร-วี", "สูตรผู้ชาย", "สูตรธรรมชาติ", "ผิวขาวใส",
]

SIZES_ML = [100, 150, 180, 200, 250, 300, 400, 450, 480, 500, 600, 900, 1000]
SIZES_G = [50, 80, 100, 120, 150, 180, 200, 250, 400, 500]

def price_for_size(size_val, unit):
    """Generate a plausible price in satang (THB*100) for a given size."""
    if unit == "ml":
        base = int(size_val * 0.35 * 100)  # ~35 satang/ml
    else:
        base = int(size_val * 0.8 * 100)   # ~80 satang/g
    return max(2900, base + random.randint(-2000, 5000))


def make_shopee_item(rank, item_id_num, brand, product_type, variant_en, size_val, size_unit):
    price = price_for_size(size_val, size_unit)
    has_promo = random.random() < 0.6
    promo = int(price * random.uniform(0.7, 0.9)) if has_promo else None
    unit_str = "ml" if size_unit == "ml" else "g"
    title = f"{brand['en']} {variant_en} {product_type['en']} {size_val}{unit_str}"
    return {
        "item_id": f"sh_{item_id_num}",
        "title": title,
        "category": "personal_care",
        "rank": rank,
        "url": f"https://shopee.co.th/product/{item_id_num}",
        "image_url": f"https://cf.shopee.co.th/file/img_{item_id_num}",
        "price": price,
        "promo_price": promo,
        "currency": "THB",
        "brand_raw": brand["en"],
        "review_count": random.randint(500, 50000),
        "sold_range": random.choice(["100+", "500+", "1K+", "5K+", "10K+", "50K+", "100K+"]),
        "rating": round(random.uniform(3.8, 5.0), 1),
    }


def make_tiktok_item(rank, item_id_num, brand, product_type, variant_th, size_val, size_unit):
    price = price_for_size(size_val, size_unit)
    # TikTok prices slightly different
    price = price + random.randint(-1500, 1500)
    price = max(2500, price)
    has_promo = random.random() < 0.4
    promo = int(price * random.uniform(0.75, 0.92)) if has_promo else None
    if size_unit == "ml":
        unit_str = random.choice(["ml", "มล.", "มล"])
    else:
        unit_str = random.choice(["g", "กรัม", "กก" if size_val >= 1000 else "กรัม"])
    # Mix Thai and English in title
    if random.random() < 0.5:
        title = f"{brand['th']} {variant_th} {product_type['th']} {size_val}{unit_str}"
    else:
        title = f"{brand['en']} {variant_th} {product_type['th']} {size_val}{unit_str}"
    return {
        "item_id": f"tt_{item_id_num}",
        "title": title,
        "category": "personal_care",
        "rank": rank,
        "url": f"https://www.tiktok.com/shop/product/{item_id_num}",
        "image_url": f"https://p16-oec-va.ibyteimg.com/tos-maliva/{item_id_num}",
        "price": price,
        "promo_price": promo,
        "currency": "THB",
        "brand_raw": brand["th"] if random.random() < 0.5 else brand["en"],
        "review_count": random.randint(200, 30000),
        "likes": random.randint(100, 100000),
        "sold_range": random.choice(["50+", "100+", "500+", "1K-5K", "5K-10K", "10K-50K", "50K+"]),
        "rating": round(random.uniform(3.5, 5.0), 1),
    }


def generate():
    shopee_items = []
    tiktok_items = []

    sh_id = 100001
    tt_id = 200001

    # ─── GROUP 1: EXACT MATCHES (items 1-50) ────────────────────────────────
    # Same brand + same spec, different titles (EN vs TH)
    for i in range(50):
        brand = BRANDS[i % len(BRANDS)]
        pt = PRODUCT_TYPES[i % len(PRODUCT_TYPES)]
        variant_idx = i % len(VARIANTS_EN)
        size = SIZES_ML[i % len(SIZES_ML)] if i % 3 != 2 else SIZES_G[i % len(SIZES_G)]
        unit = "ml" if i % 3 != 2 else "g"

        sh_rank = i + 1
        tt_rank = i + 1 + random.randint(0, 5)

        shopee_items.append(make_shopee_item(sh_rank, sh_id, brand, pt, VARIANTS_EN[variant_idx], size, unit))
        tiktok_items.append(make_tiktok_item(tt_rank, tt_id, brand, pt, VARIANTS_TH[variant_idx], size, unit))

        sh_id += 1
        tt_id += 1

    # ─── GROUP 2: VARIANT MATCHES (items 51-80) ────────────────────────────
    # Same brand, different spec (size)
    for i in range(30):
        brand = BRANDS[i % len(BRANDS)]
        pt = PRODUCT_TYPES[(i + 5) % len(PRODUCT_TYPES)]
        variant_idx = (i + 7) % len(VARIANTS_EN)

        # Shopee has one size, TikTok has a different size of the same product
        sh_size = random.choice([200, 250, 400])
        tt_size = random.choice([100, 150, 500, 600])

        sh_rank = 51 + i
        tt_rank = 51 + i + random.randint(-3, 3)
        tt_rank = max(1, tt_rank)

        shopee_items.append(make_shopee_item(sh_rank, sh_id, brand, pt, VARIANTS_EN[variant_idx], sh_size, "ml"))
        tiktok_items.append(make_tiktok_item(tt_rank, tt_id, brand, pt, VARIANTS_TH[variant_idx], tt_size, "ml"))

        sh_id += 1
        tt_id += 1

    # ─── GROUP 3: SIMILAR BUT DIFFERENT (items 81-120) ──────────────────────
    # Same brand but different product type entirely
    for i in range(40):
        brand = BRANDS[i % len(BRANDS)]
        sh_pt = PRODUCT_TYPES[i % len(PRODUCT_TYPES)]
        tt_pt = PRODUCT_TYPES[(i + 3) % len(PRODUCT_TYPES)]
        variant_idx = (i + 2) % len(VARIANTS_EN)
        size = SIZES_ML[(i + 4) % len(SIZES_ML)]

        sh_rank = 81 + i
        tt_rank = 81 + i + random.randint(-5, 5)
        tt_rank = max(1, tt_rank)

        shopee_items.append(make_shopee_item(sh_rank, sh_id, brand, sh_pt, VARIANTS_EN[variant_idx], size, "ml"))
        tiktok_items.append(make_tiktok_item(tt_rank, tt_id, brand, tt_pt, VARIANTS_TH[variant_idx], size, "ml"))

        sh_id += 1
        tt_id += 1

    # ─── GROUP 4: UNIQUE TO EACH PLATFORM (items 121-200) ──────────────────
    # These items exist only on one platform

    # Shopee-only items (with some niche / imported brands mixed in)
    extra_shopee_brands = [
        {"en": "Eucerin", "th": "ยูเซอริน"},
        {"en": "Neutrogena", "th": "นูโทรจีนา"},
        {"en": "CeraVe", "th": "เซราวี"},
        {"en": "Aveeno", "th": "อาวีโน่"},
        {"en": "Himalaya", "th": "หิมาลายา"},
        {"en": "Dettol", "th": "เดทตอล"},
        {"en": "Innisfree", "th": "อินนิสฟรี"},
        {"en": "Clean & Clear", "th": "คลีนแอนด์เคลียร์"},
    ]

    for i in range(80):
        if i < 30:
            brand = extra_shopee_brands[i % len(extra_shopee_brands)]
        else:
            brand = BRANDS[i % len(BRANDS)]
        pt = PRODUCT_TYPES[(i + 6) % len(PRODUCT_TYPES)]
        variant_idx = (i + 10) % len(VARIANTS_EN)
        size = SIZES_ML[(i + 2) % len(SIZES_ML)] if i % 4 != 0 else SIZES_G[(i + 1) % len(SIZES_G)]
        unit = "ml" if i % 4 != 0 else "g"

        sh_rank = 121 + i
        shopee_items.append(make_shopee_item(sh_rank, sh_id, brand, pt, VARIANTS_EN[variant_idx], size, unit))
        sh_id += 1

    # TikTok-only items (with some TikTok-trending brands)
    extra_tiktok_brands = [
        {"en": "Skintific", "th": "สกินทิฟิค"},
        {"en": "Somethinc", "th": "ซัมธิง"},
        {"en": "Beauty of Joseon", "th": "บิวตี้ออฟโจซอน"},
        {"en": "COSRX", "th": "คอสอาร์เอ็กซ์"},
        {"en": "Anua", "th": "อนัว"},
        {"en": "Torriden", "th": "ทอร์ริเดน"},
        {"en": "mixsoon", "th": "มิกซูน"},
        {"en": "Hada Labo", "th": "ฮาดะ ลาโบะ"},
    ]

    for i in range(80):
        if i < 30:
            brand = extra_tiktok_brands[i % len(extra_tiktok_brands)]
        else:
            brand = BRANDS[(i + 3) % len(BRANDS)]
        pt = PRODUCT_TYPES[(i + 8) % len(PRODUCT_TYPES)]
        variant_idx = (i + 5) % len(VARIANTS_TH)
        size = SIZES_ML[(i + 7) % len(SIZES_ML)] if i % 3 != 0 else SIZES_G[(i + 3) % len(SIZES_G)]
        unit = "ml" if i % 3 != 0 else "g"

        tt_rank = 121 + i
        tiktok_items.append(make_tiktok_item(tt_rank, tt_id, brand, pt, VARIANTS_TH[variant_idx], size, unit))
        tt_id += 1

    # ─── Fix ranks to be 1..200 and unique ──────────────────────────────────
    for idx, item in enumerate(shopee_items):
        item["rank"] = idx + 1
    for idx, item in enumerate(tiktok_items):
        item["rank"] = idx + 1

    assert len(shopee_items) == 200, f"Shopee items: {len(shopee_items)}"
    assert len(tiktok_items) == 200, f"TikTok items: {len(tiktok_items)}"

    return shopee_items, tiktok_items


if __name__ == "__main__":
    shopee, tiktok = generate()

    base = os.path.dirname(os.path.abspath(__file__))
    sh_dir = os.path.join(base, "data", "raw_stub", "shopee", "personal_care")
    tt_dir = os.path.join(base, "data", "raw_stub", "tiktok", "personal_care")

    os.makedirs(sh_dir, exist_ok=True)
    os.makedirs(tt_dir, exist_ok=True)

    sh_path = os.path.join(sh_dir, "2025-02-01.json")
    tt_path = os.path.join(tt_dir, "2025-02-01.json")

    with open(sh_path, "w", encoding="utf-8") as f:
        json.dump(shopee, f, indent=2, ensure_ascii=False)
    print(f"Wrote {len(shopee)} items to {sh_path}")

    with open(tt_path, "w", encoding="utf-8") as f:
        json.dump(tiktok, f, indent=2, ensure_ascii=False)
    print(f"Wrote {len(tiktok)} items to {tt_path}")
