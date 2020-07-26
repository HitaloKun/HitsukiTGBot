import json
import random
import time
from platform import python_version

import wikipedia
from emoji import UNICODE_EMOJI
from googletrans import Translator
from requests import get
from telegram import ParseMode, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.error import BadRequest
from telegram.ext import CommandHandler, run_async, Filters

import hitsuki.__main__ as hitsukiv
import hitsuki.modules.helper_funcs.git_api as git
from hitsuki import dispatcher, OWNER_ID, spamcheck
from hitsuki.modules.disable import DisableAbleCommandHandler
from hitsuki.modules.helper_funcs.alternate import send_message
from hitsuki.modules.languages import tl
from hitsuki.modules.sql import languages_sql as langsql

reactions = [
    "( ͡° ͜ʖ ͡°)",
    "¯_(ツ)_/¯",
    "\'\'̵͇З= ( ▀ ͜͞ʖ▀) =Ε/̵͇/’’",
    "▄︻̷┻═━一",
    "( ͡°( ͡° ͜ʖ( ͡° ͜ʖ ͡°)ʖ ͡°) ͡°)",
    "ʕ•ᴥ•ʔ",
    "(▀Ĺ̯▀ )",
    "(ง ͠° ͟ل͜ ͡°)ง",
    "༼ つ ◕_◕ ༽つ",
    "ಠ_ಠ",
    "(づ｡◕‿‿◕｡)づ",
    "\'\'̵͇З=( ͠° ͟ʖ ͡°)=Ε/̵͇/\'",
    "(ﾉ◕ヮ◕)ﾉ*:･ﾟ✧ ✧ﾟ･: *ヽ(◕ヮ◕ヽ)",
    "[̲̅$̲̅(̲̅5̲̅)̲̅$̲̅]",
    "┬┴┬┴┤ ͜ʖ ͡°) ├┬┴┬┴",
    "( ͡°╭͜ʖ╮͡° )",
    "(͡ ͡° ͜ つ ͡͡°)",
    "(• Ε •)",
    "(ง\'̀-\'́)ง",
    "(ಥ﹏ಥ)",
    "﴾͡๏̯͡๏﴿ O\'RLY?",
    "(ノಠ益ಠ)ノ彡┻━┻",
    "[̲̅$̲̅(̲̅ ͡° ͜ʖ ͡°̲̅)̲̅$̲̅]",
    "(ﾉ◕ヮ◕)ﾉ*:･ﾟ✧",
    "(☞ﾟ∀ﾟ)☞",
    "| (• ◡•)| (❍ᴥ❍Ʋ)",
    "(◕‿◕✿)",
    "(ᵔᴥᵔ)",
    "(╯°□°)╯︵ ꞰOOQƎƆⱯɟ",
    "(¬‿¬)",
    "(☞ﾟヮﾟ)☞ ☜(ﾟヮﾟ☜)",
    "(づ￣ ³￣)づ",
    "ლ(ಠ益ಠლ)",
    "ಠ╭╮ಠ",
    "\'\'̵͇З=(•_•)=Ε/̵͇/\'\'",
    "/╲/╭( ͡° ͡° ͜ʖ ͡° ͡°)╮/╱",
    "(;´༎ຶД༎ຶ)",
    "♪~ ᕕ(ᐛ)ᕗ",
    "♥️‿♥️",
    "༼ つ ͡° ͜ʖ ͡° ༽つ",
    "༼ つ ಥ_ಥ ༽つ",
    "(╯°□°）╯︵ ┻━┻",
    "( ͡ᵔ ͜ʖ ͡ᵔ )",
    "ヾ(⌐■_■)ノ♪",
    "~(˘▾˘~)",
    "◉_◉",
    "(•◡•) /",
    "(~˘▾˘)~",
    "(._.) ( L: ) ( .-. ) ( :L ) (._.)",
    "༼ʘ̚ل͜ʘ̚༽",
    "༼ ºل͟º ༼ ºل͟º ༼ ºل͟º ༽ ºل͟º ༽ ºل͟º ༽",
    "┬┴┬┴┤(･_├┬┴┬┴",
    "ᕙ(⇀‸↼‶)ᕗ",
    "ᕦ(Ò_Óˇ)ᕤ",
    "┻━┻ ︵ヽ(Д´)ﾉ︵ ┻━┻",
    "⚆ _ ⚆",
    "(•_•) ( •_•)>⌐■-■ (⌐■_■)",
    "(｡◕‿‿◕｡)",
    "ಥ_ಥ",
    "ヽ༼ຈل͜ຈ༽ﾉ",
    "⌐╦╦═─",
    "(☞ຈل͜ຈ)☞",
    "˙ ͜ʟ˙",
    "☜(˚▽˚)☞",
    "(•Ω•)",
    "(ง°ل͜°)ง",
    "(｡◕‿◕｡)",
    "（╯°□°）╯︵( .O.)",
    ":\')",
    "┬──┬ ノ( ゜-゜ノ)",
    "(っ˘ڡ˘Σ)",
    "ಠ⌣ಠ",
    "ლ(´ڡლ)",
    "(°ロ°)☝️",
    "｡◕‿‿◕｡",
    "( ಠ ͜ʖರೃ)",
    "╚(ಠ_ಠ)=┐",
    "(─‿‿─)",
    "ƪ(˘⌣˘)Ʃ",
    "(；一_一)",
    "(¬_¬)",
    "( ⚆ _ ⚆ )",
    "(ʘᗩʘ\')",
    "☜(⌒▽⌒)☞",
    "｡◕‿◕｡",
    "¯(°_O)/¯",
    "(ʘ‿ʘ)",
    "ლ,ᔑ•ﺪ͟͠•ᔐ.ლ",
    "(´・Ω・)",
    "ಠ~ಠ",
    "(° ͡ ͜ ͡ʖ ͡ °)",
    "┬─┬ノ( º _ ºノ)",
    "(´・Ω・)っ由",
    "ಠ_ಥ",
    "Ƹ̵̡Ӝ̵̨Ʒ",
    "(>ლ)",
    "ಠ‿↼",
    "ʘ‿ʘ",
    "(ღ˘⌣˘ღ)",
    "ಠOಠ",
    "ರ_ರ",
    "(▰˘◡˘▰)",
    "◔̯◔",
    "◔ ⌣ ◔",
    "(✿´‿`)",
    "¬_¬",
    "ب_ب",
    "｡゜(｀Д´)゜｡",
    "(Ó Ì_Í)=ÓÒ=(Ì_Í Ò)",
    "°Д°",
    "( ﾟヮﾟ)",
    "┬─┬﻿ ︵ /(.□. ）",
    "٩◔̯◔۶",
    "≧☉_☉≦",
    "☼.☼",
    "^̮^",
    "(>人<)",
    "〆(・∀・＠)",
    "(~_^)",
    "^̮^",
    "^̮^",
    ">_>",
    "(^̮^)",
    "(/) (°,,°) (/)",
    "^̮^",
    "^̮^",
    "=U",
    "(･.◤)"]

reactionhappy = [
    "\'\'̵͇З= ( ▀ ͜͞ʖ▀) =Ε/̵͇/’’",
    "ʕ•ᴥ•ʔ",
    "(づ｡◕‿‿◕｡)づ",
    "(ﾉ◕ヮ◕)ﾉ*:･ﾟ✧ ✧ﾟ･: *ヽ(◕ヮ◕ヽ)",
    "(ﾉ◕ヮ◕)ﾉ*:･ﾟ✧",
    "(☞ﾟ∀ﾟ)☞",
    "| (• ◡•)| (❍ᴥ❍Ʋ)",
    "(◕‿◕✿)",
    "(ᵔᴥᵔ)",
    "(☞ﾟヮﾟ)☞ ☜(ﾟヮﾟ☜)",
    "(づ￣ ³￣)づ",
    "♪~ ᕕ(ᐛ)ᕗ",
    "♥️‿♥️",
    "༼ つ ͡° ͜ʖ ͡° ༽つ",
    "༼ つ ಥ_ಥ ༽つ",
    "ヾ(⌐■_■)ノ♪",
    "~(˘▾˘~)",
    "◉_◉",
    "(•◡•) /",
    "(~˘▾˘)~",
    "(｡◕‿‿◕｡)",
    "☜(˚▽˚)☞",
    "(•Ω•)",
    "(｡◕‿◕｡)",
    "(っ˘ڡ˘Σ)",
    "｡◕‿‿◕｡"
    "☜(⌒▽⌒)☞",
    "｡◕‿◕｡",
    "(ღ˘⌣˘ღ)",
    "(▰˘◡˘▰)",
    "^̮^",
    "^̮^",
    ">_>",
    "(^̮^)",
    "^̮^",
    "^̮^"]

reactionangry = [
    "▄︻̷┻═━一",
    "(▀Ĺ̯▀ )",
    "(ง ͠° ͟ل͜ ͡°)ง",
    "༼ つ ◕_◕ ༽つ",
    "ಠ_ಠ",
    "\'\'̵͇З=( ͠° ͟ʖ ͡°)=Ε/̵͇/\'",
    "(ง\'̀-\'́)ง",
    "(ノಠ益ಠ)ノ彡┻━┻",
    "(╯°□°)╯︵ ꞰOOQƎƆⱯɟ",
    "ლ(ಠ益ಠლ)",
    "ಠ╭╮ಠ",
    "\'\'̵͇З=(•_•)=Ε/̵͇/\'\'",
    "(╯°□°）╯︵ ┻━┻",
    "┻━┻ ︵ヽ(Д´)ﾉ︵ ┻━┻",
    "⌐╦╦═─",
    "（╯°□°）╯︵( .O.)",
    ":\')",
    "┬──┬ ノ( ゜-゜ノ)",
    "ლ(´ڡლ)",
    "(°ロ°)☝️",
    "ლ,ᔑ•ﺪ͟͠•ᔐ.ლ",
    "┬─┬ノ( º _ ºノ)",
    "┬─┬﻿ ︵ /(.□. ）"]


@run_async
@spamcheck
def react(update, context):
    message = update.effective_message
    react = random.choice(reactions)
    if message.reply_to_message:
        message.reply_to_message.reply_text(react)
    else:
        message.reply_text(react)


@run_async
@spamcheck
def rhappy(update, context):
    message = update.effective_message
    rhappy = random.choice(reactionhappy)
    if message.reply_to_message:
        message.reply_to_message.reply_text(rhappy)
    else:
        message.reply_text(rhappy)


@run_async
@spamcheck
def rangry(update, context):
    message = update.effective_message
    rangry = random.choice(reactionangry)
    if message.reply_to_message:
        message.reply_to_message.reply_text(rangry)
    else:
        message.reply_text(rangry)


@run_async
def getlink(update, context):
    args = context.args
    if args:
        chat_id = int(args[0])
    else:
        send_message(update.effective_message, tl(update.effective_message, "You don't seem to be referring to chat"))
    chat = context.bot.getChat(chat_id)
    bot_member = chat.get_member(context.bot.id)
    if bot_member.can_invite_users:
        titlechat = context.bot.get_chat(chat_id).title
        invitelink = context.bot.get_chat(chat_id).invite_link
        send_message(update.effective_message, tl(update.effective_message,
                                                  "Successfully retrieve the invite link in the group {}. \nInvite link : {}").format(
            titlechat, invitelink))
    else:
        send_message(update.effective_message,
                     tl(update.effective_message, "I don't have access to the invitation link!"))


@run_async
def leavechat(update, context):
    args = context.args
    if args:
        chat_id = int(args[0])
    else:
        send_message(update.effective_message,
                     tl(update.effective_message, "Anda sepertinya tidak mengacu pada obrolan"))
    try:
        titlechat = context.bot.get_chat(chat_id).title
        context.bot.sendMessage(chat_id, tl(update.effective_message, "Selamat tinggal semua 😁"))
        context.bot.leaveChat(chat_id)
        send_message(update.effective_message,
                     tl(update.effective_message, "Saya telah keluar dari grup {}").format(titlechat))

    except BadRequest as excp:
        if excp.message == "Chat not found":
            send_message(update.effective_message,
                         tl(update.effective_message, "Sepertinya saya sudah keluar atau di tendang di grup tersebut"))
        else:
            return


@run_async
@spamcheck
def ping(update, context):
    start_time = time.time()
    test = send_message(update.effective_message, "Pong!")
    end_time = time.time()
    ping_time = float(end_time - start_time)
    context.bot.editMessageText(chat_id=update.effective_chat.id, message_id=test.message_id,
                                text=tl(update.effective_message, "Pong!\nSpeed was: {0:.2f}s").format(
                                    round(ping_time, 2) % 60))


@run_async
@spamcheck
def fortune(update, context):
    text = ""
    if random.randint(1, 10) >= 7:
        text += random.choice(tl(update.effective_message, "RAMALAN_FIRST"))
    text += random.choice(tl(update.effective_message, "RAMALAN_STRINGS"))
    send_message(update.effective_message, text)


@run_async
@spamcheck
def translate(update, context):
    msg = update.effective_message
    getlang = langsql.get_lang(update.effective_message.from_user.id)
    try:
        if msg.reply_to_message and msg.reply_to_message.text:
            args = update.effective_message.text.split()
            if len(args) >= 2:
                target = args[1]
                if "-" in target:
                    target2 = target.split("-")[1]
                    target = target.split("-")[0]
                else:
                    target2 = None
            else:
                if getlang:
                    target = getlang
                    target2 = None
                else:
                    raise IndexError
            teks = msg.reply_to_message.text
            exclude_list = UNICODE_EMOJI.keys()
            for emoji in exclude_list:
                if emoji in teks:
                    teks = teks.replace(emoji, '')
            trl = Translator()
            if target2 is None:
                deteksibahasa = trl.detect(teks)
                tekstr = trl.translate(teks, dest=target)
                send_message(update.effective_message,
                             tl(update.effective_message, "Diterjemahkan dari `{}` ke `{}`:\n`{}`").format(
                                 deteksibahasa.lang, target, tekstr.text), parse_mode=ParseMode.MARKDOWN)
            else:
                tekstr = trl.translate(teks, dest=target2, src=target)
                send_message(update.effective_message,
                             tl(update.effective_message, "Diterjemahkan dari `{}` ke `{}`:\n`{}`").format(target,
                                                                                                           target2,
                                                                                                           tekstr.text),
                             parse_mode=ParseMode.MARKDOWN)

        else:
            args = update.effective_message.text.split(None, 2)
            if len(args) != 1:
                target = args[1]
                teks = args[2]
                target2 = None
                if "-" in target:
                    target2 = target.split("-")[1]
                    target = target.split("-")[0]
            else:
                target = getlang
                teks = args[1]
            exclude_list = UNICODE_EMOJI.keys()
            for emoji in exclude_list:
                if emoji in teks:
                    teks = teks.replace(emoji, '')
            trl = Translator()
            if target2 is None:
                deteksibahasa = trl.detect(teks)
                tekstr = trl.translate(teks, dest=target)
                return send_message(update.effective_message,
                                    tl(update.effective_message, "Diterjemahkan dari `{}` ke `{}`:\n`{}`").format(
                                        deteksibahasa.lang, target, tekstr.text), parse_mode=ParseMode.MARKDOWN)
            else:
                tekstr = trl.translate(teks, dest=target2, src=target)
                send_message(update.effective_message,
                             tl(update.effective_message, "Diterjemahkan dari `{}` ke `{}`:\n`{}`").format(target,
                                                                                                           target2,
                                                                                                           tekstr.text),
                             parse_mode=ParseMode.MARKDOWN)
    except IndexError:
        send_message(update.effective_message,
                     tl(update.effective_message, "Balas pesan atau tulis pesan dari bahasa lain untuk "
                                                  "diterjemahkan kedalam bahasa yang di dituju\n\n"
                                                  "Contoh: `/tr en-id` untuk menerjemahkan dari Bahasa inggris ke Bahasa Indonesia\n"
                                                  "Atau gunakan: `/tr id` untuk deteksi otomatis dan menerjemahkannya kedalam bahasa indonesia"),
                     parse_mode="markdown")
    except ValueError:
        send_message(update.effective_message, tl(update.effective_message, "Bahasa yang di tuju tidak ditemukan!"))
    else:
        return


@run_async
@spamcheck
def wiki(update, context):
    chat_id = update.effective_chat.id
    args = update.effective_message.text.split(None, 1)
    teks = args[1]
    getlang = langsql.get_lang(chat_id)
    if str(getlang) == "pt":
        wikipedia.set_lang("pt")
    else:
        wikipedia.set_lang("en")
    try:
        pagewiki = wikipedia.page(teks)
    except wikipedia.exceptions.PageError:
        send_message(update.effective_message, tl(update.effective_message, "Results not found"))
        return
    except wikipedia.exceptions.DisambiguationError as refer:
        rujuk = str(refer).split("\n")
        if len(rujuk) >= 6:
            batas = 6
        else:
            batas = len(rujuk)
        teks = ""
        for x in range(batas):
            if x == 0:
                if getlang == "pt":
                    teks += rujuk[x].replace('may refer to', 'pode se referir a') + "\n"
                else:
                    teks += rujuk[x] + "\n"
            else:
                teks += "- `" + rujuk[x] + "`\n"
        send_message(update.effective_message, teks, parse_mode="markdown")
        return
    except IndexError:
        send_message(update.effective_message,
                     tl(update.effective_message, "Write a message to search from the wikipedia source"))
        return
    judul = pagewiki.title
    summary = pagewiki.summary
    if update.effective_message.chat.type == "private":
        send_message(update.effective_message,
                     tl(update.effective_message, "Results of {} is:\n\n<b>{}</b>\n{}").format(teks, judul, summary),
                     parse_mode=ParseMode.HTML)
    else:
        if len(summary) >= 200:
            judul = pagewiki.title
            summary = summary[:200] + "..."
            button = InlineKeyboardMarkup([[InlineKeyboardButton(text=tl(update.effective_message, "Read More..."),
                                                                 url="t.me/{}?start=wiki-{}".format(
                                                                     context.bot.username, teks.replace(' ', '_')))]])
        else:
            button = None
        send_message(update.effective_message,
                     tl(update.effective_message, "Results of {} is:\n\n<b>{}</b>\n{}").format(teks, judul, summary),
                     parse_mode=ParseMode.HTML, reply_markup=button)


@run_async
def status(update, context):
    reply = "*Hitsuki System Info:*\n\n"
    reply += "*Hitsuki Version:* `" + str(hitsukiv.vercheck()) + "`\n"
    reply += "*Python Version:* `" + python_version() + "`\n"
    reply += "*GitHub API Version:* `" + str(git.vercheck()) + "`\n"
    update.effective_message.reply_text(reply, parse_mode=ParseMode.MARKDOWN)


@run_async
@spamcheck
def urbandictionary(update, context):
    message = update.effective_message
    text = message.text[len('/ud '):]
    if text == '':
        text = "Cockblocked By Steve Jobs"
    results = get(
        f'http://api.urbandictionary.com/v0/define?term={text}').json()
    reply_text = f'Word: {text}\nDefinition: {results["list"][0]["definition"]}'
    message.reply_text(reply_text)


@run_async
def log(update, context):
    message = update.effective_message
    eventdict = message.to_dict()
    jsondump = json.dumps(eventdict, indent=4)
    send_message(update.effective_message, jsondump)


def deEmojify(inputString):
    return inputString.encode('ascii', 'ignore').decode('ascii')


__help__ = "exclusive_help"

__mod_name__ = "🚀 Hitsuki Exclusive 🚀"

PING_HANDLER = CommandHandler("ping", ping, filters=Filters.user(OWNER_ID))
GETLINK_HANDLER = CommandHandler("getlink", getlink, pass_args=True, filters=Filters.user(OWNER_ID))
LEAVECHAT_HANDLER = CommandHandler(["leavechat", "leavegroup", "leave"], leavechat, pass_args=True,
                                   filters=Filters.user(OWNER_ID))
FORTUNE_HANDLER = DisableAbleCommandHandler("fortune", fortune)
TRANSLATE_HANDLER = DisableAbleCommandHandler("tr", translate)
WIKIPEDIA_HANDLER = DisableAbleCommandHandler("wiki", wiki)
UD_HANDLER = DisableAbleCommandHandler("ud", urbandictionary, pass_args=True)
LOG_HANDLER = CommandHandler("log", log, filters=Filters.user(OWNER_ID))
REACT_HANDLER = DisableAbleCommandHandler("react", react)
RHAPPY_HANDLER = DisableAbleCommandHandler("happy", rhappy)
RANGRY_HANDLER = DisableAbleCommandHandler("angry", rangry)
STATUS_HANDLER = DisableAbleCommandHandler("status", status)

dispatcher.add_handler(STATUS_HANDLER)
dispatcher.add_handler(REACT_HANDLER)
dispatcher.add_handler(RHAPPY_HANDLER)
dispatcher.add_handler(RANGRY_HANDLER)
dispatcher.add_handler(PING_HANDLER)
dispatcher.add_handler(GETLINK_HANDLER)
dispatcher.add_handler(LEAVECHAT_HANDLER)
dispatcher.add_handler(FORTUNE_HANDLER)
dispatcher.add_handler(TRANSLATE_HANDLER)
dispatcher.add_handler(WIKIPEDIA_HANDLER)
dispatcher.add_handler(UD_HANDLER)
dispatcher.add_handler(LOG_HANDLER)
