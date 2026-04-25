import logging
import json
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(**name**)

BOT_TOKEN = “8714552724:AAHp2Hq3X97KC54O4Af9Cb7faxYEs2tyAgo”
ADMIN_IDS = [1325754041]
DATA_FILE = “data.json”

def load_data():
if os.path.exists(DATA_FILE):
with open(DATA_FILE, “r”, encoding=“utf-8”) as f:
return json.load(f)
default = {
“categories”: {
“mebellar”: {“name”: “Mebellar”, “items”: []},
“zina”: {“name”: “Zina”, “items”: []},
“parket”: {“name”: “Parket”, “items”: []},
“dekor”: {“name”: “Dekor”, “items”: []},
“patalok”: {“name”: “Patalok (Shift)”, “items”: []}
}
}
save_data(default)
return default

def save_data(data):
with open(DATA_FILE, “w”, encoding=“utf-8”) as f:
json.dump(data, f, ensure_ascii=False, indent=2)

def is_admin(user_id):
return user_id in ADMIN_IDS

def main_menu_keyboard(user_id):
data = load_data()
buttons = []
cats = list(data[“categories”].items())
for i in range(0, len(cats), 2):
row = []
for key, val in cats[i:i+2]:
row.append(InlineKeyboardButton(val[“name”], callback_data=“cat_” + key))
buttons.append(row)
if is_admin(user_id):
buttons.append([InlineKeyboardButton(“Admin Panel”, callback_data=“admin_panel”)])
return InlineKeyboardMarkup(buttons)

def category_keyboard(cat_key, items, page=0):
data = load_data()
PAGE_SIZE = 5
start = page * PAGE_SIZE
end = start + PAGE_SIZE
page_items = items[start:end]
buttons = []
for i, item in enumerate(page_items):
idx = start + i
buttons.append([InlineKeyboardButton(item[“name”], callback_data=“item_” + cat_key + “*” + str(idx))])
nav = []
if page > 0:
nav.append(InlineKeyboardButton(“Oldingi”, callback_data=“page*” + cat_key + “*” + str(page - 1)))
if end < len(items):
nav.append(InlineKeyboardButton(“Keyingi”, callback_data=“page*” + cat_key + “_” + str(page + 1)))
if nav:
buttons.append(nav)
buttons.append([InlineKeyboardButton(“Bosh menyu”, callback_data=“main_menu”)])
return InlineKeyboardMarkup(buttons)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
user = update.effective_user
text = “Salom “ + user.first_name + “!\n\nUstachi Botga xush kelibsiz!\nBo’limni tanlang:”
await update.message.reply_text(text, reply_markup=main_menu_keyboard(user.id))

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
query = update.callback_query
await query.answer()
data_str = query.data
user_id = query.from_user.id
db = load_data()

```
if data_str == "main_menu":
    await query.edit_message_text("Ustachi Bot - Bosh menyu\nBo'limni tanlang:", reply_markup=main_menu_keyboard(user_id))

elif data_str.startswith("cat_"):
    cat_key = data_str[4:]
    if cat_key not in db["categories"]:
        await query.edit_message_text("Kategoriya topilmadi")
        return
    cat = db["categories"][cat_key]
    items = cat["items"]
    if not items:
        await query.edit_message_text(
            cat["name"] + "\n\nHozircha mahsulot yo'q.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Bosh menyu", callback_data="main_menu")]])
        )
        return
    await query.edit_message_text(
        cat["name"] + "\n\nMahsulotni tanlang:",
        reply_markup=category_keyboard(cat_key, items, 0)
    )

elif data_str.startswith("page_"):
    parts = data_str.split("_")
    cat_key = parts[1]
    page = int(parts[2])
    items = db["categories"][cat_key]["items"]
    await query.edit_message_text(
        db["categories"][cat_key]["name"] + "\n\nMahsulotni tanlang:",
        reply_markup=category_keyboard(cat_key, items, page)
    )

elif data_str.startswith("item_"):
    parts = data_str.split("_", 2)
    cat_key = parts[1]
    idx = int(parts[2])
    item = db["categories"][cat_key]["items"][idx]
    caption = item["name"] + "\n\n" + item.get("description", "")
    back_btn = InlineKeyboardMarkup([[
        InlineKeyboardButton("Orqaga", callback_data="cat_" + cat_key),
        InlineKeyboardButton("Menyu", callback_data="main_menu")
    ]])
    if item.get("photo_id"):
        try:
            await query.message.reply_photo(photo=item["photo_id"], caption=caption, reply_markup=back_btn)
            await query.message.delete()
        except Exception:
            await query.edit_message_text(caption, reply_markup=back_btn)
    else:
        await query.edit_message_text(caption, reply_markup=back_btn)

elif data_str == "admin_panel":
    if not is_admin(user_id):
        await query.edit_message_text("Ruxsat yo'q!")
        return
    await show_admin_panel(query, db)

elif data_str.startswith("admin_add_"):
    if not is_admin(user_id):
        return
    cat_key = data_str[10:]
    context.user_data["add_cat"] = cat_key
    context.user_data["state"] = "wait_name"
    await query.edit_message_text(
        db["categories"][cat_key]["name"] + " ga yangi mahsulot qo'shish\n\nMahsulot nomini kiriting:",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Bekor", callback_data="admin_panel")]])
    )

elif data_str.startswith("admin_list_"):
    if not is_admin(user_id):
        return
    rest = data_str[11:]
    action, cat_key = rest.split("_", 1)
    items = db["categories"][cat_key]["items"]
    if not items:
        await query.edit_message_text(
            "Bu kategoriyada mahsulot yo'q.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Orqaga", callback_data="admin_panel")]])
        )
        return
    buttons = []
    for i, item in enumerate(items):
        label = "Ochir " + item["name"] if action == "del" else "Tahrir " + item["name"]
        buttons.append([InlineKeyboardButton(label, callback_data="admin_" + action + "item_" + cat_key + "_" + str(i))])
    buttons.append([InlineKeyboardButton("Orqaga", callback_data="admin_panel")])
    await query.edit_message_text("Mahsulotni tanlang:", reply_markup=InlineKeyboardMarkup(buttons))

elif data_str.startswith("admin_delitem_"):
    if not is_admin(user_id):
        return
    rest = data_str[14:]
    parts = rest.split("_", 1)
    cat_key = parts[0]
    idx = int(parts[1])
    item_name = db["categories"][cat_key]["items"][idx]["name"]
    context.user_data["del_cat"] = cat_key
    context.user_data["del_idx"] = idx
    await query.edit_message_text(
        item_name + " ni o'chirishni tasdiqlaysizmi?",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("Ha, o'chir", callback_data="confirm_delete"),
            InlineKeyboardButton("Yo'q", callback_data="admin_panel")
        ]])
    )

elif data_str == "confirm_delete":
    if not is_admin(user_id):
        return
    cat_key = context.user_data.get("del_cat")
    idx = context.user_data.get("del_idx")
    if cat_key and idx is not None:
        db["categories"][cat_key]["items"].pop(idx)
        save_data(db)
    await query.edit_message_text("Mahsulot o'chirildi!")
    await show_admin_panel(query, db)

elif data_str.startswith("admin_edititem_"):
    if not is_admin(user_id):
        return
    rest = data_str[15:]
    parts = rest.split("_", 1)
    cat_key = parts[0]
    idx = int(parts[1])
    item = db["categories"][cat_key]["items"][idx]
    context.user_data["edit_cat"] = cat_key
    context.user_data["edit_idx"] = idx
    await query.edit_message_text(
        item["name"] + " ni tahrirlash - nimani o'zgartirmoqchisiz?",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Nom", callback_data="edit_name"),
             InlineKeyboardButton("Tavsif", callback_data="edit_desc")],
            [InlineKeyboardButton("Rasm", callback_data="edit_photo")],
            [InlineKeyboardButton("Orqaga", callback_data="admin_panel")]
        ])
    )

elif data_str in ["edit_name", "edit_desc", "edit_photo"]:
    if not is_admin(user_id):
        return
    msgs = {"edit_name": "Yangi nomni kiriting:", "edit_desc": "Yangi tavsifni kiriting:", "edit_photo": "Yangi rasmni yuboring:"}
    context.user_data["state"] = data_str
    await query.edit_message_text(msgs[data_str], reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Bekor", callback_data="admin_panel")]]))

elif data_str == "skip_desc":
    context.user_data["new_desc"] = ""
    context.user_data["state"] = "wait_photo"
    await query.edit_message_text("Rasm yuboring:", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Rasmsiz saqlash", callback_data="skip_photo")]]))

elif data_str == "skip_photo":
    context.user_data["new_photo"] = None
    db = load_data()
    cat_key = context.user_data["add_cat"]
    item = {
        "name": context.user_data.get("new_name", "Nomsiz"),
        "description": context.user_data.get("new_desc", ""),
        "photo_id": None
    }
    db["categories"][cat_key]["items"].append(item)
    save_data(db)
    context.user_data["state"] = None
    await query.edit_message_text(item["name"] + " qo'shildi!")
    await show_admin_panel(query, db)
```

async def show_admin_panel(query, db):
buttons = []
for key, val in db[“categories”].items():
count = len(val[“items”])
buttons.append([
InlineKeyboardButton(”+” + val[“name”] + “ (” + str(count) + “)”, callback_data=“admin_add_” + key),
InlineKeyboardButton(“Tahrir”, callback_data=“admin_list_edit_” + key),
InlineKeyboardButton(“Ochir”, callback_data=“admin_list_del_” + key),
])
buttons.append([InlineKeyboardButton(“Bosh menyu”, callback_data=“main_menu”)])
await query.edit_message_text(“Admin Panel\n+ Qoshish | Tahrir | Ochir”, reply_markup=InlineKeyboardMarkup(buttons))

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
user_id = update.effective_user.id
if not is_admin(user_id):
return
state = context.user_data.get(“state”)
db = load_data()

```
if state == "wait_name":
    context.user_data["new_name"] = update.message.text
    context.user_data["state"] = "wait_desc"
    await update.message.reply_text(
        "Tavsif kiriting:",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("O'tkazib yuborish", callback_data="skip_desc")]])
    )

elif state == "wait_desc":
    context.user_data["new_desc"] = update.message.text
    context.user_data["state"] = "wait_photo"
    await update.message.reply_text(
        "Rasm yuboring:",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Rasmsiz saqlash", callback_data="skip_photo")]])
    )

elif state == "wait_photo":
    if update.message.photo:
        context.user_data["new_photo"] = update.message.photo[-1].file_id
        cat_key = context.user_data["add_cat"]
        item = {
            "name": context.user_data.get("new_name", "Nomsiz"),
            "description": context.user_data.get("new_desc", ""),
            "photo_id": context.user_data["new_photo"]
        }
        db["categories"][cat_key]["items"].append(item)
        save_data(db)
        context.user_data["state"] = None
        await update.message.reply_text(item["name"] + " qo'shildi!", reply_markup=main_menu_keyboard(user_id))
    else:
        await update.message.reply_text("Iltimos rasm yuboring.")

elif state == "edit_name":
    cat_key = context.user_data["edit_cat"]
    idx = context.user_data["edit_idx"]
    db["categories"][cat_key]["items"][idx]["name"] = update.message.text
    save_data(db)
    context.user_data["state"] = None
    await update.message.reply_text("Nom yangilandi!", reply_markup=main_menu_keyboard(user_id))

elif state == "edit_desc":
    cat_key = context.user_data["edit_cat"]
    idx = context.user_data["edit_idx"]
    db["categories"][cat_key]["items"][idx]["description"] = update.message.text
    save_data(db)
    context.user_data["state"] = None
    await update.message.reply_text("Tavsif yangilandi!", reply_markup=main_menu_keyboard(user_id))

elif state == "edit_photo":
    if update.message.photo:
        cat_key = context.user_data["edit_cat"]
        idx = context.user_data["edit_idx"]
        db["categories"][cat_key]["items"][idx]["photo_id"] = update.message.photo[-1].file_id
        save_data(db)
        context.user_data["state"] = None
        await update.message.reply_text("Rasm yangilandi!", reply_markup=main_menu_keyboard(user_id))
    else:
        await update.message.reply_text("Iltimos rasm yuboring.")
```

def main():
app = Application.builder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler(“start”, start))
app.add_handler(CallbackQueryHandler(button_handler))
app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, message_handler))
print(“Bot ishga tushdi!”)
app.run_polling()

if **name** == “**main**”:
main()
