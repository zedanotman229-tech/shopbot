#!/usr/bin/env python3
"""🛒 بوت متجر فاخر - نصوص تسويقية راقية"""

import logging, json, os
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import (Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, ConversationHandler)

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = "6977546380:AAHG36AW0faUuNjxg3Mb9HOo-sR3TmFs_Y4"
ADMIN_IDS = [664958477]
DATA_FILE = "/root/shop_data.json"
AWAIT_PAYMENT_PROOF = 1

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"products": {}, "orders": {}, "settings": {"payment_methods": {}, "welcome_message": "", "order_counter": 1000, "usd_to_lyd": 4.85}}

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def is_admin(uid): return uid in ADMIN_IDS
def get_order_id(data):
    data["settings"]["order_counter"] = data["settings"].get("order_counter", 1000) + 1
    save_data(data)
    return f"ORD-{data['settings']['order_counter']}"
def format_price(p, c="USD"): return f"{p:.2f} د.ل" if c == "LYD" else f"${p:.2f}"
def price_in_lyd(usd):
    return usd * load_data()["settings"].get("usd_to_lyd", 4.85)

def main_keyboard():
    return ReplyKeyboardMarkup([
        ["🛍️ تصفّح المتجر", "🛒 سلّتي"],
        ["📦 طلباتي", "👑 الأكثر طلباً"],
        ["💬 الدعم الفني", "ℹ️ من نحن"]
    ], resize_keyboard=True, input_field_placeholder="اختر بزوقك من قائمتنا الراقية...")

def admin_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📦 المنتجات", callback_data="admin_products"), InlineKeyboardButton("📊 الإحصائيات", callback_data="admin_stats")],
        [InlineKeyboardButton("📋 الطلبات المعلقة", callback_data="admin_orders")]
    ])

# ─── البداية ─────────────────────────────────────────────────────
async def start(update, context):
    user = update.effective_user
    text = (
        f"🌟 *أهلاً بك يا {user.first_name}*\n"
        f"في وجهتك الأولى للمنتجات الرقمية الأصلية\n"
        f"━━━━━━━━━━━━━━━━\n\n"
        f"حيث تلتقي *الجودة* بـ *الثقة*، ونمنحك تجربة تسوّق تليق بك.\n\n"
        f"✦ منتجات أصلية موثّقة 100%\n"
        f"✦ استلام فوري لحظة تأكيد الدفع\n"
        f"✦ ضمان كامل واسترداد خلال 24 ساعة\n"
        f"✦ خدمة عملاء لا تنام طوال الأسبوع\n\n"
        f"_آلاف العملاء وثقوا بنا... والدور عليك الآن._\n\n"
        f"تفضّل، رحلتك تبدأ من الأسفل 👇"
    )
    await update.message.reply_text(text, parse_mode='Markdown', reply_markup=main_keyboard())

async def admin_panel(update, context):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ ليس لديك صلاحية.")
        return
    data = load_data()
    orders = data.get("orders", {})
    pending = sum(1 for o in orders.values() if o["status"] in ["pending", "awaiting_confirmation"])
    confirmed = sum(1 for o in orders.values() if o["status"] == "confirmed")
    revenue = sum(o["total"] for o in orders.values() if o["status"] == "confirmed")
    text = (f"👑 *لوحة تحكم المدير*\n━━━━━━━━━━━━━━━━\n\n📦 المنتجات: *{len(data['products'])}*\n⏳ معلقة: *{pending}*\n✅ مؤكدة: *{confirmed}*\n💰 الإيرادات: *{format_price(revenue)}*")
    await update.message.reply_text(text, parse_mode='Markdown', reply_markup=admin_keyboard())

# ─── المنتجات ────────────────────────────────────────────────────
async def show_products(update, context):
    data = load_data()
    categories = {}
    for pid, p in data["products"].items():
        categories.setdefault(p["category"], []).append((pid, p))
    emojis = {"أنظمة التشغيل": "💻", "برامج التصميم": "🎨", "العاب": "🎮", "الأمن والخصوصية": "🛡️", "الأمن": "🛡️", "ترفيه": "🎬"}
    keyboard = []
    for cat in categories:
        keyboard.append([InlineKeyboardButton(f"{emojis.get(cat,'✦')} {cat}  ·  {len(categories[cat])} منتج", callback_data=f"cat_{cat}")])
    keyboard.append([InlineKeyboardButton("✨ استعرض كل ما لدينا", callback_data="all_products")])
    await update.message.reply_text(
        "🛍️ *أقسام متجرنا*\n━━━━━━━━━━━━━━━━\n\n"
        "تصفّح بهدوء... كل قسم يحمل ما يستحق اقتناءه.\n"
        "اختر ما يناسب ذوقك 👇",
        parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def show_all_products(update, context):
    query = update.callback_query
    await query.answer()
    data = load_data()
    keyboard = []
    for pid, p in data["products"].items():
        tag = "✓ متوفر" if p["available"] else "✕ نفد"
        keyboard.append([InlineKeyboardButton(f"{p['name']}  ·  {format_price(p['price'])}  ·  {tag}", callback_data=f"product_{pid}")])
    keyboard.append([InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="back_main")])
    await query.edit_message_text(
        "✨ *تشكيلتنا الكاملة*\n━━━━━━━━━━━━━━━━\n\n"
        "كل منتج هنا مختار بعناية ليمنحك أفضل قيمة.",
        parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def show_product_detail(update, context):
    query = update.callback_query
    await query.answer()
    pid = query.data.replace("product_", "")
    data = load_data()
    p = data["products"].get(pid)
    if not p:
        await query.answer("❌ المنتج غير موجود", show_alert=True)
        return
    lyd = price_in_lyd(p["price"])
    if p["available"]:
        status_line = "✓ _متوفر الآن — والكميات محدودة، فبادر باقتنائه._"
    else:
        status_line = "✕ _نفدت الكمية حالياً — تابعنا لتعود قريباً._"
    text = (
        f"✦━━━━━━━━━━━━━━━✦\n"
        f"   *{p['name']}*\n"
        f"✦━━━━━━━━━━━━━━━✦\n\n"
        f"“{p['description']}”\n\n"
        f"📂 القسم: _{p['category']}_\n"
        f"{status_line}\n\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"💰 *{format_price(p['price'])}*  ·  🇱🇾 *{format_price(lyd,'LYD')}*\n"
        f"━━━━━━━━━━━━━━━━\n\n"
        f"🛡️ _مضمون أصلي · استلام فوري · دعم متواصل_"
    )
    keyboard = []
    if p["available"]:
        keyboard.append([InlineKeyboardButton("⚡ اقتنِه الآن", callback_data=f"buy_now_{pid}")])
        keyboard.append([InlineKeyboardButton("🛒 أضِفه لسلّتي", callback_data=f"add_cart_{pid}")])
    keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="all_products")])
    await query.edit_message_text(text, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))

async def show_category(update, context, category):
    query = update.callback_query
    await query.answer()
    data = load_data()
    products = {pid: p for pid, p in data["products"].items() if p["category"] == category}
    keyboard = []
    for pid, p in products.items():
        tag = "✓" if p["available"] else "✕"
        keyboard.append([InlineKeyboardButton(f"{tag} {p['name']}  ·  {format_price(p['price'])}", callback_data=f"product_{pid}")])
    keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="all_products")])
    await query.edit_message_text(f"📂 *{category}*\n━━━━━━━━━━━━━━━━\n\nاختر ما يستهويك 👇", parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))

# ─── السلة ───────────────────────────────────────────────────────
async def add_to_cart(update, context):
    query = update.callback_query
    pid = query.data.replace("add_cart_", "")
    p = load_data()["products"].get(pid)
    context.user_data.setdefault("cart", [])
    context.user_data["cart"].append({"pid": pid, "name": p["name"], "price": p["price"]})
    await query.answer(f"✓ أضفنا {p['name']} إلى سلّتك بنجاح", show_alert=True)

async def show_cart(update, context):
    cart = context.user_data.get("cart", [])
    if not cart:
        await update.message.reply_text(
            "🛒 *سلّتك تنتظر أن تمتلئ*\n━━━━━━━━━━━━━━━━\n\n"
            "لم تُضِف شيئاً بعد... دعنا نغيّر ذلك.\n"
            "تشكيلتنا الراقية على بُعد نقرة واحدة 👇",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✨ ابدأ التسوّق", callback_data="all_products")]])
        )
        return
    total = sum(i["price"] for i in cart)
    text = "🛒 *سلّة مشترياتك*\n━━━━━━━━━━━━━━━━\n\n"
    for i, item in enumerate(cart, 1):
        text += f"{i}.  {item['name']}\n     {format_price(item['price'])}\n\n"
    text += (f"━━━━━━━━━━━━━━━━\n"
             f"الإجمالي: *{format_price(total)}*\n"
             f"🇱🇾 *{format_price(price_in_lyd(total),'LYD')}*\n"
             f"━━━━━━━━━━━━━━━━\n\n"
             f"_خطوة واحدة تفصلك عن منتجاتك._")
    keyboard = [
        [InlineKeyboardButton("💳 أكمل الطلب الآن", callback_data="checkout")],
        [InlineKeyboardButton("🗑️ إفراغ", callback_data="clear_cart"), InlineKeyboardButton("➕ أضِف المزيد", callback_data="all_products")]
    ]
    await update.message.reply_text(text, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))

# ─── الدفع ───────────────────────────────────────────────────────
async def checkout(update, context):
    query = update.callback_query
    await query.answer()
    pay = load_data()["settings"]["payment_methods"]
    keyboard = []
    if pay.get("usdt", {}).get("enabled"): keyboard.append([InlineKeyboardButton("💰 USDT (TRC20)", callback_data="pay_usdt")])
    if pay.get("paypal", {}).get("enabled"): keyboard.append([InlineKeyboardButton("🅿️ PayPal", callback_data="pay_paypal")])
    if pay.get("binance", {}).get("enabled"): keyboard.append([InlineKeyboardButton("🟡 Binance Pay", callback_data="pay_binance")])
    if pay.get("libyana", {}).get("enabled"): keyboard.append([InlineKeyboardButton("📱 رصيد ليبيانا", callback_data="pay_libyana")])
    if pay.get("bank_transfer", {}).get("enabled"): keyboard.append([InlineKeyboardButton("🏦 تحويل مصرفي", callback_data="pay_bank_transfer")])
    keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="back_cart")])
    await query.edit_message_text(
        "💳 *طريقة الدفع المفضّلة لديك*\n━━━━━━━━━━━━━━━━\n\n"
        "اختر ما يناسبك من طرقنا الآمنة والموثوقة 👇\n"
        "_كل معاملاتك محميّة بالكامل._",
        parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def show_payment_info(update, context):
    query = update.callback_query
    await query.answer()
    method = query.data.replace("pay_", "")
    data = load_data()
    pay = data["settings"]["payment_methods"]
    cart = context.user_data.get("cart", [])
    total = sum(i["price"] for i in cart)
    oid = get_order_id(data)
    data["orders"][oid] = {"id": oid, "user_id": query.from_user.id, "username": query.from_user.username or query.from_user.first_name, "items": cart, "total": total, "payment_method": method, "status": "pending", "created_at": datetime.now().isoformat(), "confirmed_at": None}
    save_data(data)
    context.user_data["current_order"] = oid
    lyd = price_in_lyd(total)
    hdr = f"🧾 طلبك رقم: `{oid}`\n💰 المبلغ المطلوب: *{format_price(total)}*"
    if method == "usdt":
        p = pay["usdt"]; text = f"💰 *الدفع عبر USDT*\n━━━━━━━━━━━━━━━━\n\n{hdr}\n\n📡 الشبكة: {p['network']}\n📋 العنوان:\n`{p['address']}`\n\n_أرسل المبلغ تماماً، ثم أرفق لقطة الشاشة وسنتكفّل بالباقي._"
    elif method == "paypal":
        p = pay["paypal"]; text = f"🅿️ *الدفع عبر PayPal*\n━━━━━━━━━━━━━━━━\n\n{hdr}\n\n📧 الحساب:\n`{p['email']}`\n\n_لا تنسَ ذكر رقم الطلب في الملاحظة._"
    elif method == "binance":
        p = pay["binance"]; text = f"🟡 *الدفع عبر Binance*\n━━━━━━━━━━━━━━━━\n\n{hdr}\n\n🆔 المعرّف:\n`{p['id']}`\n\n_أرفق لقطة الشاشة بعد التحويل مباشرة._"
    elif method == "libyana":
        p = pay["libyana"]; text = f"📱 *الدفع برصيد ليبيانا*\n━━━━━━━━━━━━━━━━\n\n{hdr}\n🇱🇾 بالدينار: *{format_price(lyd,'LYD')}*\n\n📞 الرقم: `{p['number']}`\n👤 الاسم: {p['name']}\n\n_حوّل المبلغ واذكر رقم طلبك_ `{oid}`"
    elif method == "bank_transfer":
        p = pay["bank_transfer"]; text = f"🏦 *التحويل المصرفي*\n━━━━━━━━━━━━━━━━\n\n{hdr}\n🇱🇾 بالدينار: *{format_price(lyd,'LYD')}*\n\n🏛️ {p['bank_name']}\n👤 {p['account_name']}\n🔢 `{p['account_number']}`\n📋 `{p['iban']}`\n\n_اذكر رقم طلبك_ `{oid}` _في بيان التحويل._"
    else: text = "❌ طريقة غير معروفة"
    keyboard = [[InlineKeyboardButton("📸 دفعتُ — إرسال الإثبات", callback_data="send_proof")], [InlineKeyboardButton("🔙 رجوع", callback_data="checkout")]]
    await query.edit_message_text(text, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))
    labels = {"usdt": "USDT", "paypal": "PayPal", "binance": "Binance", "libyana": "ليبيانا", "bank_transfer": "تحويل"}
    for aid in ADMIN_IDS:
        try: await context.bot.send_message(aid, f"🔔 *طلب جديد!*\n🧾 `{oid}`\n👤 @{data['orders'][oid]['username']}\n💰 {format_price(total)}\n💳 {labels.get(method, method)}", parse_mode='Markdown')
        except: pass

async def request_payment_proof(update, context):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "📸 *أرسل إثبات الدفع*\n━━━━━━━━━━━━━━━━\n\n"
        "أرفق صورة عملية الدفع، وسيتولّى فريقنا مراجعتها فوراً.\n"
        "_دقائق معدودة ويصلك منتجك._ ⏱️",
        parse_mode='Markdown'
    )
    return AWAIT_PAYMENT_PROOF

async def receive_payment_proof(update, context):
    oid = context.user_data.get("current_order")
    data = load_data()
    if oid and oid in data["orders"]:
        data["orders"][oid]["status"] = "awaiting_confirmation"
        save_data(data)
    await update.message.reply_text(
        f"✓ *استلمنا إثبات دفعك بنجاح*\n━━━━━━━━━━━━━━━━\n\n"
        f"🧾 طلبك: `{oid}`\n\n"
        f"فريقنا يراجع طلبك الآن، وستصلك منتجاتك خلال لحظات.\n\n"
        f"_نُقدّر ثقتك الغالية بنا._ 🌟",
        parse_mode='Markdown', reply_markup=main_keyboard()
    )
    cap = f"📸 *إثبات دفع*\n🧾 `{oid}`\n👤 @{update.effective_user.username or update.effective_user.first_name}"
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("✅ تأكيد", callback_data=f"confirm_{oid}"), InlineKeyboardButton("❌ رفض", callback_data=f"reject_{oid}")]])
    for aid in ADMIN_IDS:
        try:
            if update.message.photo: await context.bot.send_photo(aid, update.message.photo[-1].file_id, caption=cap, parse_mode='Markdown', reply_markup=kb)
            elif update.message.document: await context.bot.send_document(aid, update.message.document.file_id, caption=cap, parse_mode='Markdown', reply_markup=kb)
        except Exception as e: logger.error(e)
    context.user_data["cart"] = []
    return ConversationHandler.END

async def confirm_order(update, context):
    query = update.callback_query
    if not is_admin(query.from_user.id):
        await query.answer("⛔", show_alert=True); return
    oid = query.data.replace("confirm_", "")
    data = load_data()
    o = data["orders"].get(oid)
    if not o:
        await query.answer("❌", show_alert=True); return
    o["status"] = "confirmed"; o["confirmed_at"] = datetime.now().isoformat()
    save_data(data)
    await query.answer("✅ تم التأكيد!")
    try: await query.edit_message_caption(f"{query.message.caption}\n\n✅ *تم التأكيد*", parse_mode='Markdown')
    except: pass
    items = "\n".join([f"   ✦ {i['name']}" for i in o["items"]])
    try: await context.bot.send_message(o["user_id"], f"🎉 *تهانينا! تم تأكيد طلبك*\n━━━━━━━━━━━━━━━━\n\n🧾 `{oid}`\n📦 منتجاتك:\n{items}\n\nنعمل على تجهيزها وإرسالها إليك حالاً.\n\n_سعدنا بخدمتك، ونتطلّع لعودتك._ 🌟", parse_mode='Markdown')
    except Exception as e: logger.error(e)

async def reject_order(update, context):
    query = update.callback_query
    if not is_admin(query.from_user.id):
        await query.answer("⛔", show_alert=True); return
    oid = query.data.replace("reject_", "")
    data = load_data()
    o = data["orders"].get(oid)
    if o: o["status"] = "rejected"; save_data(data)
    await query.answer("❌ تم الرفض")
    try: await query.edit_message_caption(f"{query.message.caption}\n\n❌ *مرفوض*", parse_mode='Markdown')
    except: pass
    try: await context.bot.send_message(o["user_id"], f"نعتذر، لم نتمكّن من تأكيد طلبك `{oid}`.\nتواصل مع دعمنا وسنحلّ الأمر فوراً. 🤝", parse_mode='Markdown')
    except: pass

async def show_my_orders(update, context):
    uid = update.effective_user.id
    data = load_data()
    orders = {oid: o for oid, o in data["orders"].items() if o["user_id"] == uid}
    if not orders:
        await update.message.reply_text("📦 *سجلّ طلباتك فارغ*\n━━━━━━━━━━━━━━━━\n\nلم تطلب منّا شيئاً بعد...\nأول تجربة معنا ستكون بدايةً لثقة طويلة. 🌟", parse_mode='Markdown')
        return
    text = "📦 *سجلّ طلباتك*\n━━━━━━━━━━━━━━━━\n\n"
    icons = {"pending": "⏳ بانتظار الدفع", "awaiting_confirmation": "🔍 قيد المراجعة", "confirmed": "✅ مكتمل", "rejected": "❌ ملغى"}
    for oid, o in sorted(orders.items(), reverse=True)[:10]:
        text += f"`{oid}` · {format_price(o['total'])}\n     {icons.get(o['status'],'')}\n\n"
    await update.message.reply_text(text, parse_mode='Markdown')

async def show_offers(update, context):
    data = load_data()
    avail = [(pid, p) for pid, p in data["products"].items() if p["available"]]
    keyboard = [[InlineKeyboardButton(f"👑 {p['name']}  ·  {format_price(p['price'])}", callback_data=f"product_{pid}")] for pid, p in avail[:6]]
    await update.message.reply_text(
        "👑 *الأكثر طلباً لدى عملائنا*\n━━━━━━━━━━━━━━━━\n\n"
        "هذه المنتجات اختارها عملاؤنا قبلك...\n"
        "وننصحك بها بثقة. 👇",
        parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard) if keyboard else None
    )

async def support(update, context):
    await update.message.reply_text(
        "💬 *فريق الدعم في خدمتك*\n━━━━━━━━━━━━━━━━\n\n"
        "سؤال؟ استفسار؟ أو مجرّد اطمئنان؟\n"
        "نحن هنا من أجلك، في أي وقت.\n\n"
        "📱 تيليجرام: @h_q_k\n"
        "📧 البريد: zedanotman7@gmail.com\n"
        "⏰ متواجدون: 24 ساعة / 7 أيام\n\n"
        "_راحتك تهمّنا، فلا تتردّد._ 🤝",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📱 تواصل معنا مباشرة", url="https://t.me/h_q_k")]])
    )

async def about(update, context):
    await update.message.reply_text(
        "ℹ️ *قصّتنا معك*\n━━━━━━━━━━━━━━━━\n\n"
        "بدأنا بفكرة بسيطة: أن نوفّر لك المنتجات الرقمية الأصلية "
        "بثقة لا تتزعزع وسعرٍ يحترم جيبك.\n\n"
        "اليوم، نفخر بخدمة آلاف العملاء الذين منحونا ثقتهم.\n\n"
        "✦ أصالة مضمونة في كل منتج\n"
        "✦ استلام فوري دون انتظار\n"
        "✦ أسعار تنافسية بلا منافس\n"
        "✦ دعم لا يتوقّف ليلاً أو نهاراً\n"
        "✦ ضمان استرداد يحفظ حقّك\n\n"
        "_شكراً لأنك جزء من رحلتنا._ 🌟",
        parse_mode='Markdown'
    )

async def show_admin_orders(update, context):
    query = update.callback_query
    data = load_data()
    pending = {oid: o for oid, o in data["orders"].items() if o["status"] in ["pending", "awaiting_confirmation"]}
    if not pending:
        await query.edit_message_text("✅ *لا توجد طلبات معلقة*", parse_mode='Markdown'); return
    text = "📋 *الطلبات المعلقة*\n━━━━━━━━━━━━━━━━\n"
    keyboard = []
    for oid, o in pending.items():
        text += f"• `{oid}` @{o['username']} {format_price(o['total'])}\n"
        keyboard.append([InlineKeyboardButton(f"✅ {oid}", callback_data=f"confirm_{oid}"), InlineKeyboardButton("❌", callback_data=f"reject_{oid}")])
    await query.edit_message_text(text, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))

async def show_admin_stats(update, context):
    query = update.callback_query
    data = load_data()
    o = data["orders"]
    rev = sum(x["total"] for x in o.values() if x["status"] == "confirmed")
    text = (f"📊 *إحصائيات المتجر*\n━━━━━━━━━━━━━━━━\n📦 الطلبات: {len(o)}\n✅ مؤكدة: {sum(1 for x in o.values() if x['status']=='confirmed')}\n⏳ معلقة: {sum(1 for x in o.values() if x['status']=='pending')}\n❌ مرفوضة: {sum(1 for x in o.values() if x['status']=='rejected')}\n━━━━━━━━━━━━━━━━\n💰 الإيرادات: {format_price(rev)}")
    await query.edit_message_text(text, parse_mode='Markdown')

async def callback_handler(update, context):
    d = update.callback_query.data
    if d == "all_products": await show_all_products(update, context)
    elif d.startswith("product_"): await show_product_detail(update, context)
    elif d.startswith("add_cart_"): await add_to_cart(update, context)
    elif d.startswith("buy_now_"):
        await add_to_cart(update, context); await checkout(update, context)
    elif d == "checkout": await checkout(update, context)
    elif d.startswith("pay_"): await show_payment_info(update, context)
    elif d == "send_proof": await request_payment_proof(update, context)
    elif d.startswith("confirm_"): await confirm_order(update, context)
    elif d.startswith("reject_"): await reject_order(update, context)
    elif d == "clear_cart":
        context.user_data["cart"] = []
        await update.callback_query.answer("🗑️ تم إفراغ سلّتك", show_alert=True)
    elif d.startswith("cat_"): await show_category(update, context, d.replace("cat_", ""))
    elif d == "admin_orders": await show_admin_orders(update, context)
    elif d == "admin_stats": await show_admin_stats(update, context)
    elif d == "back_main":
        await update.callback_query.answer(); await update.callback_query.message.delete()

async def text_handler(update, context):
    t = update.message.text
    if t == "🛍️ تصفّح المتجر": await show_products(update, context)
    elif t == "🛒 سلّتي": await show_cart(update, context)
    elif t == "📦 طلباتي": await show_my_orders(update, context)
    elif t == "👑 الأكثر طلباً": await show_offers(update, context)
    elif t == "💬 الدعم الفني": await support(update, context)
    elif t == "ℹ️ من نحن": await about(update, context)

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(request_payment_proof, pattern="^send_proof$")],
        states={AWAIT_PAYMENT_PROOF: [MessageHandler(filters.PHOTO | filters.Document.ALL, receive_payment_proof)]},
        fallbacks=[CommandHandler("cancel", lambda u, c: ConversationHandler.END)]
    )
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(conv)
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    logger.info("🤖 البوت يعمل...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
