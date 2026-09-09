import logging
import os
import uuid

from dotenv import load_dotenv
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    LabeledPrice,
    Update,
    WebAppInfo,
)
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    PreCheckoutQueryHandler,
    filters,
)

from database import (
    activate_pro,
    get_pro_until,
    init_db,
    save_payment,
    save_user,
)

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN", "").strip()
MINI = os.getenv(
    "MINI_APP_URL",
    "https://zubimani9.github.io/raidex-mini_app/"
).strip()

if not TOKEN:
    raise RuntimeError("BOT_TOKEN is missing")

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("raidex")

PLANS = {
    "pro_7": ("7 Days PRO", 7, 50),
    "pro_30": ("30 Days PRO", 30, 150),
    "pro_90": ("90 Days PRO", 90, 400),
}


def mini_button(text="🚀 Open RaiDEX"):
    return InlineKeyboardButton(text, web_app=WebAppInfo(url=MINI))


def kb():
    return InlineKeyboardMarkup([
        [mini_button()],
        [
            InlineKeyboardButton("🔥 Trending", callback_data="trending"),
            InlineKeyboardButton("📡 X Radar", callback_data="radar"),
        ],
        [
            InlineKeyboardButton("🗳️ Vote", callback_data="vote"),
            InlineKeyboardButton("💎 PRO", callback_data="pro"),
        ],
        [
            InlineKeyboardButton("🏆 Leaderboard", callback_data="leaderboard"),
            InlineKeyboardButton("👤 Profile", callback_data="profile"),
        ],
    ])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    save_user(user.id, user.username, user.first_name)

    await update.message.reply_text(
        "🚀 *Welcome to RaiDEX*\n\n"
        "Crypto Trending & X Radar.\n\n"
        "🔥 Top Trending\n"
        "📡 X Radar\n"
        "🗳️ Community Voting\n"
        "💎 PRO Analytics\n\n"
        "Tap Open RaiDEX.",
        parse_mode="Markdown",
        reply_markup=kb(),
    )


async def trending(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔥 *Top 10 Trending*\n\n"
        "1. RaiDEX — 98 🔥\n"
        "2. Bitcoin — 94\n"
        "3. Ethereum — 91\n"
        "4. Solana — 89\n\n"
        "Live data will be connected next.",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([[mini_button()]]),
    )


async def vote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🗳️ Open RaiDEX to vote.",
        reply_markup=InlineKeyboardMarkup([[mini_button("🗳️ Vote")]]),
    )


async def radar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📡 X Radar is available inside RaiDEX.",
        reply_markup=InlineKeyboardMarkup([[mini_button("📡 Open Radar")]]),
    )


async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🏆 *Leaderboard*\n\nComing soon.",
        parse_mode="Markdown",
    )


async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    save_user(user.id, user.username, user.first_name)
    pro_until = get_pro_until(user.id)

    await update.message.reply_text(
        f"👤 *Profile*\n\n"
        f"User ID: `{user.id}`\n"
        f"Username: @{user.username or 'not set'}\n"
        f"PRO: {pro_until or 'Inactive'}",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("💎 PRO", callback_data="pro")
        ]]),
    )


async def pro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "💎 *RaiDEX PRO*\n\nChoose a plan:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("7 Days — ⭐ 50", callback_data="buy:pro_7")],
            [InlineKeyboardButton("30 Days — ⭐ 150", callback_data="buy:pro_30")],
            [InlineKeyboardButton("90 Days — ⭐ 400", callback_data="buy:pro_90")],
        ]),
    )


async def callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "trending":
        await query.message.reply_text(
            "🔥 Trending: RaiDEX, Bitcoin, Ethereum, Solana"
        )

    elif data == "radar":
        await query.message.reply_text(
            "📡 X Radar: open the Mini App for the dashboard.",
            reply_markup=InlineKeyboardMarkup([
                [mini_button("Open RaiDEX")]
            ]),
        )

    elif data == "vote":
        await query.message.reply_text(
            "🗳️ Vote in RaiDEX.",
            reply_markup=InlineKeyboardMarkup([
                [mini_button("Open RaiDEX")]
            ]),
        )

    elif data == "leaderboard":
        await query.message.reply_text("🏆 Leaderboard coming soon.")

    elif data == "profile":
        await query.message.reply_text(
            f"👤 *Profile*\n\n"
            f"User ID: `{query.from_user.id}`\n"
            f"Username: @{query.from_user.username or 'not set'}\n"
            f"PRO: {get_pro_until(query.from_user.id) or 'Inactive'}",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("💎 PRO", callback_data="pro")
            ]]),
        )

    elif data == "pro":
        await pro(
            Update(update.update_id, message=query.message),
            context,
        )

    elif data.startswith("buy:"):
        pid = data[4:]

        if pid not in PLANS:
            await query.message.reply_text("Invalid plan.")
            return

        name, days, stars = PLANS[pid]
        payload = (
            f"raidex:{pid}:{query.from_user.id}:"
            f"{uuid.uuid4().hex}"
        )

        await context.bot.send_invoice(
            chat_id=query.message.chat_id,
            title=name,
            description=f"RaiDEX PRO for {days} days",
            payload=payload,
            currency="XTR",
            prices=[LabeledPrice(name, stars)],
            provider_token="",
        )


async def pre_checkout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.pre_checkout_query

    try:
        parts = query.invoice_payload.split(":")
        valid = (
            len(parts) == 4
            and parts[0] == "raidex"
            and parts[1] in PLANS
            and int(parts[2]) == query.from_user.id
            and query.currency == "XTR"
            and query.total_amount == PLANS[parts[1]][2]
        )
    except (ValueError, TypeError):
        valid = False

    if not valid:
        await query.answer(
            ok=False,
            error_message="Payment validation failed."
        )
        return

    await query.answer(ok=True)


async def paid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    payment = update.message.successful_payment
    user = update.effective_user

    try:
        parts = payment.invoice_payload.split(":")
        valid = (
            len(parts) == 4
            and parts[0] == "raidex"
            and parts[1] in PLANS
            and int(parts[2]) == user.id
            and payment.currency == "XTR"
            and payment.total_amount == PLANS[parts[1]][2]
        )
    except (ValueError, TypeError):
        valid = False
        parts = []

    if not valid:
        await update.message.reply_text("Payment verification failed.")
        return

    pid = parts[1]
    name, days, stars = PLANS[pid]

    until = activate_pro(user.id, days)
    save_payment(
        user.id,
        pid,
        stars,
        payment.invoice_payload,
        payment.telegram_payment_charge_id,
    )

    await update.message.reply_text(
        f"✅ Payment successful!\n\n"
        f"💎 {name} activated.\n"
        f"PRO until {until} UTC.",
        reply_markup=InlineKeyboardMarkup([[mini_button()]]),
    )


def build_application():
    init_db()

    app = (
        Application.builder()
        .token(TOKEN)
        .updater(None)
        .build()
    )

    for command, function in [
        ("start", start),
        ("trending", trending),
        ("vote", vote),
        ("radar", radar),
        ("pro", pro),
        ("leaderboard", leaderboard),
        ("profile", profile),
    ]:
        app.add_handler(CommandHandler(command, function))

    app.add_handler(CallbackQueryHandler(callbacks))
    app.add_handler(PreCheckoutQueryHandler(pre_checkout))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, paid))

    return app
