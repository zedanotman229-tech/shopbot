#!/usr/bin/env python3
"""
🛒 بوت متجر المنتجات الإلكترونية
Telegram Shop Bot - Full Featured
"""

import logging
import json
import os
from datetime import datetime
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    ReplyKeyboardMarkup, KeyboardButton
)
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes, ConversationHandler
)

# ─── سعر الصرف ───────────────────────────────────────────────────
USD_TO_LYD = 4.85   # 🔑 عدّل سعر الصرف حسب السوق

# ─── إعداد السجلات ───────────────────────────────────────────────
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ─── إعدادات البوت ───────────────────────────────────────────────
BOT_TOKEN = "6977546380:AAHG36AW0faUuNjxg3Mb9HOo-sR3TmFs_Y4"          # 🔑 ضع توكن البوت هنا
ADMIN_IDS = [664958477]                     # 🔑 ضع ID المدير هنا
DATA_FILE = "shop_data.json"               # ملف قاعدة البيانات

# ─── حالات المحادثة ──────────────────────────────────────────────
AWAIT_PAYMENT_PROOF = 1
AWAIT_PRODUCT_NAME = 2
AWAIT_PRODUCT_PRICE = 3
AWAIT_PRODUCT_DESC = 4
AWAIT_ORDER_ID = 5

# ─── قاعدة البيانات المحلية ──────────────────────────────────────
def load_data():
    """تحميل البيانات من الملف"""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        "products": {
            "p1": {
                "name": "⚡ Windows 11 Pro",
                "description": "مفتاح تفعيل أصلي مدى الحياة",
                "price": 25.00,
                "currency": "USD",
                "category": "أنظمة التشغيل",
                "available": True,
                "image": "https://example.com/win11.jpg"
            },
            "p2": {
                "name": "🎨 Adobe Photoshop CC",
                "description": "اشتراك سنوي كامل الميزات",
                "price": 45.00,
                "currency": "USD",
                "category": "برامج التصميم",
                "available": True,
                "image": ""
            },
            "p3": {
                "name": "🎮 Steam Wallet 50$",
                "description": "بطاقة رصيد ستيم",
                "price": 52.00,
                "currency": "USD",
                "category": "العاب",
                "available": True,
                "image": ""
            },
            "p4": {
                "name": "🔒 NordVPN - سنة",
                "description": "اشتراك سنوي لحماية خصوصيتك",
                "price": 30.00,
                "currency": "USD",
                "category": "الأمن والخصوصية",
                "available": True,
                "image": ""
            },
            "p5": {
                "name": "🎵 Spotify Premium",
                "description": "اشتراك 3 أشهر",
                "price": 15.00,
                "currency": "USD",
                "category": "ترفيه",
                "available": True,
                "image": ""
            },
            "p6": {
                "name": "📺 Netflix Premium",
                "description": "اشتراك شهري - UHD 4K",
                "price": 20.00,
                "currency": "USD",
                "category": "ترفيه",
                "available": False,
                "image": ""
            }
        },
        "orders": {},
        "settings": {
            "payment_methods": {
                "usdt": {"enabled": True, "address": "YOUR_USDT_ADDRESS", "network": "TRC20"},
                "paypal": {"enabled": True, "email": "shop@example.com"},
                "binance": {"enabled": True, "id": "YOUR_BINANCE_ID"},
                "libyana": {"enabled": True, "number": "09XXXXXXXX", "name": "اسم صاحب الرصيد"},
                "bank_transfer": {
                    "enabled": True,
                    "bank_name": "مصرف الجمهورية",
                    "account_name": "اسم صاحب الحساب",
                    "account_number": "XXXX-XXXX-XXXX-XXXX",
                    "iban": "LY00 0000 0000 0000 0000"
                }
            },
            "welcome_message": "مرحباً بك في متجرنا الإلكتروني! 🛒",
            "order_counter": 1000
        }
    }

def save_data(data):
    """حفظ البيانات في الملف"""
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ─── دوال مساعدة ─────────────────────────────────────────────────
def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

def get_order_id(data):
    data["settings"]["order_counter"] += 1
    save_data(data)
    return f"ORD-{data['settings']['order_counter']}"

def format_price(price, currency="USD"):
    if currency == "LYD":
        return f"{price:.2f} د.ل"
    return f"{price:.2f} {currency}"

def price_in_lyd(usd_price):
    """تحويل السعر من دولار إلى دينار ليبي"""
    return usd_price * USD_TO_LYD

# ─── لوحة المفاتيح الرئيسية ──────────────────────────────────────
def main_keyboard():
    return ReplyKeyboardMarkup([
        ["🛍️ المنتجات", "🛒 سلة المشتريات"],
        ["📦 طلباتي", "💬 الدعم الفني"],
        ["ℹ️ من نحن", "⚙️ إعدادات"]
    ], resize_keyboard=True, input_field_placeholder="اختر من القائمة...")

def admin_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📦 إدارة المنتجات", callback_data="admin_products")],
        [InlineKeyboardButton("📋 الطلبات المعلقة", callback_data="admin_orders"),
         InlineKeyboardButton("✅ تأكيد دفع", callback_data="admin_confirm")],
        [InlineKeyboardButton("⚙️ الإعدادات", callback_data="admin_settings"),
         InlineKeyboardButton("📊 الإحصائيات", callback_data="admin_stats")]
    ])

# ─── أوامر البوت ─────────────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر البداية"""
    data = load_data()
    user = update.effective_user
    welcome = data["settings"]["welcome_message"]
    
    text = (
        f"👋 أهلاً وسهلاً *{user.first_name}*!\n\n"
        f"{welcome}\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "🌟 نوفر لك أفضل المنتجات الرقمية بأسعار منافسة\n"
        "⚡ تسليم فوري بعد تأكيد الدفع\n"
        "🔒 ضمان استرداد المال خلال 24 ساعة\n"
        "━━━━━━━━━━━━━━━━\n\n"
        "اختر من القائمة أدناه 👇"
    )
    
    await update.message.reply_text(
        text,
        parse_mode='Markdown',
        reply_markup=main_keyboard()
    )

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """لوحة تحكم المدير"""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ ليس لديك صلاحية للوصول إلى هذه الصفحة.")
        return
    
    data = load_data()
    orders = data.get("orders", {})
    pending = sum(1 for o in orders.values() if o["status"] == "pending")
    confirmed = sum(1 for o in orders.values() if o["status"] == "confirmed")
    
    text = (
        "🎛️ *لوحة التحكم الإدارية*\n"
        "━━━━━━━━━━━━━━━━\n"
        f"📦 المنتجات: {len(data['products'])}\n"
        f"📋 الطلبات المعلقة: {pending}\n"
        f"✅ الطلبات المؤكدة: {confirmed}\n"
        f"📊 إجمالي الطلبات: {len(orders)}\n"
        "━━━━━━━━━━━━━━━━"
    )
    
    await update.message.reply_text(
        text,
        parse_mode='Markdown',
        reply_markup=admin_keyboard()
    )

# ─── عرض المنتجات ────────────────────────────────────────────────
async def show_products(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض قائمة المنتجات"""
    data = load_data()
    products = data["products"]
    
    # تجميع الفئات
    categories = {}
    for pid, product in products.items():
        cat = product["category"]
        if cat not in categories:
            categories[cat] = []
        categories[cat].append((pid, product))
    
    keyboard = []
    for cat, items in categories.items():
        keyboard.append([InlineKeyboardButton(f"📁 {cat}", callback_data=f"cat_{cat}")])
    keyboard.append([InlineKeyboardButton("🔄 عرض الكل", callback_data="all_products")])
    
    await update.message.reply_text(
        "🛍️ *اختر الفئة*\n\nتصفح منتجاتنا حسب الفئة:",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def show_all_products(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض كل المنتجات"""
    query = update.callback_query
    await query.answer()
    
    data = load_data()
    products = data["products"]
    keyboard = []
    
    for pid, product in products.items():
        status = "✅" if product["available"] else "❌"
        keyboard.append([
            InlineKeyboardButton(
                f"{status} {product['name']} - {format_price(product['price'])}",
                callback_data=f"product_{pid}"
            )
        ])
    
    keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="back_main")])
    
    await query.edit_message_text(
        "🛍️ *جميع المنتجات*",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def show_product_detail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض تفاصيل منتج"""
    query = update.callback_query
    await query.answer()
    
    pid = query.data.replace("product_", "")
    data = load_data()
    product = data["products"].get(pid)
    
    if not product:
        await query.edit_message_text("❌ المنتج غير موجود.")
        return
    
    status = "✅ متوفر" if product["available"] else "❌ غير متوفر"
    lyd_price = price_in_lyd(product["price"])
    text = (
        f"🏷️ *{product['name']}*\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"📝 {product['description']}\n"
        f"📁 الفئة: {product['category']}\n"
        f"💰 السعر: *{format_price(product['price'])}*\n"
        f"🇱🇾 بالدينار الليبي: *{format_price(lyd_price, 'LYD')}*\n"
        f"📊 الحالة: {status}\n"
        f"━━━━━━━━━━━━━━━━"
    )
    
    keyboard = []
    if product["available"]:
        keyboard.append([InlineKeyboardButton("🛒 أضف للسلة", callback_data=f"add_cart_{pid}")])
        keyboard.append([InlineKeyboardButton("⚡ اشتري الآن", callback_data=f"buy_now_{pid}")])
    keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="all_products")])
    
    await query.edit_message_text(
        text,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ─── السلة ───────────────────────────────────────────────────────
async def add_to_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إضافة للسلة"""
    query = update.callback_query
    await query.answer("✅ تمت الإضافة للسلة!")
    
    pid = query.data.replace("add_cart_", "")
    data = load_data()
    product = data["products"].get(pid)
    
    if not context.user_data.get("cart"):
        context.user_data["cart"] = []
    
    context.user_data["cart"].append({
        "pid": pid,
        "name": product["name"],
        "price": product["price"]
    })
    
    await query.answer(f"✅ تمت إضافة {product['name']} للسلة!", show_alert=True)

async def show_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض السلة"""
    cart = context.user_data.get("cart", [])
    
    if not cart:
        await update.message.reply_text(
            "🛒 *السلة فارغة*\n\nتفضل بتصفح المنتجات وأضف ما يعجبك!",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🛍️ تصفح المنتجات", callback_data="all_products")]
            ])
        )
        return
    
    total = sum(item["price"] for item in cart)
    total_lyd = price_in_lyd(total)
    text = "🛒 *محتويات السلة*\n━━━━━━━━━━━━━━━━\n"
    
    for i, item in enumerate(cart, 1):
        text += f"{i}. {item['name']} - {format_price(item['price'])}\n"
    
    text += (
        f"━━━━━━━━━━━━━━━━\n"
        f"💰 *المجموع: {format_price(total)}*\n"
        f"🇱🇾 *بالدينار: {format_price(total_lyd, 'LYD')}*"
    )
    
    keyboard = [
        [InlineKeyboardButton("💳 إتمام الشراء", callback_data="checkout")],
        [InlineKeyboardButton("🗑️ تفريغ السلة", callback_data="clear_cart")],
        [InlineKeyboardButton("🛍️ متابعة التسوق", callback_data="all_products")]
    ]
    
    await update.message.reply_text(
        text,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ─── الدفع ───────────────────────────────────────────────────────
async def checkout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إتمام الشراء"""
    query = update.callback_query
    await query.answer()
    
    data = load_data()
    settings = data["settings"]
    payment = settings["payment_methods"]
    
    keyboard = []
    if payment["usdt"]["enabled"]:
        keyboard.append([InlineKeyboardButton("💰 USDT (TRC20)", callback_data="pay_usdt")])
    if payment["paypal"]["enabled"]:
        keyboard.append([InlineKeyboardButton("🅿️ PayPal", callback_data="pay_paypal")])
    if payment["binance"]["enabled"]:
        keyboard.append([InlineKeyboardButton("🟡 Binance Pay", callback_data="pay_binance")])
    if payment.get("libyana", {}).get("enabled"):
        keyboard.append([InlineKeyboardButton("📱 رصيد ليبيانا", callback_data="pay_libyana")])
    if payment.get("bank_transfer", {}).get("enabled"):
        keyboard.append([InlineKeyboardButton("🏦 تحويل مصرفي", callback_data="pay_bank_transfer")])
    keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="back_cart")])
    
    await query.edit_message_text(
        "💳 *اختر طريقة الدفع*\n\nنقبل الطرق التالية:",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def show_payment_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض معلومات الدفع"""
    query = update.callback_query
    await query.answer()
    
    method = query.data.replace("pay_", "")
    data = load_data()
    payment = data["settings"]["payment_methods"]
    cart = context.user_data.get("cart", [])
    total = sum(item["price"] for item in cart)
    
    # إنشاء الطلب
    order_id = get_order_id(data)
    order = {
        "id": order_id,
        "user_id": query.from_user.id,
        "username": query.from_user.username or query.from_user.first_name,
        "items": cart,
        "total": total,
        "payment_method": method,
        "status": "pending",
        "created_at": datetime.now().isoformat(),
        "confirmed_at": None
    }
    
    data["orders"][order_id] = order
    save_data(data)
    context.user_data["current_order"] = order_id
    
    if method == "usdt":
        pay_info = payment["usdt"]
        text = (
            f"💰 *الدفع بـ USDT*\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"🔢 رقم الطلب: `{order_id}`\n"
            f"💵 المبلغ: *{format_price(total)}*\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"📱 الشبكة: {pay_info['network']}\n"
            f"📋 العنوان:\n`{pay_info['address']}`\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"⚠️ *مهم:* أرسل المبلغ بالضبط ثم أرسل لقطة الشاشة"
        )
    elif method == "paypal":
        pay_info = payment["paypal"]
        text = (
            f"🅿️ *الدفع بـ PayPal*\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"🔢 رقم الطلب: `{order_id}`\n"
            f"💵 المبلغ: *{format_price(total)}*\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"📧 الإيميل: `{pay_info['email']}`\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"⚠️ *مهم:* اكتب رقم الطلب في ملاحظة الدفع"
        )
    elif method == "binance":
        pay_info = payment["binance"]
        text = (
            f"🟡 *الدفع بـ Binance Pay*\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"🔢 رقم الطلب: `{order_id}`\n"
            f"💵 المبلغ: *{format_price(total)}*\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"🆔 Binance ID: `{pay_info['id']}`\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"⚠️ *مهم:* أرسل لقطة الشاشة للتأكيد"
        )
    elif method == "libyana":
        pay_info = payment["libyana"]
        total_lyd = price_in_lyd(total)
        text = (
            f"📱 *الدفع برصيد ليبيانا*\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"🔢 رقم الطلب: `{order_id}`\n"
            f"💵 المبلغ: *{format_price(total)}*\n"
            f"🇱🇾 بالدينار الليبي: *{format_price(total_lyd, 'LYD')}*\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"📞 رقم ليبيانا: `{pay_info['number']}`\n"
            f"👤 الاسم: {pay_info['name']}\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"⚠️ *مهم:* أرسل المبلغ بالدينار الليبي ثم أرسل لقطة الشاشة\n"
            f"📌 اكتب رقم الطلب `{order_id}` في رسالة التحويل"
        )
    elif method == "bank_transfer":
        pay_info = payment["bank_transfer"]
        total_lyd = price_in_lyd(total)
        text = (
            f"🏦 *التحويل المصرفي*\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"🔢 رقم الطلب: `{order_id}`\n"
            f"💵 المبلغ: *{format_price(total)}*\n"
            f"🇱🇾 بالدينار الليبي: *{format_price(total_lyd, 'LYD')}*\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"🏛️ المصرف: {pay_info['bank_name']}\n"
            f"👤 اسم الحساب: {pay_info['account_name']}\n"
            f"🔢 رقم الحساب: `{pay_info['account_number']}`\n"
            f"📋 IBAN: `{pay_info['iban']}`\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"⚠️ *مهم:* حوّل المبلغ بالدينار الليبي وأرسل إيصال التحويل\n"
            f"📌 اذكر رقم الطلب `{order_id}` في بيان التحويل"
        )
    else:
        text = "❌ طريقة دفع غير معروفة."
    
    keyboard = [
        [InlineKeyboardButton("📸 أرسل إثبات الدفع", callback_data="send_proof")],
        [InlineKeyboardButton("🔙 رجوع", callback_data="checkout")]
    ]
    
    await query.edit_message_text(
        text,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
    # إشعار المدير
    method_labels = {
        "usdt": "USDT", "paypal": "PayPal", "binance": "Binance Pay",
        "libyana": "📱 رصيد ليبيانا", "bank_transfer": "🏦 تحويل مصرفي"
    }
    lyd_note = ""
    if method in ("libyana", "bank_transfer"):
        lyd_note = f"\n🇱🇾 المبلغ بالدينار: {format_price(price_in_lyd(total), 'LYD')}"
    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_message(
                admin_id,
                f"🔔 *طلب جديد!*\n"
                f"━━━━━━━━━━━━━━━━\n"
                f"📋 رقم الطلب: `{order_id}`\n"
                f"👤 المستخدم: @{order['username']}\n"
                f"💰 المبلغ: {format_price(total)}{lyd_note}\n"
                f"💳 طريقة الدفع: {method_labels.get(method, method)}\n"
                f"━━━━━━━━━━━━━━━━",
                parse_mode='Markdown'
            )
        except:
            pass

async def request_payment_proof(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """طلب إثبات الدفع"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "📸 *أرسل إثبات الدفع*\n\n"
        "يرجى إرسال صورة/لقطة شاشة لإثبات عملية الدفع.\n"
        "سيتم مراجعتها وتأكيد طلبك خلال دقائق. ⏱️",
        parse_mode='Markdown'
    )
    
    return AWAIT_PAYMENT_PROOF

async def receive_payment_proof(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """استلام إثبات الدفع"""
    order_id = context.user_data.get("current_order")
    data = load_data()
    
    if order_id and order_id in data["orders"]:
        data["orders"][order_id]["proof_received"] = True
        data["orders"][order_id]["status"] = "awaiting_confirmation"
        save_data(data)
    
    await update.message.reply_text(
        "✅ *تم استلام إثبات الدفع!*\n\n"
        f"📋 رقم طلبك: `{order_id}`\n"
        "⏱️ سيتم مراجعة طلبك وإرسال المنتج خلال دقائق.\n\n"
        "شكراً لثقتك بنا! 🙏",
        parse_mode='Markdown',
        reply_markup=main_keyboard()
    )
    
    # إرسال للمدير مع الصورة
    caption = (
        f"📸 *إثبات دفع جديد!*\n"
        f"📋 رقم الطلب: `{order_id}`\n"
        f"👤 @{update.effective_user.username or update.effective_user.first_name}"
    )
    
    for admin_id in ADMIN_IDS:
        try:
            if update.message.photo:
                await context.bot.send_photo(
                    admin_id,
                    update.message.photo[-1].file_id,
                    caption=caption,
                    parse_mode='Markdown',
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("✅ تأكيد الطلب", callback_data=f"confirm_{order_id}")],
                        [InlineKeyboardButton("❌ رفض الطلب", callback_data=f"reject_{order_id}")]
                    ])
                )
            elif update.message.document:
                await context.bot.send_document(
                    admin_id,
                    update.message.document.file_id,
                    caption=caption,
                    parse_mode='Markdown',
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("✅ تأكيد الطلب", callback_data=f"confirm_{order_id}")],
                        [InlineKeyboardButton("❌ رفض الطلب", callback_data=f"reject_{order_id}")]
                    ])
                )
        except Exception as e:
            logger.error(f"Failed to notify admin: {e}")
    
    context.user_data["cart"] = []
    return ConversationHandler.END

# ─── تأكيد/رفض الطلبات (للمدير) ─────────────────────────────────
async def confirm_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تأكيد الطلب"""
    query = update.callback_query
    
    if not is_admin(query.from_user.id):
        await query.answer("⛔ ليس لديك صلاحية!", show_alert=True)
        return
    
    order_id = query.data.replace("confirm_", "")
    data = load_data()
    order = data["orders"].get(order_id)
    
    if not order:
        await query.answer("❌ الطلب غير موجود!", show_alert=True)
        return
    
    order["status"] = "confirmed"
    order["confirmed_at"] = datetime.now().isoformat()
    order["confirmed_by"] = query.from_user.id
    save_data(data)
    
    await query.answer("✅ تم تأكيد الطلب!")
    await query.edit_message_caption(
        f"{query.message.caption}\n\n✅ *تم التأكيد بواسطة @{query.from_user.username}*",
        parse_mode='Markdown'
    )
    
    # إشعار العميل
    items_text = "\n".join([f"• {i['name']}" for i in order["items"]])
    try:
        await context.bot.send_message(
            order["user_id"],
            f"🎉 *تم تأكيد طلبك!*\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"📋 رقم الطلب: `{order_id}`\n"
            f"📦 المنتجات:\n{items_text}\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"⚡ سيتم إرسال المنتج إليك الآن...\n"
            f"شكراً لتسوقك معنا! 🙏",
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Failed to notify user: {e}")

async def reject_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """رفض الطلب"""
    query = update.callback_query
    
    if not is_admin(query.from_user.id):
        await query.answer("⛔ ليس لديك صلاحية!", show_alert=True)
        return
    
    order_id = query.data.replace("reject_", "")
    data = load_data()
    order = data["orders"].get(order_id)
    
    if order:
        order["status"] = "rejected"
        save_data(data)
    
    await query.answer("❌ تم رفض الطلب!")
    await query.edit_message_caption(
        f"{query.message.caption}\n\n❌ *تم الرفض*",
        parse_mode='Markdown'
    )
    
    try:
        await context.bot.send_message(
            order["user_id"],
            f"❌ *عذراً، تم رفض طلبك*\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"📋 رقم الطلب: `{order_id}`\n\n"
            f"يرجى التواصل مع الدعم الفني لمعرفة السبب.\n"
            f"نعتذر عن الإزعاج 🙏",
            parse_mode='Markdown'
        )
    except:
        pass

# ─── عرض الطلبات ─────────────────────────────────────────────────
async def show_my_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض طلبات المستخدم"""
    user_id = update.effective_user.id
    data = load_data()
    
    user_orders = {
        oid: o for oid, o in data["orders"].items()
        if o["user_id"] == user_id
    }
    
    if not user_orders:
        await update.message.reply_text(
            "📦 *لا توجد طلبات*\n\nلم تقم بأي طلبات بعد.",
            parse_mode='Markdown'
        )
        return
    
    text = "📦 *طلباتي*\n━━━━━━━━━━━━━━━━\n"
    status_icons = {
        "pending": "⏳",
        "awaiting_confirmation": "🔍",
        "confirmed": "✅",
        "rejected": "❌",
        "delivered": "📬"
    }
    
    for oid, order in sorted(user_orders.items(), reverse=True)[:10]:
        icon = status_icons.get(order["status"], "❓")
        text += f"{icon} `{oid}` - {format_price(order['total'])}\n"
    
    await update.message.reply_text(text, parse_mode='Markdown')

# ─── الدعم الفني ─────────────────────────────────────────────────
async def support(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """الدعم الفني"""
    await update.message.reply_text(
        "💬 *الدعم الفني*\n"
        "━━━━━━━━━━━━━━━━\n"
        "نحن هنا لمساعدتك!\n\n"
        "📧 الإيميل: support@shop.com\n"
        "⏰ ساعات العمل: 24/7\n"
        "━━━━━━━━━━━━━━━━\n"
        "يمكنك مراسلتنا مباشرة وسنرد في أقرب وقت.",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📞 تواصل معنا", url="https://t.me/yoursupport")]
        ])
    )

# ─── Callback Handler الرئيسي ────────────────────────────────────
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج الضغطات"""
    query = update.callback_query
    data_key = query.data
    
    if data_key == "all_products":
        await show_all_products(update, context)
    elif data_key.startswith("product_"):
        await show_product_detail(update, context)
    elif data_key.startswith("add_cart_"):
        await add_to_cart(update, context)
    elif data_key == "checkout":
        await checkout(update, context)
    elif data_key.startswith("pay_"):
        await show_payment_info(update, context)
    elif data_key == "send_proof":
        await request_payment_proof(update, context)
    elif data_key.startswith("confirm_"):
        await confirm_order(update, context)
    elif data_key.startswith("reject_"):
        await reject_order(update, context)
    elif data_key == "clear_cart":
        context.user_data["cart"] = []
        await query.answer("🗑️ تم تفريغ السلة!", show_alert=True)
    elif data_key.startswith("cat_"):
        cat = data_key.replace("cat_", "")
        await show_category(update, context, cat)
    elif data_key == "admin_orders":
        await show_admin_orders(update, context)
    elif data_key == "admin_stats":
        await show_admin_stats(update, context)

async def show_category(update: Update, context: ContextTypes.DEFAULT_TYPE, category: str):
    """عرض منتجات فئة"""
    query = update.callback_query
    data = load_data()
    
    products = {
        pid: p for pid, p in data["products"].items()
        if p["category"] == category
    }
    
    keyboard = []
    for pid, product in products.items():
        status = "✅" if product["available"] else "❌"
        keyboard.append([
            InlineKeyboardButton(
                f"{status} {product['name']} - {format_price(product['price'])}",
                callback_data=f"product_{pid}"
            )
        ])
    keyboard.append([InlineKeyboardButton("🔙 رجوع", callback_data="all_products")])
    
    await query.edit_message_text(
        f"📁 *{category}*",
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def show_admin_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض الطلبات للمدير"""
    query = update.callback_query
    data = load_data()
    
    pending_orders = {
        oid: o for oid, o in data["orders"].items()
        if o["status"] in ["pending", "awaiting_confirmation"]
    }
    
    if not pending_orders:
        await query.edit_message_text(
            "📋 *لا توجد طلبات معلقة* ✅",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 رجوع", callback_data="back_admin")]
            ])
        )
        return
    
    text = "📋 *الطلبات المعلقة*\n━━━━━━━━━━━━━━━━\n"
    keyboard = []
    
    for oid, order in pending_orders.items():
        text += f"• `{oid}` - @{order['username']} - {format_price(order['total'])}\n"
        keyboard.append([
            InlineKeyboardButton(f"✅ تأكيد {oid}", callback_data=f"confirm_{oid}"),
            InlineKeyboardButton(f"❌ رفض", callback_data=f"reject_{oid}")
        ])
    
    await query.edit_message_text(
        text,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def show_admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إحصائيات المتجر"""
    query = update.callback_query
    data = load_data()
    orders = data["orders"]
    
    total_revenue = sum(
        o["total"] for o in orders.values()
        if o["status"] == "confirmed"
    )
    
    text = (
        f"📊 *إحصائيات المتجر*\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"📦 إجمالي الطلبات: {len(orders)}\n"
        f"✅ مؤكدة: {sum(1 for o in orders.values() if o['status'] == 'confirmed')}\n"
        f"⏳ معلقة: {sum(1 for o in orders.values() if o['status'] == 'pending')}\n"
        f"❌ مرفوضة: {sum(1 for o in orders.values() if o['status'] == 'rejected')}\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"💰 إجمالي الإيرادات: {format_price(total_revenue)}\n"
        f"━━━━━━━━━━━━━━━━"
    )
    
    await query.edit_message_text(
        text,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 رجوع", callback_data="back_admin")]
        ])
    )

# ─── معالج الرسائل النصية ────────────────────────────────────────
async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    if text == "🛍️ المنتجات":
        await show_products(update, context)
    elif text == "🛒 سلة المشتريات":
        await show_cart(update, context)
    elif text == "📦 طلباتي":
        await show_my_orders(update, context)
    elif text == "💬 الدعم الفني":
        await support(update, context)
    elif text == "ℹ️ من نحن":
        await update.message.reply_text(
            "🏪 *متجرنا الإلكتروني*\n\n"
            "نحن متجر متخصص في بيع المنتجات الرقمية والبرمجيات.\n"
            "تسليم فوري • ضمان أصالة المنتج • دعم على مدار الساعة",
            parse_mode='Markdown'
        )

# ─── تشغيل البوت ─────────────────────────────────────────────────
def main():
    """تشغيل البوت"""
    app = Application.builder().token(BOT_TOKEN).build()
    
    # ConversationHandler لإثبات الدفع
    payment_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(request_payment_proof, pattern="^send_proof$")],
        states={
            AWAIT_PAYMENT_PROOF: [
                MessageHandler(filters.PHOTO | filters.Document.ALL, receive_payment_proof)
            ]
        },
        fallbacks=[CommandHandler("cancel", lambda u, c: ConversationHandler.END)]
    )
    
    # تسجيل الأوامر
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(payment_conv)
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    
    logger.info("🤖 البوت يعمل...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
