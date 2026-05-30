#!/usr/bin/env python3
"""
🛒 بوت متجر المنتجات الإلكترونية - نسخة محسّنة بمظهر إبداعي
"""

import logging
import json
import os
from datetime import datetime
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    ReplyKeyboardMarkup
)
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes, ConversationHandler
)

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

def is_admin(user_id):
    return user_id in ADMIN_IDS

def get_order_id(data):
    data["settings"]["order_counter"] = data["settings"].get("order_counter", 1000) + 1
    save_data(data)
    return f"ORD-{data['settings']['order_counter']}"

def format_price(price, currency="USD"):
    if currency == "LYD":
        return f"{price:.2f} د.ل"
    return f"${price:.2f}"

def price_in_lyd(usd_price):
    data = load_data()
    rate = data["settings"].get("usd_to_lyd", 4.85)
    return usd_price * rate

# ─── لوحات المفاتيح الجذابة ───────────────────────────────────────
def main_keyboard():
    return ReplyKeyboardMarkup([
        ["🛍️ تصفّح المنتجات", "🛒 سلّتي"],
        ["📦 طلباتي", "💎 العروض"],
        ["💬 الدعم الفني", "ℹ️ من نحن"]
    ], resize_keyboard=True, input_field_placeholder="✨ اكتب أو اختر من القائمة...")

def admin_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📦 المنتجات", callback_data="admin_products"),
         InlineKeyboardButton("📊 الإحصائيات", callback_data="admin_stats")],
        [InlineKeyboardButton("📋 الطلبات المعلقة", callback_data="admin_orders")]
    ])

# ─── البداية ─────────────────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    user = update.effective_user
    welcome = data["settings"].get("welcome_message", "مرحباً بك!")
    text = (
        f"✨━━━━━━━━━━━━━━━✨\n"
        f"      🌟 *أهلاً {user.first_name}* 🌟\n"
        f"✨━━━━━━━━━━━━━━━✨\n\n"
        f"{welcome}\n\n"
        f"┏━━━━━━━━━━━━━━━┓\n"
        f"┃ 💎 منتجات رقمية أصلية\n"
        f"┃ ⚡ تسليم فوري وآمن\n"
        f"┃ 🔒 ضمان استرداد 24 ساعة\n"
        f"┃ 💳 طرق دفع متعددة\n"
        f"┃ 🌍 دعم 24/7\n"
        f"┗━━━━━━━━━━━━━━━┛\n\n"
        f"👇 *اختر ما يناسبك من الأسفل*"
    )
    await update.message.reply_text(text, parse_mode='Markdown', reply_markup=main_keyboard())

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ ليس لديك صلاحية.")
        return
    data = load_data()
    orders = data.get("orders", {})
    pending = sum(1 for o in orders.values() if o["status"] in ["pending", "awaiting_confirmation"])
    confirmed = sum(1 for o in orders.values() if o["status"] == "confirmed")
    revenue = sum(o["total"] for o in orders.values() if o["status"] == "confirmed")
    text = (
        f"👑━━━━━━━━━━━━━━━👑\n"
        f"    *لوحة تحكم المدير*\n"
        f"👑━━━━━━━━━━━━━━━👑\n\n"
        f"📦 المنتجات: *{len(data['products'])}*\n"
        f"⏳ طلبات معلقة: *{pending}*\n"
        f"✅ طلبات مؤكدة: *{confirmed}*\n"
        f"💰 الإيرادات: *{format_price(revenue)}*\n"
        f"━━━━━━━━━━━━━━━━"
    )
    await update.message.reply_text(text, parse_mode='Markdown', reply_markup=admin_keyboard())

# ─── المنتجات ────────────────────────────────────────────────────
async def show_products(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    categories = {}
    for pid, product in data["products"].items():
        cat = product["category"]
        categories.setdefault(cat, []).append((pid, product))

    cat_emojis = {"أنظمة التشغيل": "💻", "برامج التصميم": "🎨", "العاب": "🎮", "الأمن والخصوصية": "🔒", "الأمن": "🔒", "ترفيه": "🎬"}

    keyboard = []
    for cat in categories:
        emoji = cat_emojis.get(cat, "📁")
        count = len(categories[cat])
        keyboard.append([InlineKeyboardButton(f"{emoji} {cat} ({count})", callback_data=f"cat_{cat}")])
    keyboard.append([InlineKeyboardButton("🔥 عرض جميع المنتجات", callback_data="all_products")])

    await update.message.reply_text(
        "🛍️━━━━━━━━━━━━━━━🛍️\n"
        "    *تصفّح حسب الفئة*\n"
        "🛍️━━━━━━━━━━━━━━━🛍️\n\n"
        "اختر الفئة التي تهمك 👇",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def show_all_products(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = load_data()
    keyboard = []
    for pid, product in data["products"].items():
        status = "🟢" if product["available"] else "🔴"
        keyboard.append([InlineKeyboardButton(f"{status} {product['name']} • {format_price(product['price'])}", callback_data=f"product_{pid}")])
    keyboard.append([InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="back_main")])
    await query.edit_message_text(
        "🔥━━━━━━━━━━━━━━━🔥\n"
        "    *جميع المنتجات*\n"
        "🔥━━━━━━━━━━━━━━━🔥",
        parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def show_product_detail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    pid = query.data.replace("product_", "")
    data = load_data()
    product = data["products"].get(pid)
    if not product:
        await query.answer("❌ المنتج غير موجود", show_alert=True)
        return
    status = "🟢 متوفر الآن" if product["available"] else "🔴 نفذت الكمية"
    lyd = price_in_lyd(product["price"])
    text = (
        f"╭━━━━━━━━━━━━━━━╮\n"
        f"  🏷️ *{product['name']}*\n"
        f"╰━━━━━━━━━━━━━━━╯\n\n"
        f"📝 {product['description']}\n\n"
        f"📁 الفئة: _{product['category']}_\n"
        f"📊 الحالة: {status}\n\n"
        f"💵━━━━━━━━━━━━━━━\n"
        f"  💰 السعر: *{format_price(product['price'])}*\n"
        f"  🇱🇾 بالدينار: *{format_price(lyd, 'LYD')}*\n"
        f"💵━━━━━━━━━━━━━━━"
    )
    keyboard = []
    if product["available"]:
        keyboard.append([InlineKeyboardButton("🛒 أضف إلى السلة", callback_data=f"add_cart_{pid}")])
        keyboard.append([InlineKeyboardButton("⚡ اشترِ الآن مباشرة", callback_data=f"buy_now_{pid}")])
    keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="all_products")])
    await query.edit_message_text(text, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))

async def show_category(update, context, category):
    query = update.callback_query
    await query.answer()
    data = load_data()
    products = {pid: p for pid, p in data["products"].items() if p["category"] == category}
    keyboard = []
    for pid, product in products.items():
        status = "🟢" if product["available"] else "🔴"
        keyboard.append([InlineKeyboardButton(f"{status} {product['name']} • {format_price(product['price'])}", callback_data=f"product_{pid}")])
    keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="all_products")])
    await query.edit_message_text(f"📁 *{category}*\n━━━━━━━━━━━━━━━━", parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))

# ─── السلة ───────────────────────────────────────────────────────
async def add_to_cart(update, context):
    query = update.callback_query
    pid = query.data.replace("add_cart_", "")
    data = load_data()
    product = data["products"].get(pid)
    context.user_data.setdefault("cart", [])
    context.user_data["cart"].append({"pid": pid, "name": product["name"], "price": product["price"]})
    await query.answer(f"✅ تمت إضافة {product['name']} إلى سلتك!", show_alert=True)

async def show_cart(update, context):
    cart = context.user_data.get("cart", [])
    if not cart:
        await update.message.reply_text(
            "🛒━━━━━━━━━━━━━━━🛒\n"
            "   *سلّتك فارغة حالياً*\n"
            "🛒━━━━━━━━━━━━━━━🛒\n\n"
            "ابدأ التسوّق الآن واكتشف منتجاتنا المميزة! 💎",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🛍️ تصفّح المنتجات", callback_data="all_products")]])
        )
        return
    total = sum(i["price"] for i in cart)
    total_lyd = price_in_lyd(total)
    text = "🛒━━━━━━━━━━━━━━━🛒\n    *محتويات سلّتك*\n🛒━━━━━━━━━━━━━━━🛒\n\n"
    for i, item in enumerate(cart, 1):
        text += f"  {i}️⃣ {item['name']}\n      └ {format_price(item['price'])}\n\n"
    text += (
        f"━━━━━━━━━━━━━━━━\n"
        f"💰 المجموع: *{format_price(total)}*\n"
        f"🇱🇾 بالدينار: *{format_price(total_lyd, 'LYD')}*\n"
        f"━━━━━━━━━━━━━━━━"
    )
    keyboard = [
        [InlineKeyboardButton("💳 إتمام عملية الشراء", callback_data="checkout")],
        [InlineKeyboardButton("🗑️ تفريغ السلة", callback_data="clear_cart"),
         InlineKeyboardButton("➕ متابعة التسوق", callback_data="all_products")]
    ]
    await update.message.reply_text(text, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))

# ─── الدفع ───────────────────────────────────────────────────────
async def checkout(update, context):
    query = update.callback_query
    await query.answer()
    data = load_data()
    payment = data["settings"]["payment_methods"]
    keyboard = []
    if payment.get("usdt", {}).get("enabled"):
        keyboard.append([InlineKeyboardButton("💰 USDT (TRC20)", callback_data="pay_usdt")])
    if payment.get("paypal", {}).get("enabled"):
        keyboard.append([InlineKeyboardButton("🅿️ PayPal", callback_data="pay_paypal")])
    if payment.get("binance", {}).get("enabled"):
        keyboard.append([InlineKeyboardButton("🟡 Binance Pay", callback_data="pay_binance")])
    if payment.get("libyana", {}).get("enabled"):
        keyboard.append([InlineKeyboardButton("📱 رصيد ليبيانا", callback_data="pay_libyana")])
    if payment.get("bank_transfer", {}).get("enabled"):
        keyboard.append([InlineKeyboardButton("🏦 تحويل مصرفي", callback_data="pay_bank_transfer")])
    keyboard.append([InlineKeyboardButton("🔙 رجوع للسلة", callback_data="back_cart")])
    await query.edit_message_text(
        "💳━━━━━━━━━━━━━━━💳\n"
        "  *اختر طريقة الدفع*\n"
        "💳━━━━━━━━━━━━━━━💳\n\n"
        "جميع طرق الدفع آمنة 100% 🔒",
        parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def show_payment_info(update, context):
    query = update.callback_query
    await query.answer()
    method = query.data.replace("pay_", "")
    data = load_data()
    payment = data["settings"]["payment_methods"]
    cart = context.user_data.get("cart", [])
    total = sum(i["price"] for i in cart)
    order_id = get_order_id(data)
    order = {"id": order_id, "user_id": query.from_user.id, "username": query.from_user.username or query.from_user.first_name, "items": cart, "total": total, "payment_method": method, "status": "pending", "created_at": datetime.now().isoformat(), "confirmed_at": None}
    data["orders"][order_id] = order
    save_data(data)
    context.user_data["current_order"] = order_id
    total_lyd = price_in_lyd(total)

    header = f"🧾 رقم الطلب: `{order_id}`\n💵 المبلغ: *{format_price(total)}*"

    if method == "usdt":
        p = payment["usdt"]
        text = f"💰━━━ *الدفع بـ USDT* ━━━💰\n\n{header}\n\n📡 الشبكة: {p['network']}\n📋 العنوان:\n`{p['address']}`\n\n⚠️ أرسل المبلغ بالضبط ثم أرسل لقطة الشاشة"
    elif method == "paypal":
        p = payment["paypal"]
        text = f"🅿️━━━ *الدفع بـ PayPal* ━━━🅿️\n\n{header}\n\n📧 الإيميل:\n`{p['email']}`\n\n⚠️ اكتب رقم الطلب في الملاحظة"
    elif method == "binance":
        p = payment["binance"]
        text = f"🟡━━━ *Binance Pay* ━━━🟡\n\n{header}\n\n🆔 ID:\n`{p['id']}`\n\n⚠️ أرسل لقطة الشاشة بعد الدفع"
    elif method == "libyana":
        p = payment["libyana"]
        text = f"📱━━━ *رصيد ليبيانا* ━━━📱\n\n{header}\n🇱🇾 بالدينار: *{format_price(total_lyd, 'LYD')}*\n\n📞 الرقم: `{p['number']}`\n👤 الاسم: {p['name']}\n\n⚠️ اكتب رقم الطلب `{order_id}` في التحويل"
    elif method == "bank_transfer":
        p = payment["bank_transfer"]
        text = f"🏦━━━ *تحويل مصرفي* ━━━🏦\n\n{header}\n🇱🇾 بالدينار: *{format_price(total_lyd, 'LYD')}*\n\n🏛️ المصرف: {p['bank_name']}\n👤 الحساب: {p['account_name']}\n🔢 الرقم: `{p['account_number']}`\n📋 IBAN: `{p['iban']}`\n\n⚠️ اذكر رقم الطلب `{order_id}`"
    else:
        text = "❌ طريقة غير معروفة"

    keyboard = [[InlineKeyboardButton("📸 أرسلت المبلغ - إرسال الإثبات", callback_data="send_proof")], [InlineKeyboardButton("🔙 رجوع", callback_data="checkout")]]
    await query.edit_message_text(text, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))

    labels = {"usdt": "USDT", "paypal": "PayPal", "binance": "Binance", "libyana": "📱 ليبيانا", "bank_transfer": "🏦 تحويل"}
    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_message(admin_id, f"🔔 *طلب جديد!*\n🧾 `{order_id}`\n👤 @{order['username']}\n💰 {format_price(total)}\n💳 {labels.get(method, method)}", parse_mode='Markdown')
        except:
            pass

async def request_payment_proof(update, context):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "📸━━━━━━━━━━━━━━━📸\n"
        "  *أرسل إثبات الدفع*\n"
        "📸━━━━━━━━━━━━━━━📸\n\n"
        "أرسل صورة أو لقطة شاشة لعملية الدفع 👇\n"
        "سيتم مراجعة طلبك فوراً ⏱️",
        parse_mode='Markdown'
    )
    return AWAIT_PAYMENT_PROOF

async def receive_payment_proof(update, context):
    order_id = context.user_data.get("current_order")
    data = load_data()
    if order_id and order_id in data["orders"]:
        data["orders"][order_id]["status"] = "awaiting_confirmation"
        save_data(data)
    await update.message.reply_text(
        f"✅━━━━━━━━━━━━━━━✅\n"
        f"  *تم استلام طلبك!*\n"
        f"✅━━━━━━━━━━━━━━━✅\n\n"
        f"🧾 رقم طلبك: `{order_id}`\n"
        f"⏱️ ستتم مراجعته وإرسال المنتج خلال دقائق\n\n"
        f"شكراً لثقتك بنا! 💎",
        parse_mode='Markdown', reply_markup=main_keyboard()
    )
    caption = f"📸 *إثبات دفع*\n🧾 `{order_id}`\n👤 @{update.effective_user.username or update.effective_user.first_name}"
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("✅ تأكيد", callback_data=f"confirm_{order_id}"), InlineKeyboardButton("❌ رفض", callback_data=f"reject_{order_id}")]])
    for admin_id in ADMIN_IDS:
        try:
            if update.message.photo:
                await context.bot.send_photo(admin_id, update.message.photo[-1].file_id, caption=caption, parse_mode='Markdown', reply_markup=kb)
            elif update.message.document:
                await context.bot.send_document(admin_id, update.message.document.file_id, caption=caption, parse_mode='Markdown', reply_markup=kb)
        except Exception as e:
            logger.error(f"notify admin: {e}")
    context.user_data["cart"] = []
    return ConversationHandler.END

async def confirm_order(update, context):
    query = update.callback_query
    if not is_admin(query.from_user.id):
        await query.answer("⛔", show_alert=True)
        return
    order_id = query.data.replace("confirm_", "")
    data = load_data()
    order = data["orders"].get(order_id)
    if not order:
        await query.answer("❌ غير موجود", show_alert=True)
        return
    order["status"] = "confirmed"
    order["confirmed_at"] = datetime.now().isoformat()
    save_data(data)
    await query.answer("✅ تم التأكيد!")
    try:
        await query.edit_message_caption(f"{query.message.caption}\n\n✅ *تم التأكيد*", parse_mode='Markdown')
    except:
        pass
    items = "\n".join([f"  • {i['name']}" for i in order["items"]])
    try:
        await context.bot.send_message(order["user_id"], f"🎉━━━━━━━━━━━━━━━🎉\n  *تم تأكيد طلبك!*\n🎉━━━━━━━━━━━━━━━🎉\n\n🧾 `{order_id}`\n📦 منتجاتك:\n{items}\n\n⚡ سيصلك المنتج الآن...\nشكراً لتسوقك معنا! 💎", parse_mode='Markdown')
    except Exception as e:
        logger.error(f"notify user: {e}")

async def reject_order(update, context):
    query = update.callback_query
    if not is_admin(query.from_user.id):
        await query.answer("⛔", show_alert=True)
        return
    order_id = query.data.replace("reject_", "")
    data = load_data()
    order = data["orders"].get(order_id)
    if order:
        order["status"] = "rejected"
        save_data(data)
    await query.answer("❌ تم الرفض")
    try:
        await query.edit_message_caption(f"{query.message.caption}\n\n❌ *مرفوض*", parse_mode='Markdown')
    except:
        pass
    try:
        await context.bot.send_message(order["user_id"], f"❌ عذراً، تم رفض الطلب `{order_id}`\nتواصل مع الدعم لمعرفة السبب 🙏", parse_mode='Markdown')
    except:
        pass

async def show_my_orders(update, context):
    user_id = update.effective_user.id
    data = load_data()
    orders = {oid: o for oid, o in data["orders"].items() if o["user_id"] == user_id}
    if not orders:
        await update.message.reply_text(
            "📦━━━━━━━━━━━━━━━📦\n"
            "  *لا توجد طلبات بعد*\n"
            "📦━━━━━━━━━━━━━━━📦\n\n"
            "ابدأ التسوّق الآن! 🛍️",
            parse_mode='Markdown'
        )
        return
    text = "📦━━━━━━━━━━━━━━━📦\n    *سجلّ طلباتك*\n📦━━━━━━━━━━━━━━━📦\n\n"
    icons = {"pending": "⏳", "awaiting_confirmation": "🔍", "confirmed": "✅", "rejected": "❌"}
    for oid, o in sorted(orders.items(), reverse=True)[:10]:
        icon = icons.get(o["status"], "❓")
        text += f"{icon} `{oid}` • {format_price(o['total'])}\n"
    await update.message.reply_text(text, parse_mode='Markdown')

# ─── العروض ──────────────────────────────────────────────────────
async def show_offers(update, context):
    data = load_data()
    available = [(pid, p) for pid, p in data["products"].items() if p["available"]]
    keyboard = []
    for pid, p in available[:5]:
        keyboard.append([InlineKeyboardButton(f"🔥 {p['name']} • {format_price(p['price'])}", callback_data=f"product_{pid}")])
    await update.message.reply_text(
        "💎━━━━━━━━━━━━━━━💎\n"
        "    *عروض حصرية* 🔥\n"
        "💎━━━━━━━━━━━━━━━💎\n\n"
        "أفضل منتجاتنا المتاحة الآن 👇",
        parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard) if keyboard else None
    )

# ─── الدعم ───────────────────────────────────────────────────────
async def support(update, context):
    await update.message.reply_text(
        "💬━━━━━━━━━━━━━━━💬\n"
        "    *الدعم الفني* 🌟\n"
        "💬━━━━━━━━━━━━━━━💬\n\n"
        "نحن في خدمتك على مدار الساعة!\n\n"
        "📱 تيليجرام: @h_q_k\n"
        "📧 الإيميل: zedanotman7@gmail.com\n"
        "⏰ متاحون: 24/7\n\n"
        "لا تتردد في التواصل معنا 💎",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📱 تواصل عبر تيليجرام", url="https://t.me/h_q_k")]])
    )

async def about(update, context):
    await update.message.reply_text(
        "ℹ️━━━━━━━━━━━━━━━ℹ️\n"
        "    *من نحن؟* 🏪\n"
        "ℹ️━━━━━━━━━━━━━━━ℹ️\n\n"
        "نحن متجرك الموثوق للمنتجات الرقمية 💎\n\n"
        "┏━━━━━━━━━━━━━━━┓\n"
        "┃ ⚡ تسليم فوري\n"
        "┃ 🔒 منتجات أصلية 100%\n"
        "┃ 💰 أسعار منافسة\n"
        "┃ 🌍 دعم على مدار الساعة\n"
        "┃ ✅ ضمان استرداد المال\n"
        "┗━━━━━━━━━━━━━━━┛\n\n"
        "ثقتك هي أولويتنا! 🌟",
        parse_mode='Markdown'
    )

# ─── إحصائيات المدير ─────────────────────────────────────────────
async def show_admin_orders(update, context):
    query = update.callback_query
    data = load_data()
    pending = {oid: o for oid, o in data["orders"].items() if o["status"] in ["pending", "awaiting_confirmation"]}
    if not pending:
        await query.edit_message_text("✅ *لا توجد طلبات معلقة*", parse_mode='Markdown')
        return
    text = "📋 *الطلبات المعلقة*\n━━━━━━━━━━━━━━━━\n"
    keyboard = []
    for oid, o in pending.items():
        text += f"• `{oid}` @{o['username']} {format_price(o['total'])}\n"
        keyboard.append([InlineKeyboardButton(f"✅ {oid}", callback_data=f"confirm_{oid}"), InlineKeyboardButton("❌", callback_data=f"reject_{oid}")])
    await query.edit_message_text(text, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))

async def show_admin_stats(update, context):
    query = update.callback_query
    data = load_data()
    orders = data["orders"]
    revenue = sum(o["total"] for o in orders.values() if o["status"] == "confirmed")
    text = (
        f"📊 *إحصائيات المتجر*\n━━━━━━━━━━━━━━━━\n"
        f"📦 الطلبات: {len(orders)}\n"
        f"✅ مؤكدة: {sum(1 for o in orders.values() if o['status']=='confirmed')}\n"
        f"⏳ معلقة: {sum(1 for o in orders.values() if o['status']=='pending')}\n"
        f"❌ مرفوضة: {sum(1 for o in orders.values() if o['status']=='rejected')}\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"💰 الإيرادات: {format_price(revenue)}"
    )
    await query.edit_message_text(text, parse_mode='Markdown')

# ─── المعالجات ───────────────────────────────────────────────────
async def callback_handler(update, context):
    query = update.callback_query
    d = query.data
    if d == "all_products": await show_all_products(update, context)
    elif d.startswith("product_"): await show_product_detail(update, context)
    elif d.startswith("add_cart_"): await add_to_cart(update, context)
    elif d.startswith("buy_now_"):
        await add_to_cart(update, context)
        await checkout(update, context)
    elif d == "checkout": await checkout(update, context)
    elif d.startswith("pay_"): await show_payment_info(update, context)
    elif d == "send_proof": await request_payment_proof(update, context)
    elif d.startswith("confirm_"): await confirm_order(update, context)
    elif d.startswith("reject_"): await reject_order(update, context)
    elif d == "clear_cart":
        context.user_data["cart"] = []
        await query.answer("🗑️ تم تفريغ السلة!", show_alert=True)
    elif d.startswith("cat_"): await show_category(update, context, d.replace("cat_", ""))
    elif d == "admin_orders": await show_admin_orders(update, context)
    elif d == "admin_stats": await show_admin_stats(update, context)
    elif d == "back_main":
        await query.answer()
        await query.message.delete()

async def text_handler(update, context):
    text = update.message.text
    if text == "🛍️ تصفّح المنتجات": await show_products(update, context)
    elif text == "🛒 سلّتي": await show_cart(update, context)
    elif text == "📦 طلباتي": await show_my_orders(update, context)
    elif text == "💎 العروض": await show_offers(update, context)
    elif text == "💬 الدعم الفني": await support(update, context)
    elif text == "ℹ️ من نحن": await about(update, context)

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
