
from pathlib import Path
from PIL import Image, ImageDraw
import app
import re
import hashlib

OUT = Path("static/images/products")
OUT.mkdir(parents=True, exist_ok=True)

COLORS = [
    (77, 105, 65), (130, 87, 52), (166, 119, 48),
    (105, 75, 112), (66, 111, 116), (145, 91, 65),
    (103, 119, 68), (174, 133, 76)
]

def safe_name(text):
    text = re.sub(r"[^\w\-]+", "_", text, flags=re.UNICODE)
    return text.strip("_") or "product"

def make_image(name, category):
    digest = hashlib.md5((category + name).encode("utf-8")).hexdigest()
    color = COLORS[int(digest[:2], 16) % len(COLORS)]

    img = Image.new("RGB", (600, 450), (245, 242, 232))
    d = ImageDraw.Draw(img)

    # بطاقة المنتج
    d.rounded_rectangle(
        (65, 45, 535, 405),
        radius=30,
        fill=(255, 255, 250),
        outline=color,
        width=5
    )

    # وعاء المنتج
    d.ellipse((170, 125, 430, 330), fill=color)
    d.ellipse((190, 135, 410, 305), fill=(220, 194, 145))
    d.ellipse((205, 150, 395, 290), fill=color)

    # حبيبات زخرفية تختلف حسب اسم المنتج
    seed = int(digest[2:10], 16)
    import random
    rng = random.Random(seed)

    for _ in range(100):
        x = rng.randint(220, 380)
        y = rng.randint(165, 270)
        r = rng.randint(2, 7)
        shade = rng.choice([
            (225, 190, 110), (75, 53, 35),
            (235, 220, 170), (150, 110, 55)
        ])
        d.ellipse((x-r, y-r, x+r, y+r), fill=shade)

    # اسم المنتج
    d.rounded_rectangle((95, 340, 505, 390), radius=12, fill=color)

    try:
        from PIL import ImageFont
        font = ImageFont.truetype("arial.ttf", 22)
    except:
        font = ImageFont.load_default()

    d.text((300, 365), name, fill="white", font=font, anchor="mm")

    filename = safe_name(name) + ".jpg"
    img.save(OUT / filename, quality=90)
    return "products/" + filename


count = 0

for product in app.PRODUCTS:
    product["image"] = make_image(
        product["name"],
        product["category"]
    )
    count += 1

print("تم تجهيز الصور:", count)
print("المجلد:", OUT)
