from telegram.ext import Updater, CommandHandler, RegexHandler, MessageHandler,Filters
from telegram import ReplyKeyboardMarkup,Bot
import requests,json
import os

config = json.load(open('config.json','r'))

TOKEN = config['token']
DEV = True
signup = config['signup']
refr = config['ref']
admins = config['admins']
data = []
dash_key = [['Twitter','Reddit','BSC address'],['Referral Link','Referred'],['Balance','Details']]
admin_key = [['Users','Get List']]

webhook_url = 'http://localhost:8433'
PORT = int(os.environ.get('PORT','8443'))

def set_data_safe(user, key, value, default):
    if key not in data.keys():
        data[key] = {}
    if user not in data[key].keys():
        data[key][user] = default
    data[key][user] = value

def start(update, context):
    if update.message.chat.type == 'private':
        user = str(update.message.chat.username)
        if user not in data['users']:
            data['users'].append(user)
            set_data_safe(user, 'twitter', "", "")
            set_data_safe(user, 'reddit', "", "")
            set_data_safe(user, 'bsc', "", "")

            ref_id = update.message.text.split()
            if len(ref_id) > 1:
                data['ref'][user] = ref_id[1]
                if str(ref_id[1]) not in data['referred']:
                    data['referred'][str(ref_id[1])] = 1
                else:
                    data['referred'][str(ref_id[1])] += 1
            else:
                data['ref'][user] = 0
            data['total'] += 1
            data['id'][user] = data['total']
            data['process'][user] = "twitter"
            json.dump(data,open('users.json','w'))
            msg = config['intro']
            started_msg = config['twitter_message']
            update.message.reply_text(msg)
            update.message.reply_text(started_msg)
        else:
            welcome_msg = config['dashboard_message']
            reply_markup = ReplyKeyboardMarkup(dash_key,resize_keyboard=True)
            update.message.reply_text(welcome_msg,reply_markup=reply_markup)

    else:
        msg = '{} \n. I don\'t reply in group, come in private'.format(config['intro'])
        update.message.reply_text(msg)

def twitter(update, context):
    if update.message.chat.type == 'private':
        user = str(update.message.chat.username)
        twtr_user = data['twitter'][user]
        msg = 'Your twitter username is {}'.format(twtr_user)
        reply_markup = ReplyKeyboardMarkup(dash_key,resize_keyboard=True)
        update.message.reply_text(msg,reply_markup=reply_markup)

def bsc(update, context):
    if update.message.chat.type == 'private':
        user = str(update.message.chat.username)
        bsc_addr = data['bsc'][user]
        msg = 'Your bsc address is {}'.format(bsc_addr)
        reply_markup = ReplyKeyboardMarkup(dash_key,resize_keyboard=True)
        update.message.reply_text(msg,reply_markup=reply_markup)

def reddit(update, context):
    if update.message.chat.type == 'private':
        user = str(update.message.chat.username)
        du = data['reddit'][user]
        msg = 'Your Reddit username is {}'.format(du)
        reply_markup = ReplyKeyboardMarkup(dash_key,resize_keyboard=True)
        update.message.reply_text(msg,reply_markup=reply_markup)

def link(update, context):
    if update.message.chat.type == 'private':
        user = str(update.message.chat.username)
        msg = 'https://t.me/{}?start={}'.format(config['botname'],data['id'][user])
        reply_markup = ReplyKeyboardMarkup(dash_key,resize_keyboard=True)
        update.message.reply_text(msg,reply_markup=reply_markup)


def extra(update, context):
    if update.message.chat.type == 'private':
        user = str(update.message.chat.username)
        if data["process"][user] == 'twitter':
            data['twitter'][user] = update.message.text
            data['process'][user] = 'reddit'
            json.dump(data,open('users.json','w'))
            update.message.reply_text(config['reddit_message'])
        elif data["process"][user] == 'reddit':
            data['reddit'][user] = update.message.text
            data['process'][user] = "bsc"
            json.dump(data,open('users.json','w'))
            update.message.reply_text(config['bsc_message'])
        elif data["process"][user] == 'bsc':
            data['bsc'][user] = update.message.text
            data['process'][user] = "finished"
            json.dump(data,open('users.json','w'))
            msg = config['dashboard_message']
            reply_markup = ReplyKeyboardMarkup(dash_key,resize_keyboard=True)
            update.message.reply_text(msg,reply_markup=reply_markup)
        else:
            msg = "Please select one of the options."
            reply_markup = ReplyKeyboardMarkup(dash_key,resize_keyboard=True)
            update.message.reply_text(msg,reply_markup=reply_markup)

def ref(update, context):
    if update.message.chat.type == 'private':
        user = str(update.message.chat.username)
        i = str(data["id"][user])
        referred = 0
        if i in data['referred']:
            referred = data['referred'][i]
        msg = "You have referred {} people".format(referred)
        reply_markup = ReplyKeyboardMarkup(dash_key,resize_keyboard=True)
        update.message.reply_text(msg,reply_markup=reply_markup)

def admin(update, context):
    if update.message.chat.type == 'private':
        user = str(update.message.chat.username)
        if user in admins:
            msg = "Welcome to Admin Dashboard"
            reply_markup = ReplyKeyboardMarkup(admin_key,resize_keyboard=True)
            update.message.reply_text(msg,reply_markup=reply_markup)

def users(update, context):
    if update.message.chat.type == 'private':
        user = str(update.message.chat.username)
        if user in admins:
            msg = "A total of {} have joined this program".format(data['total']-1000)
            reply_markup = ReplyKeyboardMarkup(admin_key,resize_keyboard=True)
            update.message.reply_text(msg,reply_markup=reply_markup)

def get_file(update, context):
    if update.message.chat.type == 'private':
        user = str(update.message.chat.username)
        if user in admins:
            f = open('users.csv','w')
            f.write("id,username,twitter username,bsc address,reddit,no. of persons referred,referred by\n")
            for u in data['users']:
                i = str(data['id'][u])
                refrrd = 0
                if i in data['referred']:
                    refrrd = data['referred'][i]
                d = "{},{},{},{},{},{},{}\n".format(i,u,data['twitter'][u],data['bsc'][u],data['reddit'][u],refrrd,data['ref'][u])
                f.write(d)
            f.close()
            bot = Bot(TOKEN)
            bot.send_document(chat_id=update.message.chat.id, document=open('users.csv','rb'))

def bal(update, context):
    if update.message.chat.type == 'private':
        user = str(update.message.chat.username)
        i = str(data["id"][user])
        referred = 0
        if i in data['referred']:
            referred = data['referred'][i]
        bal = signup + refr * referred
        msg = "You have {} points".format(bal)
        reply_markup = ReplyKeyboardMarkup(dash_key,resize_keyboard=True)
        update.message.reply_text(msg,reply_markup=reply_markup)

def detail(update, context):
    if update.message.chat.type == 'private':
        msg = config['details']
        reply_markup = ReplyKeyboardMarkup(dash_key,resize_keyboard=True)
        update.message.reply_text(msg,reply_markup=reply_markup)

if __name__ == '__main__':
    data = json.load(open('users.json','r'))
    updater = Updater(TOKEN,use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start",start))
    dp.add_handler(CommandHandler("admin",admin))
    dp.add_handler(RegexHandler("^Twitter$",twitter))
    dp.add_handler(RegexHandler("^BSC address$",bsc))
    dp.add_handler(RegexHandler("^Reddit$",reddit))
    dp.add_handler(RegexHandler("^Referral Link$",link))
    dp.add_handler(RegexHandler("^Referred$",ref))
    dp.add_handler(RegexHandler("^Users$",users))
    dp.add_handler(RegexHandler("^Get List$",get_file))
    dp.add_handler(RegexHandler("^Balance$",bal))
    dp.add_handler(RegexHandler("^Details$",detail))
    dp.add_handler(MessageHandler(Filters.text,extra))
    if DEV is not True:
        updater.start_webhook(listen="0.0.0.0",port=PORT,url_path=TOKEN)
        updater.bot.set_webhook(webhook_url + TOKEN)
    else:
        updater.start_polling()
    print("Bot Started")
    updater.idle()
