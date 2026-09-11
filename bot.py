import os
import uuid
import logging
from dotenv import load_dotenv
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    LabeledPrice,
    Update,
    WebAppInfo,
    ChatMember,
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    PreCheckoutQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from database import (
    init_db,
    save_user,
    activate_pro,
    save_payment,
    get_pro_until,
    get_user,
    add_affiliate_stars,
    affiliate_stats,
    set_group_media,
    get_group_media,
    clear_group_media,
    save_raid,
    stop_raid,
    get_active_raid,
    add_check,
    raid_checks,
)

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN", "").strip()
MINI = os.getenv("MINI_APP_URL", "https://zubimani9.github.io/raidex-mini_app/").strip()
BOT_USERNAME = os.getenv("BOT_USERNAME", "RaiDEX_RadarBot").strip().lstrip("@")
AFF_PCT = float(os.getenv("AFF_PCT", "0.20"))

if not TOKEN:
    raise RuntimeError("BOT_TOKEN is missing")

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("raidex")

PLANS = {
    "pro_7": ("PRO 7 Days", 7, 750),
    "pro_15": ("PRO 15 Days", 15, 1500),
    "pro_30": ("PRO 30 Days", 30, 2500),
}
FREE_GOALS = (10, 5, 3)


def mini_button(text="Open RaiDEX"):
    return InlineKeyboardButton(text, web_app=WebAppInfo(url=MINI))


def kb():
    return InlineKeyboardMarkup(
        [
            [mini_button()],
            [
                InlineKeyboardButton("Trending", callback_data="trending"),
                InlineKeyboardButton("X Radar", callback_data="radar"),
            ],
            [
                InlineKeyboardButton("Vote", callback_data="vote"),
                InlineKeyboardButton("PRO", callback_data="pro"),
            ],
            [
                InlineKeyboardButton("Leaderboard", callback_data="leaderboard"),
                InlineKeyboardButton("Profile", callback_data="profile"),
            ],
            [
                InlineKeyboardButton("Plans", callback_data="pro"),
                InlineKeyboardButton("Affiliate", callback_data="affiliate"),
            ],
        ]
    )


def plans_kb():
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("750 Stars — 7 days", callback_data="buy:pro_7")],
            [InlineKeyboardButton("1500 Stars — 15 days", callback_data="buy:pro_15")],
            [InlineKeyboardButton("2500 Stars — 30 days", callback_data="buy:pro_30")],
        ]
    )


def media_from_message(msg):
    if not msg:
        return None, None
    if msg.animation:
        return msg.animation.file_id, "gif"
    if msg.photo:
        return msg.photo[-1].file_id, "photo"
    if msg.video:
        return msg.video.file_id, "video"
    if msg.sticker and msg.sticker.is_video:
        return msg.sticker.file_id, "video"
    if msg.document and (msg.document.mime_type or "").startswith("image/"):
        return msg.document.file_id, "photo"
    return None, None


async def bot_is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    member = await context.bot.get_chat_member(update.effective_chat.id, context.bot.id)
    return member.status in (ChatMember.ADMINISTRATOR, ChatMember.OWNER)


async def user_is_group_admin(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id=None) -> bool:
    user_id = user_id or update.effective_user.id
    member = await context.bot.get_chat_member(update.effective_chat.id, user_id)
    return member.status in (ChatMember.ADMINISTRATOR, ChatMember.OWNER)


async def send_raid_card(message, url, likes, comments, reposts, file_id=None, media_type=None):
    text = (
        "RAID TASK\n\n"
        f"{url}\n\n"
        f"Likes: {likes}\n"
        f"Comments: {comments}\n"
        f"Reposts: {reposts}\n\n"
        "Open the post, complete the task yourself, then tap I raided."
    )
    markup = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("Open post", url=url)],
            [InlineKeyboardButton("I raided", callback_data="did")],
        ]
    )
    if media_type == "gif" and file_id:
        return await message.reply_animation(file_id, caption=text, reply_markup=markup)
    if media_type == "photo" and file_id:
        return await message.reply_photo(file_id, caption=text, reply_markup=markup)
    if media_type == "video" and file_id:
        return await message.reply_video(file_id, caption=text, reply_markup=markup)
    return await message.reply_text(text, reply_markup=markup)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    ref_by = None
    if context.args and context.args[0].startswith("ref"):
        try:
            ref_by = int(context.args[0][3:])
        except ValueError:
            ref_by = None
    save_user(user.id, user.username, user.first_name, ref_by)
    await update.message.reply_text(
        "Welcome to RaiDEX\n\n"
        "Crypto radar + group raid tasks.\n\n"
        "Add the bot to a group and make it ADMIN.\n"
        "Then a group admin can run:\n"
        "/raid https://x.com/user/status/123\n\n"
        "Free task: 10 likes, 5 comments, 3 reposts\n"
        "PRO: /plans  (Telegram Stars)\n"
        "Affiliate: /affiliate\n"
        "Media: reply to a photo/GIF with /raid <link> or /setmedia",
        reply_markup=kb(),
    )


async def trending(update, context):
    await update.message.reply_text(
        "Top Trending\n\nRaiDEX, Bitcoin, Ethereum, Solana\n\nOpen the Mini App for live data.",
        reply_markup=InlineKeyboardMarkup([[mini_button()]]),
    )


async def vote(update, context):
    await update.message.reply_text(
        "Open RaiDEX to vote.",
        reply_markup=InlineKeyboardMarkup([[mini_button("Vote")]]),
    )


async def radar(update, context):
    await update.message.reply_text(
        "X Radar is available inside RaiDEX.",
        reply_markup=InlineKeyboardMarkup([[mini_button("Open Radar")]]),
    )


async def profile(update, context):
    user = update.effective_user
    save_user(user.id, user.username, user.first_name)
    await update.message.reply_text(
        f"Profile\n\nUser ID: `{user.id}`\nUsername: @{user.username or 'not set'}\nPRO: {get_pro_until(user.id) or 'Inactive'}",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("PRO", callback_data="pro")]]),
    )


async def pro(update, context):
    target = update.effective_message
    if update.effective_chat.type != "private":
        await target.reply_text("Open a private chat with the bot and send /plans")
        return
    await target.reply_text(
        "RaiDEX PRO\n\n"
        "750 Stars — 7 days\n"
        "1500 Stars — 15 days\n"
        "2500 Stars — 30 days\n\n"
        "Pay with Telegram Stars.",
        reply_markup=plans_kb(),
    )


async def plans(update, context):
    await pro(update, context)


async def send_affiliate(chat_id, user_id, context):
    stars, refs = affiliate_stats(user_id)
    link = f"https://t.me/{BOT_USERNAME}?start=ref{user_id}"
    await context.bot.send_message(
        chat_id,
        "AFFILIATE PROGRAM\n\n"
        f"Your link:\n{link}\n\n"
        "Share this link. If that user buys PRO with Stars, you receive 20% credit.\n\n"
        f"Referrals: {refs}\n"
        f"Balance: {stars} Stars\n\n"
        "Ask the owner for payout when you want to withdraw.",
    )


async def affiliate(update, context):
    if update.effective_chat.type != "private":
        await update.message.reply_text("Open a private chat with the bot and send /affiliate")
        return
    user = update.effective_user
    save_user(user.id, user.username, user.first_name)
    await send_affiliate(user.id, user.id, context)


async def raid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if chat.type not in ("group", "supergroup"):
        await update.message.reply_text("Use /raid inside a group.")
        return
    if not await bot_is_admin(update, context):
        await update.message.reply_text("Make this bot a group ADMIN first.")
        return
    if not await user_is_group_admin(update, context):
        await update.message.reply_text("Only a group admin can start a raid.")
        return
    if not context.args:
        await update.message.reply_text(
            "Usage:\n"
            "/raid https://x.com/user/status/123\n\n"
            "Optional: reply to a photo, GIF, or video with that command."
        )
        return

    url = context.args[0]
    if "x.com/" not in url and "twitter.com/" not in url:
        await update.message.reply_text("Send a valid X / Twitter post link.")
        return

    likes, comments, reposts = FREE_GOALS
    file_id, media_type = media_from_message(update.message.reply_to_message)
    if not file_id:
        saved = get_group_media(chat.id)
        if saved:
            file_id, media_type = saved["file_id"], saved["media_type"]

    save_raid(chat.id, url, likes, comments, reposts, update.effective_user.id, file_id, media_type)
    await send_raid_card(update.message, url, likes, comments, reposts, file_id, media_type)


async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type not in ("group", "supergroup"):
        return
    if not await user_is_group_admin(update, context):
        await update.message.reply_text("Only a group admin can stop a raid.")
        return
    stop_raid(update.effective_chat.id)
    await update.message.reply_text("Raid stopped.")


async def setmedia(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if chat.type not in ("group", "supergroup"):
        await update.message.reply_text("Use /setmedia inside a group.")
        return
    if not await bot_is_admin(update, context):
        await update.message.reply_text("Make this bot a group ADMIN first.")
        return
    if not await user_is_group_admin(update, context):
        await update.message.reply_text("Only a group admin can set raid media.")
        return

    src = update.message.reply_to_message or update.message
    file_id, media_type = media_from_message(src)
    if not file_id:
        await update.message.reply_text(
            "Reply to a photo, GIF, or video with /setmedia\n"
            "or send the media with /setmedia in the caption."
        )
        return
    set_group_media(chat.id, file_id, media_type)
    await update.message.reply_text(f"Default raid media saved ({media_type}).")


async def clearmedia(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type not in ("group", "supergroup"):
        return
    if not await user_is_group_admin(update, context):
        return
    clear_group_media(update.effective_chat.id)
    await update.message.reply_text("Default raid media cleared.")


async def leaderboard(update, context):
    chat = update.effective_chat
    if chat.type in ("group", "supergroup"):
        rows = raid_checks(chat.id)
        if not rows:
            await update.message.reply_text("No check-ins for this raid yet.")
            return
        lines = [f"{i}. `{row['user_id']}`" for i, row in enumerate(rows, 1)]
        await update.message.reply_text("This raid:\n" + "\n".join(lines), parse_mode="Markdown")
        return
    await update.message.reply_text("Open a group and send /leaderboard during a raid.")


async def send_invoice_for(context, chat_id, user_id, plan_id):
    name, days, stars = PLANS[plan_id]
    payload = f"raidex:{plan_id}:{user_id}:{uuid.uuid4().hex}"
    await context.bot.send_invoice(
        chat_id=chat_id,
        title=name,
        description=f"RaiDEX PRO for {days} days",
        payload=payload,
        currency="XTR",
        prices=[LabeledPrice(name, stars)],
        provider_token="",
    )


async def callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    data = q.data

    if data == "did":
        raid_row = get_active_raid(q.message.chat_id)
        if not raid_row:
            await q.answer("No active raid", show_alert=True)
            return
        count = add_check(q.message.chat_id, q.from_user.id)
        await q.message.reply_text(f"{q.from_user.first_name} checked in. Members: {count}")
        return

    if data == "trending":
        await q.message.reply_text("Trending: RaiDEX, Bitcoin, Ethereum, Solana")
    elif data == "radar":
        await q.message.reply_text(
            "X Radar: open the Mini App.",
            reply_markup=InlineKeyboardMarkup([[mini_button()]]),
        )
    elif data == "vote":
        await q.message.reply_text("Vote in RaiDEX.", reply_markup=InlineKeyboardMarkup([[mini_button()]]))
    elif data == "leaderboard":
        await leaderboard(update, context)
    elif data == "profile":
        user = q.from_user
        save_user(user.id, user.username, user.first_name)
        await q.message.reply_text(
            f"Profile\n\nUser ID: `{user.id}`\nUsername: @{user.username or 'not set'}\nPRO: {get_pro_until(user.id) or 'Inactive'}",
            parse_mode="Markdown",
        )
    elif data == "pro":
        if q.message.chat.type != "private":
            await q.message.reply_text("Open a private chat with the bot and send /plans")
            return
        await q.message.reply_text("Choose a PRO plan:", reply_markup=plans_kb())
    elif data == "affiliate":
        if q.message.chat.type != "private":
            await q.message.reply_text("Open a private chat with the bot and send /affiliate")
            return
        await send_affiliate(q.from_user.id, q.from_user.id, context)
    elif data.startswith("buy:"):
        plan_id = data[4:]
        if plan_id not in PLANS:
            return
        if q.message.chat.type != "private":
            await q.message.reply_text("Pay in a private chat with the bot: /plans")
            return
        await send_invoice_for(context, q.message.chat_id, q.from_user.id, plan_id)


async def pre(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.pre_checkout_query
    parts = q.invoice_payload.split(":")
    valid = (
        len(parts) == 4
        and parts[0] == "raidex"
        and parts[1] in PLANS
        and parts[2].isdigit()
        and int(parts[2]) == q.from_user.id
        and q.currency == "XTR"
        and q.total_amount == PLANS[parts[1]][2]
    )
    await q.answer(ok=valid, error_message=None if valid else "Payment validation failed.")


async def paid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pay = update.message.successful_payment
    user = update.effective_user
    parts = pay.invoice_payload.split(":")
    if len(parts) != 4 or parts[0] != "raidex" or parts[1] not in PLANS:
        await update.message.reply_text("Payment verification failed.")
        return
    plan_id = parts[1]
    name, days, stars = PLANS[plan_id]
    if not parts[2].isdigit() or int(parts[2]) != user.id or pay.currency != "XTR" or pay.total_amount != stars:
        await update.message.reply_text("Payment verification failed.")
        return

    save_user(user.id, user.username, user.first_name)
    until = activate_pro(user.id, days)
    save_payment(user.id, plan_id, stars, pay.invoice_payload, pay.telegram_payment_charge_id)

    row = get_user(user.id)
    if row and row["ref_by"]:
        cut = int(stars * AFF_PCT)
        if cut > 0:
            add_affiliate_stars(row["ref_by"], cut)
            try:
                await context.bot.send_message(
                    row["ref_by"],
                    f"Affiliate credit: +{cut} Stars from a PRO purchase.",
                )
            except Exception:
                pass

    await update.message.reply_text(
        f"Payment successful.\n\n{name} is active.\nPRO until {until} UTC.",
        reply_markup=InlineKeyboardMarkup([[mini_button()]]),
    )


def build_application():
    init_db()
    app = Application.builder().token(TOKEN).build()

    commands = [
        ("start", start),
        ("trending", trending),
        ("vote", vote),
        ("radar", radar),
        ("pro", pro),
        ("plans", plans),
        ("profile", profile),
        ("affiliate", affiliate),
        ("raid", raid),
        ("stop", stop),
        ("setmedia", setmedia),
        ("clearmedia", clearmedia),
        ("leaderboard", leaderboard),
    ]
    for name, fn in commands:
        app.add_handler(CommandHandler(name, fn))

    app.add_handler(CallbackQueryHandler(callbacks))
    app.add_handler(PreCheckoutQueryHandler(pre))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, paid))
    return app


if __name__ == "__main__":
    print("RaiDEX Bot starting in polling mode...")
    application = build_application()
    application.run_polling(drop_pending_updates=True)
