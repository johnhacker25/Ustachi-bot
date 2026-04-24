import logging
import json
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import (
Application, CommandHandler, CallbackQueryHandler,
MessageHandler, filters, ContextTypes, ConversationHandler
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ===================== CONFIG =====================

BOT_TOKEN = "8714552724:AAHp2Hq3X97KC54O4Af9Cb7faxYEs2tyAgo"  # @BotFather dan oling
ADMIN_IDS = [1325754041]  # Sizning Telegram ID ingiz (https://t.me/userinfobot dan oling)
DATA_FILE = "data.json"

# ===================== STATES =====================

WAIT_CATEGORY_NAME, WAIT_PHOTO, WAIT_ITEM_NAME, WAIT_ITEM_DESC = range(4)
WAIT_EDIT_NAME, WAIT_EDIT_DESC, WAIT_EDIT_PHOTO = range(4, 7)
WAIT_DELETE_CONFIRM = 7

# ===================== DATA =====================

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    # Default kategoriyalar
    default = {
        "categories": {
            "mebellar": {"name": "🪑 Mebellar", "items": []},
            "zina": {"name": "🪜 Zina", "items": []},
            "parket": {"name": "🪵 Parket", "items": []},
            "dekor": {"name": "🎨 Dekor", "items": []},
            "patalok": {"name": "✨ Patalok (Shift)", "items": []}
        }
    }
    save_data(default)
    return default

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ===================== HELPERS =====================

def is_admin(user_id):
    return user_id in ADMIN_IDS

def main_menu_keyboard(user_id):
    data = load_data()
    buttons = []
    cats = list(data["categories"].items())
    # 2 tadan qator
    for i in range(0, len(cats), 2):
        row = []
        for key, val in cats[i:i+2]:
            row.append(InlineKeyboardButton(val["name"], callback_data=f"cat_{key}"))
        buttons.append(row)
    if is_admin(user_id):
        buttons.append([InlineKeyboardButton("⚙️ Admin Panel", callback_data="admin_panel")])
    return InlineKeyboardMarkup(buttons)

def category_keyboard(cat_key, items, page=0):
    data = load_data()
    cat_name = data["categories"][cat_key]["name"]
    PAGE_SIZE = 5
    start = page * PAGE_SIZE
    end = start + PAGE_SIZE
    page_items = items[start:end]

    buttons = []
    for i, item in enumerate(page_items):
        idx = start + i
        buttons.append([InlineKeyboardButton(
            f"📸 {item['name']}", callback_data=f"item_{cat_key}_{idx}"
        )])

    # Pagination
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("⬅️ Oldingi", callback_data=f"page_{cat_key}_{page-1}"))
    if end < len(items):
        nav.append(InlineKeyboardButton("Keyingi ➡️", callback_data=f"page_{cat_key}_{page+1}"))
    if nav:
        buttons.append(nav)

    buttons.append([InlineKeyboardButton("🏠 Bosh menyu", callback_data="main_menu")])
    return InlineKeyboardMarkup(buttons)

# ===================== HANDLERS =====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = (
        f"👷 Salom, {user.first_name}!\n\n"
        "🏗 *Ustachi Bot*ga xush kelibsiz!\n"
        "Quyidagi bo'limlardan birini tanlang:"
    )
    await update.message.reply_text(
        text,
        parse_mode="Markdown",
        reply_markup=main_menu_keyboard(user.id)
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data_str = query.data
    user_id = query.from_user.id
    db = load_data()

    # --- MAIN MENU ---
    if data_str == "main_menu":
        await query.edit_message_text(
            "🏗 *Ustachi Bot* - Bosh menyu\nBo'limni tanlang:",
            parse_mode="Markdown",
            reply_markup=main_menu_keyboard(user_id)
        )

    # --- CATEGORY ---
    elif data_str.startswith("cat_"):
        cat_key = data_str[4:]
        if cat_key not in db["categories"]:
            await query.edit_message_text("❌ Kategoriya topilmadi")
            return
        cat = db["categories"][cat_key]
        items = cat["items"]
        if not items:
            await query.edit_message_text(
                f"{cat['name']}\n\n📭 Hozircha ma'lumot yo'q.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🏠 Bosh menyu", callback_data="main_menu")
                ]])
            )
            return
        await query.edit_message_text(
            f"{cat['name']}\n\n📋 Quyidagi mahsulotlardan birini tanlang:",
            reply_markup=category_keyboard(cat_key, items, 0)
        )

    # --- PAGINATION ---
    elif data_str.startswith("page_"):
        parts = data_str.split("_")
        cat_key = parts[1]
        page = int(parts[2])
        items = db["categories"][cat_key]["items"]
        await query.edit_message_text(
            f"{db['categories'][cat_key]['name']}\n\n📋 Mahsulotni tanlang:",
            reply_markup=category_keyboard(cat_key, items, page)
        )

    # --- ITEM DETAIL ---
    elif data_str.startswith("item_"):
        parts = data_str.split("_", 2)
        cat_key = parts[1]
        idx = int(parts[2])
        item = db["categories"][cat_key]["items"][idx]
        caption = f"*{item['name']}*\n\n{item.get('description', '')}"

        back_btn = InlineKeyboardMarkup([[
            InlineKeyboardButton("⬅️ Orqaga", callback_data=f"cat_{cat_key}"),
            InlineKeyboardButton("🏠 Menyu", callback_data="main_menu")
        ]])

        if item.get("photo_id"):
            try:
                await query.message.reply_photo(
                    photo=item["photo_id"],
                    caption=caption,
                    parse_mode="Markdown",
                    reply_markup=back_btn
                )
                await query.message.delete()
            except:
                await query.edit_message_text(caption, parse_mode="Markdown", reply_markup=back_btn)
        else:
            await query.edit_message_text(caption, parse_mode="Markdown", reply_markup=back_btn)

    # --- ADMIN PANEL ---
    elif data_str == "admin_panel":
        if not is_admin(user_id):
            await query.edit_message_text("❌ Ruxsat yo'q!")
            return
        await show_admin_panel(query, db)

    # --- ADMIN: ADD ITEM ---
    elif data_str.startswith("admin_add_"):
        if not is_admin(user_id): return
        cat_key = data_str[10:]
        context.user_data["add_cat"] = cat_key
        context.user_data["state"] = "wait_name"
        await query.edit_message_text(
            f"✏️ *{db['categories'][cat_key]['name']}* ga yangi mahsulot qo'shish\n\n"
            "Mahsulot nomini kiriting:",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("❌ Bekor", callback_data="admin_panel")
            ]])
        )

    # --- ADMIN: LIST ITEMS for delete/edit ---
    elif data_str.startswith("admin_list_"):
        if not is_admin(user_id): return
        action, cat_key = data_str[11:].split("_", 1)
        items = db["categories"][cat_key]["items"]
        if not items:
            await query.edit_message_text(
                "📭 Bu kategoriyada mahsulot yo'q.",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("⬅️ Orqaga", callback_data="admin_panel")
                ]])
            )
            return
        buttons = []
        for i, item in enumerate(items):
            buttons.append([InlineKeyboardButton(
                f"{'🗑' if action=='del' else '✏️'} {item['name']}",
                callback_data=f"admin_{action}item_{cat_key}_{i}"
            )])
        buttons.append([InlineKeyboardButton("⬅️ Orqaga", callback_data="admin_panel")])
        await query.edit_message_text(
            f"{'O\'chirish' if action=='del' else 'Tahrirlash'} uchun mahsulotni tanlang:",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    # --- ADMIN: DELETE ITEM ---
    elif data_str.startswith("admin_delitem_"):
        if not is_admin(user_id): return
        parts = data_str[14:].split("_", 1)
        cat_key = parts[0]
        idx = int(parts[1])
        item_name = db["categories"][cat_key]["items"][idx]["name"]
        context.user_data["del_cat"] = cat_key
        context.user_data["del_idx"] = idx
        await query.edit_message_text(
            f"🗑 *{item_name}* ni o'chirishni tasdiqlaysizmi?",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Ha, o'chir", callback_data="confirm_delete"),
                 InlineKeyboardButton("❌ Yo'q", callback_data="admin_panel")]
            ])
        )

    elif data_str == "confirm_delete":
        if not is_admin(user_id): return
        cat_key = context.user_data.get("del_cat")
        idx = context.user_data.get("del_idx")
        if cat_key and idx is not None:
            db["categories"][cat_key]["items"].pop(idx)
            save_data(db)
            await query.edit_message_text("✅ Mahsulot o'chirildi!")
        await show_admin_panel(query, db)

    # --- ADMIN: EDIT ITEM ---
    elif data_str.startswith("admin_edititem_"):
        if not is_admin(user_id): return
        parts = data_str[15:].split("_", 1)
        cat_key = parts[0]
        idx = int(parts[1])
        item = db["categories"][cat_key]["items"][idx]
        context.user_data["edit_cat"] = cat_key
        context.user_data["edit_idx"] = idx
        context.user_data["state"] = "edit_menu"
        await query.edit_message_text(
            f"✏️ *{item['name']}* ni tahrirlash\n\nNimani o'zgartirmoqchisiz?",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📝 Nom", callback_data="edit_name"),
                 InlineKeyboardButton("📄 Tavsif", callback_data="edit_desc")],
                [InlineKeyboardButton("🖼 Rasm", callback_data="edit_photo")],
                [InlineKeyboardButton("⬅️ Orqaga", callback_data="admin_panel")]
            ])
        )

    elif data_str in ["edit_name", "edit_desc", "edit_photo"]:
        if not is_admin(user_id): return
        prompts = {
            "edit_name": ("edit_name", "Yangi nomni kiriting:"),
            "edit_desc": ("edit_desc", "Yangi tavsifni kiriting:"),
            "edit_photo": ("edit_photo", "Yangi rasmni yuboring:"),
        }
        state, msg = prompts[data_str]
        context.user_data["state"] = state
        await query.edit_message_text(
            msg,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("❌ Bekor", callback_data="admin_panel")
            ]])
        )

async def show_admin_panel(query, db):
    buttons = []
    for key, val in db["categories"].items():
        count = len(val["items"])
        buttons.append([
            InlineKeyboardButton(f"➕ {val['name']} ({count})", callback_data=f"admin_add_{key}"),
            InlineKeyboardButton("✏️", callback_data=f"admin_list_edit_{key}"),
            InlineKeyboardButton("🗑", callback_data=f"admin_list_del_{key}"),
        ])
    buttons.append([InlineKeyboardButton("🏠 Bosh menyu", callback_data="main_menu")])
    await query.edit_message_text(
        "⚙️ *Admin Panel*\n\n"
        "➕ = Qo'shish | ✏️ = Tahrirlash | 🗑 = O'chirish",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        return

    state = context.user_data.get("state")
    db = load_data()

    # === ADD: wait name ===
    if state == "wait_name":
        context.user_data["new_name"] = update.message.text
        context.user_data["state"] = "wait_desc"
        await update.message.reply_text(
            "📄 Tavsif kiriting (yoki /skip bosing):",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("⏭ O'tkazib yuborish", callback_data="skip_desc")
            ]])
        )

    elif state == "wait_desc":
        context.user_data["new_desc"] = update.message.text
        context.user_data["state"] = "wait_photo"
        await update.message.reply_text("🖼 Rasm yuboring (yoki o'tkazib yuboring):",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("⏭ Rasmsiz saqlash", callback_data="skip_photo")
            ]])
        )

    elif state == "wait_photo":
        if update.message.photo:
            photo_id = update.message.photo[-1].file_id
            context.user_data["new_photo"] = photo_id
            await save_new_item(update, context, db)
        else:
            await update.message.reply_text("❗ Iltimos rasm yuboring yoki 'O'tkazib yuborish' ni bosing.")

    # === EDIT ===
    elif state == "edit_name":
        cat_key = context.user_data["edit_cat"]
        idx = context.user_data["edit_idx"]
        db["categories"][cat_key]["items"][idx]["name"] = update.message.text
        save_data(db)
        context.user_data["state"] = None
        await update.message.reply_text("✅ Nom yangilandi!", reply_markup=main_menu_keyboard(user_id))

    elif state == "edit_desc":
        cat_key = context.user_data["edit_cat"]
        idx = context.user_data["edit_idx"]
        db["categories"][cat_key]["items"][idx]["description"] = update.message.text
        save_data(db)
        context.user_data["state"] = None
        await update.message.reply_text("✅ Tavsif yangilandi!", reply_markup=main_menu_keyboard(user_id))

    elif state == "edit_photo":
        if update.message.photo:
            cat_key = context.user_data["edit_cat"]
            idx = context.user_data["edit_idx"]
            db["categories"][cat_key]["items"][idx]["photo_id"] = update.message.photo[-1].file_id
            save_data(db)
            context.user_data["state"] = None
            await update.message.reply_text("✅ Rasm yangilandi!", reply_markup=main_menu_keyboard(user_id))
        else:
            await update.message.reply_text("❗ Iltimos rasm yuboring.")

async def skip_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    state = context.user_data.get("state")
    db = load_data()

    if state == "wait_desc":
        context.user_data["new_desc"] = ""
        context.user_data["state"] = "wait_photo"
        await query.edit_message_text("🖼 Rasm yuboring (yoki o'tkazib yuboring):",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("⏭ Rasmsiz saqlash", callback_data="skip_photo")
            ]])
        )
    elif state == "wait_photo":
        context.user_data["new_photo"] = None
        await save_new_item_query(query, context, db)

async def save_new_item(update, context, db):
    cat_key = context.user_data["add_cat"]
    item = {
        "name": context.user_data.get("new_name", "Noma'lum"),
        "description": context.user_data.get("new_desc", ""),
        "photo_id": context.user_data.get("new_photo"),
    }
    db["categories"][cat_key]["items"].append(item)
    save_data(db)
    context.user_data["state"] = None
    await update.message.reply_text(
        f"✅ *{item['name']}* qo'shildi!",
        parse_mode="Markdown",
        reply_markup=main_menu_keyboard(update.effective_user.id)
    )

async def save_new_item_query(query, context, db):
    cat_key = context.user_data["add_cat"]
    item = {
        "name": context.user_data.get("new_name", "Noma'lum"),
        "description": context.user_data.get("new_desc", ""),
        "photo_id": context.user_data.get("new_photo"),
    }
    db["categories"][cat_key]["items"].append(item)
    save_data(db)
    context.user_data["state"] = None
    await query.edit_message_text(f"✅ *{item['name']}* qo'shildi!", parse_mode="Markdown")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(skip_handler, pattern="^skip_"))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, message_handler))
    print("🤖 Bot ishga tushdi!")
    app.run_polling()

if __name__ == "__main__":
    main()
