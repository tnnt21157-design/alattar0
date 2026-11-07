import re
from flask import Flask, render_template, request, redirect, url_for, session, flash
from urllib.parse import quote
import sqlite3, os
from pathlib import Path

BASE = Path(__file__).resolve().parent
DB = BASE / 'store.db'
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'change-this-secret-key-before-deploy')
WHATSAPP = os.environ.get('WHATSAPP_NUMBER', '962781611698')

# بيانات المنتجات: الاسم والسعر بالدينار الأردني
CATALOG = {
    'البهارات والتوابل': [
        ('فلفل أسود مطحون',1.50),('فلفل أبيض',1.75),('كمون مطحون',1.25),('كمون حب',1.25),('كركم',1.00),('كزبرة ناشفة',1.00),('قرفة مطحونة',1.50),('قرفة خشب',5.00),('قرفة سيجار',7.00),('هيل مطحون',3.00),('هيل حب',4.00),('قرنفل',2.50),('زنجبيل مطحون',1.50),('بابريكا',1.50),('شطة ناعمة',1.00),('شطة مجروشة',1.25),('سماق',2.00),('يانسون',1.50),('كراوية',1.50),('محلب',3.00),('جوزة الطيب',3.00),('بهار مشكل',2.00),('بهار كبسة',2.00),('بهار منسف',2.00),('بهار شاورما',2.00),('بهار دجاج',2.00),('بهار سمك',2.00),('زعفران',5.00),('ورق غار',1.00),('زعتر بلدي',3.00),('زعتر ورق',6.00)
    ],
    'الأعشاب الطبيعية': [
        ('ميرمية',1.50),('بابونج',1.50),('يانسون',1.50),('نعناع مجفف',1.25),('زوفا',1.50),('خزامى',2.00),('إكليل الجبل',1.50),('حلبة',1.00),('كركديه',1.75),('قراص',2.00),('شمر',1.50),('مليسة',2.00),('زعتر بري',2.00),('قشر رمان',1.50),('ورد مجفف',2.00),('لافندر',2.00),('ذيل الحصان',2.00),('سنامكي',1.50),('قشر ليمون مجفف',1.50),('أوراق زيتون مجففة',1.50)
    ],
    'الحبوب والبقوليات': [
        ('فاصوليا',1.25),('عدس حب',1.00),('عدس مجروش',1.00),('حمص مكسيكي',1.50),('حمص حب',1.25),('برغل خشن',0.75),('برغل ناعم بلدي',1.00),('فريكة جنين',2.50),('قمح بلدي',0.75),('طحين قمح بلدي',1.00),('شوفان',2.00),('نشا سعودي',1.00),('كربونة',1.00),('رز بسمتي',2.00),('رز قصير',1.25),('ذرة فشار',1.25),('لوبيا',1.50),('فول حب',1.25),('بازيلاء مجففة',1.25),('سمسم',2.00)
    ],
    'المونة البلدية': [
        ('زعتر بلدي',3.00),('دقة بلدية',2.50),('سماق بلدي',2.00),('فريكة بلدية',2.50),('قمح مجروش',1.00),('مريمية بلدية',1.50),('مكدوس',4.00),('مربى منزلي',3.00),('دبس رمان',3.00),('قزحة',2.50)
    ],
    'الزيوت الطبيعية': [('زيت اللوز 30 مل', 1.0), ('زيت الخروع 30 مل', 1.0), ('زيت جوز الهند 30 مل', 1.0), ('زيت السمسم 30 مل', 1.0), ('زيت الأرغان 30 مل', 1.0), ('زيت الجوجوبا 30 مل', 1.0), ('زيت النعناع 30 مل', 1.0), ('زيت اللافندر 30 مل', 1.0), ('زيت إكليل الجبل 30 مل', 1.0), ('زيت شجرة الشاي 30 مل', 1.0), ('زيت القرنفل 30 مل', 1.0), ('زيت الحبة السوداء 30 مل', 1.0), ('زيت الأفوكادو 30 مل', 1.0), ('زيت بذور العنب 30 مل', 1.0), ('زيت فيتامين E 30 مل', 1.0), ('زيت حبة البركة 30 مل', 1.0), ('زيت الأرجان 30 مل', 1.0), ('زيت البابونج 30 مل', 1.0), ('زيت القرفة 30 مل', 1.0), ('زيت الزنجبيل 30 مل', 1.0), ('زيت الثوم 30 مل', 1.0), ('زيت البصل 30 مل', 1.0), ('زيت الجرجير 30 مل', 1.0), ('زيت الحلبة 30 مل', 1.0), ('زيت الصبار 30 مل', 1.0), ('زيت الجزر 30 مل', 1.0), ('زيت الرمان 30 مل', 1.0), ('زيت بذور القرع 30 مل', 1.0), ('زيت الخردل 30 مل', 1.0), ('زيت الكركم 30 مل', 1.0), ('زيت الورد 30 مل', 1.0), ('زيت الياسمين 30 مل', 1.0), ('زيت خشب الصندل 30 مل', 1.0), ('زيت اللبان 30 مل', 1.0), ('زيت النيم 30 مل', 1.0), ('زيت السدر 30 مل', 1.0), ('زيت المورينجا 30 مل', 1.0), ('زيت اليانسون 30 مل', 1.0), ('زيت الهيل 30 مل', 1.0), ('زيت الكراوية 30 مل', 1.0), ('زيت الشمر 30 مل', 1.0)],
    'بذور الزراعة': [
        ('بذور بندورة',2.00),('بذور خيار',2.00),('بذور كوسا',2.00),('بذور باذنجان',2.00),('بذور فلفل',2.00),('بذور بقدونس',2.00),('بذور كزبرة',2.00),('بذور جرجير',2.00),('بذور خس',2.00),('بذور نعناع',2.00),('بذور ريحان',2.00),('بذور زهور موسمية',2.00)
    ]
}

PERFUMES = [
'عود ملكي','عود كمبودي','عود هندي','عود شرقي','عود فاخر','عود وعنبر','عود ومسك','عود ورد','مسك أبيض','مسك أسود',
'مسك الطهارة','مسك ورد','مسك فانيلا','مسك بودرة','مسك قطني','مسك ناعم','عنبر ملكي','عنبر شرقي','عنبر ذهبي','عنبر فانيلا',
'ورد طائفي','ورد دمشقي','ورد تركي','ورد ناعم','ياسمين','فل وياسمين','زهر البرتقال','زنبق','لافندر','فانيلا',
'فانيلا دافئة','كراميل','شوكولاتة','قهوة','قهوة وفانيلا','كاكاو','جوز الهند','لوز حلو','توت أحمر','توت أسود',
'فراولة','كرز','توت أزرق','مانجو','أناناس','خوخ','مشمش','تفاح أخضر','تفاح أحمر','كمثرى',
'ليمون','برتقال','برغموت','حمضيات','نعناع','ريحان','زنجبيل','قرفة','هيل','زعفران',
'جلد فاخر','خشب الصندل','خشب الأرز','باتشولي','طحلب السنديان','فيتيفر','أخشاب شرقية','أخشاب دافئة','عطر بحري','نسيم البحر',
'مطر','هواء منعش','عطر صيفي','عطر شتوي','عطر يومي','عطر مسائي','عطر كلاسيكي','عطر فاخر','عطر ناعم','عطر قوي',
'عطر زهري','عطر فاكهي','عطر خشبي','عطر بودري','عطر شرقي','عطر غربي','عطر رجالي كلاسيكي','عطر رجالي منعش','عطر رجالي خشبي','عطر رجالي فاخر',
'عطر رجالي رياضي','عطر رجالي ليلي','عطر نسائي زهري','عطر نسائي ناعم','عطر نسائي فاكهي','عطر نسائي فاخر','عطر نسائي رومانسي','عطر نسائي يومي','عطر للجنسين','عطر مسك وعنبر',
'عطر ورد وفانيلا','عطر عود وفانيلا','عطر حمضيات وأخشاب','عطر فواكه استوائية','عطر زهور بيضاء','عطر زهور الربيع','عطر بودرة الأطفال','عطر نظافة وانتعاش','عطر سكر وفانيلا','عطر كراميل وعنبر',
'عطر توت ومسك','عطر جلد وعنبر','عطر زعفران وعود','عطر صندل ومسك','عطر قهوة وعود','عطر ورد وعنبر',
'عطر زهرة البرتقال','عطر فانيلا ومسك','عطر ليمون ونعناع','عطر خشب وعنبر'
]
PERFUMES += ['أكوا دي جيو', 'وان مليون', 'غبار الذهب', 'غبار الفضة', 'لاكوست وايت', 'جاي جلفشي', 'كلك فلور', 'خمرة', 'خمرة بالقهوة', 'قصة', 'بربري هير', 'سكلبتشر', 'أبيض', 'دبليو', 'بيبي جونسون', 'سي ديليشيص', 'إتيرنيتي رجالي', 'كسبيليا', '212 رجالي', 'تي روز', 'إليبس', 'كنزو', 'وشوشة', 'مارلين', 'سكندال تاج', 'كاندي سيكسي كرافيتي', 'تومي بوي', 'أماريج', 'بلو ليدي', 'الوسام', 'كنزو فلور', 'جادور', 'درهم', 'دارج', 'أمير العود', 'فوياج', 'سوفاج', 'سيلفر سينت', 'ويك اند', '212', 'بندورة', 'صبايا', 'فندي', 'فرنكو فيري', 'شاليز', 'كريد الأفينتوس', 'أنفكتوس', 'عود مبخر', 'نوفو موند', 'يارا']

assert len(PERFUMES) == 170, f'عدد العطور الحالي {len(PERFUMES)} وليس 120'
CATALOG['العطور والتركيب'] = [(name, 1.00) for name in PERFUMES]


def db():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con


def init_db():
    with db() as con:
        con.execute('''CREATE TABLE IF NOT EXISTS discounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            percent INTEGER NOT NULL CHECK(percent BETWEEN 0 AND 90)
        )''')

init_db()
def product_image(category, name):
    filename = re.sub(r"[^\w\-]+", "_", name, flags=re.UNICODE).strip("_") or "product"
    path = BASE / "static" / "images" / "products" / (filename + ".jpg")
    if path.is_file():
        return "products/" + filename + ".jpg"
    return "spices.jpg"


def all_products():
    items=[]
    for category, products in CATALOG.items():
        for i,(name,price) in enumerate(products):
            pid=f'{list(CATALOG).index(category)}-{i}'
            items.append({
                'id':pid,
                'category':category,
                'name':name,
                'price':price,
                'perfume':category=='العطور والتركيب',
                'image':product_image(category,name)
            })
    return items
PRODUCTS = all_products()


def discount_map():
    with db() as con:
        rows=con.execute('SELECT category, percent FROM discounts').fetchall()
    return {r['category']:r['percent'] for r in rows}


def product_by_id(pid):
    return next((p for p in PRODUCTS if p['id']==pid),None)

@app.context_processor
def inject_globals():
    cart=session.get('cart',{})
    return {'cart_count':sum(int(v.get('qty',0)) for v in cart.values()), 'categories':list(CATALOG.keys())}

@app.route('/')
def home():
    selected=request.args.get('category','')
    search=request.args.get('q','').strip()
    discounts=discount_map()
    products=[p.copy() for p in PRODUCTS if (not selected or p['category']==selected) and (not search or search in p['name'])]
    for p in products:
        p['discount']=discounts.get(p['category'],0)
        p['final_price']=round(p['price']*(1-p['discount']/100),2)
    return render_template('index.html',products=products,selected=selected,search=search,discounts=discounts)

@app.post('/add')
def add_to_cart():
    pid=request.form.get('pid','')
    product=product_by_id(pid)
    if not product:
        flash('المنتج غير موجود')
        return redirect(url_for('home'))
    size=request.form.get('size','1') if product['perfume'] else ''
    if product['name']=='زيت اللوز 30 مل':
        size=request.form.get('almond_type','حلو')
        if size not in {'حلو','مر'}:
            size='حلو'
    if product['perfume'] and size not in {'1','3','5'}:
        size='1'
    key=f"{pid}:{size}"
    cart=session.get('cart',{})
    cart.setdefault(key,{'pid':pid,'size':size,'qty':0})
    cart[key]['qty']+=max(1,min(int(request.form.get('qty',1)),99))
    session['cart']=cart
    flash('تمت إضافة المنتج إلى السلة')
    return redirect(request.referrer or url_for('home'))

@app.route('/cart')
def cart():
    cart_data=session.get('cart',{})
    discounts=discount_map()
    lines=[]; total=0
    for key,item in cart_data.items():
        p=product_by_id(item['pid'])
        if not p: continue
        price=float(item['size']) if p['perfume'] else p['price']
        price=round(price*(1-discounts.get(p['category'],0)/100),2)
        subtotal=price*item['qty']; total+=subtotal
        lines.append({'key':key,'name':(p['name']+' - '+item['size'] if p['name']=='زيت اللوز 30 مل' else p['name']),'category':p['category'],'qty':item['qty'],'price':price,'subtotal':subtotal,'size':item['size']})
    return render_template('cart.html',lines=lines,total=round(total,2))

@app.post('/cart/update')
def update_cart():
    key=request.form.get('key',''); qty=max(0,min(int(request.form.get('qty',0)),99))
    cart=session.get('cart',{})
    if key in cart:
        if qty==0: cart.pop(key)
        else: cart[key]['qty']=qty
    session['cart']=cart
    return redirect(url_for('cart'))

@app.post('/checkout')
def checkout():
    name=request.form.get('name','').strip(); phone=request.form.get('phone','').strip(); address=request.form.get('address','').strip(); notes=request.form.get('notes','').strip()
    cart_data=session.get('cart',{})
    if not cart_data:
        flash('السلة فارغة')
        return redirect(url_for('cart'))
    discounts=discount_map(); rows=[]; total=0
    for item in cart_data.values():
        p=product_by_id(item['pid'])
        if not p: continue
        price=float(item['size']) if p['perfume'] else p['price']
        price=round(price*(1-discounts.get(p['category'],0)/100),2)
        sub=price*item['qty']; total+=sub
        label=f"{p['name']} (عبوة {item['size']} دنانير)" if p['perfume'] else p['name']
        if p['name']=='زيت اللوز 30 مل':
            label=f"{p['name']} - {item['size']}" 
        rows.append(f"- {label} × {item['qty']} = {sub:.2f} د.أ")
    message='طلب جديد من متجر العطّار%0A'
    message='طلب جديد من متجر العطّار\n'+'\n'.join(rows)+f'\nالمجموع: {total:.2f} د.أ\nالاسم: {name}\nالهاتف: {phone}\nالعنوان: {address}\nملاحظات: {notes}\nالتوصيل يبدأ من 1 دينار حسب المنطقة'
    session['cart']={}
    return redirect('https://wa.me/'+WHATSAPP+'?text='+quote(message))

@app.route('/admin', methods=['GET','POST'])
def admin():
    # صفحة خصومات بسيطة محمية بكلمة مرور من متغير ADMIN_PASSWORD
    if request.method=='POST':
        if request.form.get('password') != os.environ.get('ADMIN_PASSWORD','') or not os.environ.get('ADMIN_PASSWORD'):
            flash('كلمة المرور غير صحيحة أو لم يتم إعدادها في إعدادات الاستضافة')
            return redirect(url_for('admin'))
        category=request.form.get('category','')
        percent=max(0,min(int(request.form.get('percent',0)),90))
        if category in CATALOG:
            with db() as con:
                con.execute('DELETE FROM discounts WHERE category=?',(category,))
                if percent: con.execute('INSERT INTO discounts(category,percent) VALUES(?,?)',(category,percent))
            flash('تم تحديث الخصم')
        return redirect(url_for('admin'))
    return render_template('admin.html',categories=list(CATALOG.keys()),discounts=discount_map())

if __name__=='__main__':
    init_db()
    app.run(host='0.0.0.0',port=int(os.environ.get('PORT',5000)),debug=False)
