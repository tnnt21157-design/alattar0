import os, re, json
from datetime import datetime, timezone
from urllib.parse import quote
from flask import Flask, render_template, request, redirect, url_for, session, flash, abort, send_file
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from io import BytesIO

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-secret-before-deploy")
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024

database_url = os.environ.get("DATABASE_URL", "sqlite:///store.db")
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql+psycopg2://", 1)
elif database_url.startswith("postgresql://"):
    database_url = database_url.replace("postgresql://", "postgresql+psycopg2://", 1)
app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

CATALOG = {
    "البهارات والتوابل": [
        ("فلفل أسود مطحون",1.50),("فلفل أبيض",1.75),("كمون مطحون",1.25),("كمون حب",1.25),("كركم",1.00),("كزبرة ناشفة",1.00),("قرفة مطحونة",1.50),("قرفة خشب",5.00),("قرفة سيجار",7.00),("هيل مطحون",3.00),("هيل حب",4.00),("قرنفل",2.50),("زنجبيل مطحون",1.50),("بابريكا",1.50),("شطة ناعمة",1.00),("شطة مجروشة",1.25),("سماق",2.00),("يانسون",1.50),("كراوية",1.50),("محلب",3.00),("جوزة الطيب",3.00),("بهار مشكل",2.00),("بهار كبسة",2.00),("بهار منسف",2.00),("بهار شاورما",2.00),("بهار دجاج",2.00),("بهار سمك",2.00),("زعفران",5.00),("ورق غار",1.00),("زعتر بلدي",3.00),("زعتر ورق",6.00)],
    "الأعشاب الطبيعية": [
        ("ميرمية",1.50),("بابونج",1.50),("يانسون",1.50),("نعناع مجفف",1.25),("زوفا",1.50),("خزامى",2.00),("إكليل الجبل",1.50),("حلبة",1.00),("كركديه",1.75),("قراص",2.00),("شمر",1.50),("مليسة",2.00),("زعتر بري",2.00),("قشر رمان",1.50),("ورد مجفف",2.00),("لافندر",2.00),("ذيل الحصان",2.00),("سنامكي",1.50),("قشر ليمون مجفف",1.50),("أوراق زيتون مجففة",1.50)],
    "الحبوب والبقوليات": [
        ("فاصوليا",1.25),("عدس حب",1.00),("عدس مجروش",1.00),("حمص مكسيكي",1.50),("حمص حب",1.25),("برغل خشن",0.75),("برغل ناعم بلدي",1.00),("فريكة جنين",2.50),("قمح بلدي",0.75),("طحين قمح بلدي",1.00),("شوفان",2.00),("نشا سعودي",1.00),("كربونة",1.00),("رز بسمتي",2.00),("رز قصير",1.25),("ذرة فشار",1.25),("لوبيا",1.50),("فول حب",1.25),("بازيلاء مجففة",1.25),("سمسم",2.00)],
    "المونة البلدية": [
        ("زعتر بلدي",3.00),("دقة بلدية",2.50),("سماق بلدي",2.00),("فريكة بلدية",2.50),("قمح مجروش",1.00),("مريمية بلدية",1.50),("مكدوس",4.00),("مربى منزلي",3.00),("دبس رمان",3.00),("قزحة",2.50)],
    "الزيوت الطبيعية": [(n,1.0) for n in ["زيت اللوز 30 مل","زيت الخروع 30 مل","زيت جوز الهند 30 مل","زيت السمسم 30 مل","زيت الأرغان 30 مل","زيت الجوجوبا 30 مل","زيت النعناع 30 مل","زيت اللافندر 30 مل","زيت إكليل الجبل 30 مل","زيت شجرة الشاي 30 مل","زيت القرنفل 30 مل","زيت الحبة السوداء 30 مل","زيت الأفوكادو 30 مل","زيت بذور العنب 30 مل","زيت فيتامين E 30 مل","زيت حبة البركة 30 مل","زيت الأرجان 30 مل","زيت البابونج 30 مل","زيت القرفة 30 مل","زيت الزنجبيل 30 مل","زيت الثوم 30 مل","زيت البصل 30 مل","زيت الجرجير 30 مل","زيت الحلبة 30 مل","زيت الصبار 30 مل","زيت الجزر 30 مل","زيت الرمان 30 مل","زيت بذور القرع 30 مل","زيت الخردل 30 مل","زيت الكركم 30 مل","زيت الورد 30 مل","زيت الياسمين 30 مل","زيت خشب الصندل 30 مل","زيت اللبان 30 مل","زيت النيم 30 مل","زيت السدر 30 مل","زيت المورينجا 30 مل","زيت اليانسون 30 مل","زيت الهيل 30 مل","زيت الكراوية 30 مل","زيت الشمر 30 مل"]],
    "بذور الزراعة": [(n,2.0) for n in ["بذور بندورة","بذور خيار","بذور كوسا","بذور باذنجان","بذور فلفل","بذور بقدونس","بذور كزبرة","بذور جرجير","بذور خس","بذور نعناع","بذور ريحان","بذور زهور موسمية"]]
}
PERFUMES = ["عود ملكي","عود كمبودي","عود هندي","عود شرقي","عود فاخر","عود وعنبر","عود ومسك","عود ورد","مسك أبيض","مسك أسود","مسك الطهارة","مسك ورد","مسك فانيلا","مسك بودرة","مسك قطني","مسك ناعم","عنبر ملكي","عنبر شرقي","عنبر ذهبي","عنبر فانيلا","ورد طائفي","ورد دمشقي","ورد تركي","ورد ناعم","ياسمين","فل وياسمين","زهر البرتقال","زنبق","لافندر","فانيلا","فانيلا دافئة","كراميل","شوكولاتة","قهوة","قهوة وفانيلا","كاكاو","جوز الهند","لوز حلو","توت أحمر","توت أسود","فراولة","كرز","توت أزرق","مانجو","أناناس","خوخ","مشمش","تفاح أخضر","تفاح أحمر","كمثرى","ليمون","برتقال","برغموت","حمضيات","نعناع","ريحان","زنجبيل","قرفة","هيل","زعفران","جلد فاخر","خشب الصندل","خشب الأرز","باتشولي","طحلب السنديان","فيتيفر","أخشاب شرقية","أخشاب دافئة","عطر بحري","نسيم البحر","مطر","هواء منعش","عطر صيفي","عطر شتوي","عطر يومي","عطر مسائي","عطر كلاسيكي","عطر فاخر","عطر ناعم","عطر قوي","عطر زهري","عطر فاكهي","عطر خشبي","عطر بودري","عطر شرقي","عطر غربي","عطر رجالي كلاسيكي","عطر رجالي منعش","عطر رجالي خشبي","عطر رجالي فاخر","عطر رجالي رياضي","عطر رجالي ليلي","عطر نسائي زهري","عطر نسائي ناعم","عطر نسائي فاكهي","عطر نسائي فاخر","عطر نسائي رومانسي","عطر نسائي يومي","عطر للجنسين","عطر مسك وعنبر","عطر ورد وفانيلا","عطر عود وفانيلا","عطر حمضيات وأخشاب","عطر فواكه استوائية","عطر زهور بيضاء","عطر زهور الربيع","عطر بودرة الأطفال","عطر نظافة وانتعاش","عطر سكر وفانيلا","عطر كراميل وعنبر","عطر توت ومسك","عطر جلد وعنبر","عطر زعفران وعود","عطر صندل ومسك","عطر قهوة وعود","عطر ورد وعنبر","عطر زهرة البرتقال","عطر فانيلا ومسك","عطر ليمون ونعناع","عطر خشب وعنبر","أكوا دي جيو","وان مليون","غبار الذهب","غبار الفضة","لاكوست وايت","جاي جلفشي","كلك فلور","خمرة","خمرة بالقهوة","قصة","بربري هير","سكلبتشر","أبيض","دبليو","بيبي جونسون","سي ديليشيص","إتيرنيتي رجالي","كسبيليا","212 رجالي","تي روز","إليبس","كنزو","وشوشة","مارلين","سكندال تاج","كاندي سيكسي كرافيتي","تومي بوي","أماريج","بلو ليدي","الوسام","كنزو فلور","جادور","درهم","دارج","أمير العود","فوياج","سوفاج","سيلفر سينت","ويك اند","212","بندورة","صبايا","فندي","فرنكو فيري","شاليز","كريد الأفينتوس","أنفكتوس","عود مبخر","نوفو موند","يارا"]
CATALOG["العطور والتركيب"] = [(name,1.0) for name in PERFUMES]

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    discount = db.Column(db.Integer, nullable=False, default=0)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(180), nullable=False)
    category = db.Column(db.String(120), nullable=False, index=True)
    price = db.Column(db.Float, nullable=False, default=0)
    image_path = db.Column(db.String(400))
    image_data = db.Column(db.LargeBinary)
    image_mime = db.Column(db.String(100))
    active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class StoreSetting(db.Model):
    key = db.Column(db.String(80), primary_key=True)
    value = db.Column(db.Text, nullable=False)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_name = db.Column(db.String(160), nullable=False)
    phone = db.Column(db.String(60), nullable=False)
    address = db.Column(db.Text, nullable=False)
    notes = db.Column(db.Text)
    items_json = db.Column(db.Text, nullable=False)
    total = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(40), nullable=False, default="جديد")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

def setting(key, default=""):
    row = db.session.get(StoreSetting, key)
    return row.value if row else default

def set_setting(key, value):
    row = db.session.get(StoreSetting, key)
    if row:
        row.value = str(value)
    else:
        db.session.add(StoreSetting(key=key, value=str(value)))

def init_store():
    db.create_all()
    for name in CATALOG:
        if not Category.query.filter_by(name=name).first():
            db.session.add(Category(name=name))
    if Product.query.count() == 0:
        for category, entries in CATALOG.items():
            for name, price in entries:
                filename = re.sub(r"[^\w\-]+", "_", name, flags=re.UNICODE).strip("_") or "product"
                image_path = "products/" + filename + ".jpg"
                db.session.add(Product(name=name, category=category, price=price, image_path=image_path))
    if not StoreSetting.query.filter_by(key="whatsapp").first():
        set_setting("whatsapp", os.environ.get("WHATSAPP_NUMBER", "962781611698"))
    if not StoreSetting.query.filter_by(key="delivery_text").first():
        set_setting("delivery_text", "التوصيل يبدأ من 1 دينار حسب المنطقة")
    db.session.commit()

with app.app_context():
    init_store()

def is_admin():
    return session.get("admin_logged_in") is True

def admin_required():
    if not is_admin():
        return redirect(url_for("admin_login"))
    return None

def product_image_url(product):
    if product.image_data:
        return url_for("product_image", product_id=product.id)
    if product.image_path:
        return url_for("static", filename="images/" + product.image_path)
    return url_for("static", filename="images/spices.jpg")

@app.context_processor
def inject_globals():
    cart = session.get("cart", {})
    return {
        "cart_count": sum(int(v.get("qty", 0)) for v in cart.values()),
        "categories": [c.name for c in Category.query.order_by(Category.id).all()],
        "delivery_text": setting("delivery_text", "التوصيل يبدأ من 1 دينار حسب المنطقة")
    }

@app.route("/")
def home():
    selected = request.args.get("category", "")
    search = request.args.get("q", "").strip()
    query = Product.query.filter_by(active=True)
    if selected:
        query = query.filter_by(category=selected)
    if search:
        query = query.filter(Product.name.ilike("%" + search + "%"))
    products = query.order_by(Product.id.desc()).all()
    for p in products:
        cat = Category.query.filter_by(name=p.category).first()
        p.discount = cat.discount if cat else 0
        p.final_price = round(p.price * (1 - p.discount / 100), 2)
        p.perfume = p.category == "العطور والتركيب"
        p.image = product_image_url(p)
    return render_template("index.html", products=products, selected=selected, search=search)

@app.route("/product-image/<int:product_id>")
def product_image(product_id):
    product = db.session.get(Product, product_id)
    if not product or not product.image_data:
        abort(404)
    return send_file(BytesIO(product.image_data), mimetype=product.image_mime or "image/jpeg", max_age=3600)

@app.post("/add")
def add_to_cart():
    pid = request.form.get("pid", "")
    product = db.session.get(Product, int(pid)) if pid.isdigit() else None
    if not product or not product.active:
        flash("المنتج غير متاح حالياً")
        return redirect(url_for("home"))
    size = request.form.get("size", "1") if product.category == "العطور والتركيب" else ""
    if product.name == "زيت اللوز 30 مل":
        size = request.form.get("almond_type", "حلو")
        if size not in {"حلو", "مر"}:
            size = "حلو"
    if product.category == "العطور والتركيب" and size not in {"1", "3", "5"}:
        size = "1"
    key = str(product.id) + ":" + size
    cart = session.get("cart", {})
    cart.setdefault(key, {"pid": product.id, "size": size, "qty": 0})
    cart[key]["qty"] += max(1, min(int(request.form.get("qty", 1)), 99))
    session["cart"] = cart
    flash("تمت إضافة المنتج إلى السلة")
    return redirect(request.referrer or url_for("home"))

def current_price(product):
    category = Category.query.filter_by(name=product.category).first()
    discount = category.discount if category else 0
    return round(product.price * (1 - discount / 100), 2)

@app.route("/cart")
def cart():
    lines, total = [], 0
    for key, item in session.get("cart", {}).items():
        product = db.session.get(Product, int(item["pid"]))
        if not product:
            continue
        price = float(item["size"]) if product.category == "العطور والتركيب" else current_price(product)
        subtotal = price * item["qty"]
        total += subtotal
        label = product.name
        if product.name == "زيت اللوز 30 مل":
            label += " - " + item["size"]
        elif product.category == "العطور والتركيب":
            label += " - عبوة " + item["size"] + " دينار"
        lines.append({"key":key,"name":label,"category":product.category,"qty":item["qty"],"price":price,"subtotal":subtotal,"size":item["size"]})
    return render_template("cart.html", lines=lines, total=round(total, 2))

@app.post("/cart/update")
def update_cart():
    key = request.form.get("key", "")
    qty = max(0, min(int(request.form.get("qty", 0)), 99))
    cart = session.get("cart", {})
    if key in cart:
        if qty == 0:
            cart.pop(key)
        else:
            cart[key]["qty"] = qty
    session["cart"] = cart
    return redirect(url_for("cart"))

@app.post("/checkout")
def checkout():
    name = request.form.get("name", "").strip()
    phone = request.form.get("phone", "").strip()
    address = request.form.get("address", "").strip()
    notes = request.form.get("notes", "").strip()
    cart_data = session.get("cart", {})
    if not cart_data:
        flash("السلة فارغة")
        return redirect(url_for("cart"))
    rows, order_items, total = [], [], 0
    for item in cart_data.values():
        product = db.session.get(Product, int(item["pid"]))
        if not product:
            continue
        price = float(item["size"]) if product.category == "العطور والتركيب" else current_price(product)
        subtotal = price * item["qty"]
        total += subtotal
        label = product.name
        if product.category == "العطور والتركيب":
            label += " (عبوة " + item["size"] + " دنانير)"
        if product.name == "زيت اللوز 30 مل":
            label += " - " + item["size"]
        rows.append("- " + label + " × " + str(item["qty"]) + " = " + format(subtotal, ".2f") + " د.أ")
        order_items.append({"name":label,"qty":item["qty"],"price":price,"subtotal":round(subtotal,2)})
    order = Order(customer_name=name, phone=phone, address=address, notes=notes, items_json=json.dumps(order_items, ensure_ascii=False), total=round(total,2))
    db.session.add(order)
    db.session.commit()
    message = "طلب جديد من متجر العطّار\n" + "\n".join(rows) + "\nالمجموع: " + format(total, ".2f") + " د.أ\nالاسم: " + name + "\nالهاتف: " + phone + "\nالعنوان: " + address + "\nملاحظات: " + notes + "\n" + setting("delivery_text", "التوصيل يبدأ من 1 دينار حسب المنطقة")
    session["cart"] = {}
    whatsapp = re.sub(r"\D", "", setting("whatsapp", "962781611698"))
    return redirect("https://wa.me/" + whatsapp + "?text=" + quote(message))

@app.route("/admin", methods=["GET", "POST"])
def admin_login():
    if is_admin():
        return redirect(url_for("admin_dashboard"))
    if request.method == "POST":
        password = os.environ.get("ADMIN_PASSWORD", "")
        if not password:
            flash("يجب ضبط ADMIN_PASSWORD في إعدادات Render أولاً")
        elif request.form.get("password", "") == password:
            session["admin_logged_in"] = True
            return redirect(url_for("admin_dashboard"))
        else:
            flash("كلمة المرور غير صحيحة")
    return render_template("admin.html", login=True)

@app.route("/admin/logout", methods=["POST"])
def admin_logout():
    session.pop("admin_logged_in", None)
    return redirect(url_for("admin_login"))

@app.route("/admin/dashboard")
def admin_dashboard():
    gate = admin_required()
    if gate: return gate
    return render_template("admin.html", login=False, products=Product.query.order_by(Product.id.desc()).all(),
        categories=Category.query.order_by(Category.id).all(), orders=Order.query.order_by(Order.created_at.desc()).limit(100).all(),
        settings={"whatsapp":setting("whatsapp","962781611698"),"delivery_text":setting("delivery_text","التوصيل يبدأ من 1 دينار حسب المنطقة")},
        stats={"products":Product.query.count(),"orders":Order.query.count(),"new_orders":Order.query.filter_by(status="جديد").count()})

@app.post("/admin/products/save")
def admin_product_save():
    gate = admin_required()
    if gate: return gate
    product_id = request.form.get("id", "").strip()
    product = db.session.get(Product, int(product_id)) if product_id.isdigit() else Product()
    name = request.form.get("name", "").strip()
    category = request.form.get("category", "").strip()
    try:
        price = float(request.form.get("price", "0"))
    except ValueError:
        price = -1
    if not name or len(name) > 180 or not Category.query.filter_by(name=category).first() or price < 0 or price > 100000:
        flash("تحقق من اسم المنتج والقسم والسعر")
        return redirect(url_for("admin_dashboard"))
    product.name, product.category, product.price = name, category, price
    product.active = request.form.get("active") == "on"
    upload = request.files.get("image")
    if upload and upload.filename:
        data = upload.read()
        if len(data) > 5 * 1024 * 1024 or not upload.mimetype or not upload.mimetype.startswith("image/"):
            flash("الصورة غير صالحة أو أكبر من 5 ميغابايت")
            return redirect(url_for("admin_dashboard"))
        product.image_data = data
        product.image_mime = upload.mimetype
        product.image_path = None
    if not product_id:
        db.session.add(product)
    db.session.commit()
    flash("تم حفظ المنتج")
    return redirect(url_for("admin_dashboard"))

@app.post("/admin/products/delete")
def admin_product_delete():
    gate = admin_required()
    if gate: return gate
    product_id = request.form.get("id", "")
    product = db.session.get(Product, int(product_id)) if product_id.isdigit() else None
    if product:
        db.session.delete(product)
        db.session.commit()
        flash("تم حذف المنتج")
    return redirect(url_for("admin_dashboard"))

@app.post("/admin/categories/save")
def admin_category_save():
    gate = admin_required()
    if gate: return gate
    name = request.form.get("name", "").strip()
    if name and len(name) <= 120 and not Category.query.filter_by(name=name).first():
        db.session.add(Category(name=name))
        db.session.commit()
        flash("تمت إضافة القسم")
    else:
        flash("اسم القسم غير صالح أو موجود مسبقاً")
    return redirect(url_for("admin_dashboard"))

@app.post("/admin/categories/discount")
def admin_category_discount():
    gate = admin_required()
    if gate: return gate
    category = db.session.get(Category, int(request.form.get("id", "0")))
    try: percent = int(request.form.get("discount", "0"))
    except ValueError: percent = -1
    if category and 0 <= percent <= 90:
        category.discount = percent
        db.session.commit()
        flash("تم تحديث الخصم")
    else:
        flash("نسبة الخصم يجب أن تكون بين 0 و90")
    return redirect(url_for("admin_dashboard"))

@app.post("/admin/categories/delete")
def admin_category_delete():
    gate = admin_required()
    if gate: return gate
    category = db.session.get(Category, int(request.form.get("id", "0")))
    if category:
        if Product.query.filter_by(category=category.name).count():
            flash("لا يمكن حذف قسم يحتوي على منتجات؛ انقل المنتجات أولاً")
        else:
            db.session.delete(category)
            db.session.commit()
            flash("تم حذف القسم")
    return redirect(url_for("admin_dashboard"))

@app.post("/admin/orders/status")
def admin_order_status():
    gate = admin_required()
    if gate: return gate
    order = db.session.get(Order, int(request.form.get("id", "0")))
    status = request.form.get("status", "")
    if order and status in {"جديد","قيد التجهيز","تم التسليم","ملغي"}:
        order.status = status
        db.session.commit()
    return redirect(url_for("admin_dashboard"))

@app.post("/admin/settings")
def admin_settings():
    gate = admin_required()
    if gate: return gate
    whatsapp = re.sub(r"\D", "", request.form.get("whatsapp", ""))
    delivery = request.form.get("delivery_text", "").strip()[:300]
    if len(whatsapp) >= 10 and delivery:
        set_setting("whatsapp", whatsapp)
        set_setting("delivery_text", delivery)
        db.session.commit()
        flash("تم حفظ إعدادات المتجر")
    else:
        flash("تحقق من رقم واتساب ونص التوصيل")
    return redirect(url_for("admin_dashboard"))

@app.errorhandler(413)
def too_large(_error):
    flash("حجم الملف أكبر من 5 ميغابايت")
    return redirect(url_for("admin_dashboard"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
