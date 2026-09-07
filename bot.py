import os, uuid, threading, logging
from http.server import BaseHTTPRequestHandler, HTTPServer
from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, PreCheckoutQueryHandler, MessageHandler, ContextTypes, filters
from database import init_db, save_user, activate_pro, save_payment, get_pro_until
load_dotenv(); TOKEN=os.getenv('BOT_TOKEN','').strip(); MINI=os.getenv('MINI_APP_URL','https://zubimani9.github.io/raidex-mini_app/').strip()
if not TOKEN: raise RuntimeError('BOT_TOKEN is missing')
logging.basicConfig(level=logging.INFO); log=logging.getLogger('raidex')
PLANS={'pro_7':('7 Days PRO',7,50),'pro_30':('30 Days PRO',30,150),'pro_90':('90 Days PRO',90,400)}
def kb(): return InlineKeyboardMarkup([[InlineKeyboardButton('🚀 Open RaiDEX',web_app={'url':MINI})],[InlineKeyboardButton('🔥 Trending',callback_data='trending'),InlineKeyboardButton('📡 X Radar',callback_data='radar')],[InlineKeyboardButton('🗳️ Vote',callback_data='vote'),InlineKeyboardButton('💎 PRO',callback_data='pro')],[InlineKeyboardButton('🏆 Leaderboard',callback_data='leaderboard'),InlineKeyboardButton('👤 Profile',callback_data='profile')]])
async def start(u,c):
    x=u.effective_user; save_user(x.id,x.username,x.first_name); await u.message.reply_text('🚀 *Welcome to RaiDEX*\n\nCrypto Trending & X Radar.\n\n🔥 Top Trending\n📡 X Radar\n🗳️ Community Voting\n💎 PRO Analytics\n\nTap Open RaiDEX.',parse_mode='Markdown',reply_markup=kb())
async def trending(u,c): await u.message.reply_text('🔥 *Top 10 Trending*\n\n1. RaiDEX — 98 🔥\n2. Bitcoin — 94\n3. Ethereum — 91\n4. Solana — 89\n\nLive data will be connected next.',parse_mode='Markdown',reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('🚀 Open RaiDEX',web_app={'url':MINI})]]))
async def vote(u,c): await u.message.reply_text('🗳️ Open RaiDEX to vote.',reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('🗳️ Vote',web_app={'url':MINI})]]))
async def radar(u,c): await u.message.reply_text('📡 X Radar is available inside RaiDEX.',reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('📡 Open Radar',web_app={'url':MINI})]]))
async def leaderboard(u,c): await u.message.reply_text('🏆 *Leaderboard*\n\nComing soon.',parse_mode='Markdown')
async def profile(u,c):
    x=u.effective_user; save_user(x.id,x.username,x.first_name); p=get_pro_until(x.id); await u.message.reply_text(f'👤 *Profile*\n\nUser ID: `{x.id}`\nUsername: @{x.username or "not set"}\nPRO: {p or "Inactive"}',parse_mode='Markdown',reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('💎 PRO',callback_data='pro')]]))
async def pro(u,c): await u.message.reply_text('💎 *RaiDEX PRO*\n\nChoose a plan:',parse_mode='Markdown',reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('7 Days — ⭐ 50',callback_data='buy:pro_7')],[InlineKeyboardButton('30 Days — ⭐ 150',callback_data='buy:pro_30')],[InlineKeyboardButton('90 Days — ⭐ 400',callback_data='buy:pro_90')]]))
async def callbacks(u,c):
    q=u.callback_query; await q.answer(); d=q.data
    if d=='trending': await q.message.reply_text('🔥 Trending: RaiDEX, Bitcoin, Ethereum, Solana')
    elif d=='radar': await q.message.reply_text('📡 X Radar: open the Mini App for the dashboard.',reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('Open RaiDEX',web_app={'url':MINI})]]))
    elif d=='vote': await q.message.reply_text('🗳️ Vote in RaiDEX.',reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('Open RaiDEX',web_app={'url':MINI})]]))
    elif d=='leaderboard': await q.message.reply_text('🏆 Leaderboard coming soon.')
    elif d=='profile': await profile(type('U',(),{'effective_user':q.from_user,'message':q.message})(),c)
    elif d=='pro': await pro(type('U',(),{'message':q.message})(),c)
    elif d.startswith('buy:'):
        pid=d[4:]; name,days,stars=PLANS[pid]; payload=f'raidex:{pid}:{q.from_user.id}:{uuid.uuid4().hex}'
        await c.bot.send_invoice(q.message.chat_id,name,f'RaiDEX PRO for {days} days',payload,'XTR',[LabeledPrice(name,stars)],provider_token='')
async def pre(u,c):
    q=u.pre_checkout_query; p=q.invoice_payload.split(':')
    if len(p)!=4 or p[0]!='raidex' or p[1] not in PLANS or int(p[2])!=q.from_user.id or q.currency!='XTR' or q.total_amount!=PLANS[p[1]][2]: await q.answer(ok=False,error_message='Payment validation failed.'); return
    await q.answer(ok=True)
async def paid(u,c):
    pay=u.message.successful_payment; x=u.effective_user; p=pay.invoice_payload.split(':'); pid=p[1]; name,days,stars=PLANS[pid]
    if len(p)!=4 or int(p[2])!=x.id or pay.currency!='XTR' or pay.total_amount!=stars: await u.message.reply_text('Payment verification failed.'); return
    until=activate_pro(x.id,days); save_payment(x.id,pid,stars,pay.invoice_payload,pay.telegram_payment_charge_id); await u.message.reply_text(f'✅ Payment successful!\n\n💎 {name} activated.\nPRO until {until} UTC.',reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton('🚀 Open RaiDEX',web_app={'url':MINI})]]))
def health():
    class H(BaseHTTPRequestHandler):
        def do_GET(self):
            b=b'RaiDEX bot is running.'; self.send_response(200); self.send_header('Content-Length',str(len(b))); self.end_headers(); self.wfile.write(b)
        def log_message(self,*a): pass
    HTTPServer(('0.0.0.0',int(os.getenv('PORT','10000'))),H).serve_forever()
def main():
    init_db(); threading.Thread(target=health,daemon=True).start(); app=Application.builder().token(TOKEN).build()
    for cmd,fn in [('start',start),('trending',trending),('vote',vote),('radar',radar),('pro',pro),('leaderboard',leaderboard),('profile',profile)]: app.add_handler(CommandHandler(cmd,fn))
    app.add_handler(CallbackQueryHandler(callbacks)); app.add_handler(PreCheckoutQueryHandler(pre)); app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT,paid)); log.info('RaiDEX starting'); app.run_polling(allowed_updates=Update.ALL_TYPES)
if __name__=='__main__': main()
