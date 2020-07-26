import re
from typing import Optional

import telegram
from telegram import ParseMode, InlineKeyboardMarkup, Message, Chat
from telegram.error import BadRequest
from telegram.ext import CommandHandler, MessageHandler, DispatcherHandlerStop, run_async, Filters
from telegram.utils.helpers import escape_markdown, mention_markdown

from hitsuki import dispatcher, LOGGER, spamcheck, OWNER_ID
from hitsuki.modules.connection import connected
from hitsuki.modules.disable import DisableAbleCommandHandler
from hitsuki.modules.helper_funcs.alternate import send_message
from hitsuki.modules.helper_funcs.chat_status import user_admin
from hitsuki.modules.helper_funcs.extraction import extract_text
from hitsuki.modules.helper_funcs.filters import CustomFilters
from hitsuki.modules.helper_funcs.misc import build_keyboard_parser
from hitsuki.modules.helper_funcs.msg_types import get_filter_type
from hitsuki.modules.helper_funcs.string_handling import split_quotes, button_markdown_parser, \
    escape_invalid_curly_brackets
from hitsuki.modules.languages import tl
from hitsuki.modules.sql import cust_filters_sql as sql

HANDLER_GROUP = 10

ENUM_FUNC_MAP = {
    sql.Types.TEXT.value: dispatcher.bot.send_message,
    sql.Types.BUTTON_TEXT.value: dispatcher.bot.send_message,
    sql.Types.STICKER.value: dispatcher.bot.send_sticker,
    sql.Types.DOCUMENT.value: dispatcher.bot.send_document,
    sql.Types.PHOTO.value: dispatcher.bot.send_photo,
    sql.Types.AUDIO.value: dispatcher.bot.send_audio,
    sql.Types.VOICE.value: dispatcher.bot.send_voice,
    sql.Types.VIDEO.value: dispatcher.bot.send_video,
    sql.Types.VIDEO_NOTE.value: dispatcher.bot.send_video_note
}


@run_async
@spamcheck
def list_handlers(update, context):
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user

    conn = connected(context.bot, update, chat, user.id, need_admin=False)
    if conn is not False:
        chat_id = conn
        chat_name = dispatcher.bot.getChat(conn).title
        filter_list = "*Filter di {}:*\n"
    else:
        chat_id = update.effective_chat.id
        if chat.type == "private":
            chat_name = tl(update.effective_message, "filter lokal")
            filter_list = tl(update.effective_message, "*filter lokal:*\n")
        else:
            chat_name = chat.title
            filter_list = tl(update.effective_message, "*Filter di {}*:\n")

    all_handlers = sql.get_chat_triggers(chat_id)

    if not all_handlers:
        send_message(update.effective_message,
                     tl(update.effective_message, "Tidak ada filter di {}!").format(chat_name))
        return

    for keyword in all_handlers:
        entry = " - {}\n".format(escape_markdown(keyword))
        if len(entry) + len(filter_list) > telegram.MAX_MESSAGE_LENGTH:
            send_message(update.effective_message, filter_list.format(chat_name),
                         parse_mode=telegram.ParseMode.MARKDOWN)
            filter_list = entry
        else:
            filter_list += entry

    send_message(update.effective_message, filter_list.format(chat_name), parse_mode=telegram.ParseMode.MARKDOWN)


# NOT ASYNC BECAUSE DISPATCHER HANDLER RAISED
@spamcheck
@user_admin
def filters(update, context):
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user
    msg = update.effective_message  # type: Optional[Message]
    args = msg.text.split(None, 1)  # use python's maxsplit to separate Cmd, keyword, and reply_text

    conn = connected(context.bot, update, chat, user.id)
    if conn is not False:
        chat_id = conn
        chat_name = dispatcher.bot.getChat(conn).title
    else:
        chat_id = update.effective_chat.id
        if chat.type == "private":
            chat_name = tl(update.effective_message, "catatan lokal")
        else:
            chat_name = chat.title

    if not msg.reply_to_message and len(args) < 2:
        send_message(update.effective_message,
                     tl(update.effective_message, "Anda harus memberi nama untuk filter ini!"))
        return

    if msg.reply_to_message:
        if len(args) < 2:
            send_message(update.effective_message,
                         tl(update.effective_message, "Anda harus memberi nama untuk filter ini!"))
            return
        else:
            keyword = args[1]
    else:
        extracted = split_quotes(args[1])
        if len(extracted) < 1:
            return
        # set trigger -> lower, so as to avoid adding duplicate filters with different cases
        keyword = extracted[0].lower()

    # Add the filter
    # Note: perhaps handlers can be removed somehow using sql.get_chat_filters
    for handler in dispatcher.handlers.get(HANDLER_GROUP, []):
        if handler.filters == (keyword, chat_id):
            dispatcher.remove_handler(handler, HANDLER_GROUP)

    text, file_type, file_id = get_filter_type(msg)
    if not msg.reply_to_message and len(extracted) >= 2:
        offset = len(extracted[1]) - len(msg.text)  # set correct offset relative to command + notename
        text, buttons = button_markdown_parser(extracted[1], entities=msg.parse_entities(), offset=offset)
        text = text.strip()
        if not text:
            send_message(update.effective_message, tl(update.effective_message,
                                                      "Tidak ada pesan catatan - Anda tidak bisa HANYA menekan tombol, Anda perlu pesan untuk melakukannya!"))
            return

    elif msg.reply_to_message and len(args) >= 2:
        if msg.reply_to_message.text:
            text_to_parsing = msg.reply_to_message.text
        elif msg.reply_to_message.caption:
            text_to_parsing = msg.reply_to_message.caption
        else:
            text_to_parsing = ""
        offset = len(text_to_parsing)  # set correct offset relative to command + notename
        text, buttons = button_markdown_parser(text_to_parsing, entities=msg.parse_entities(), offset=offset)
        text = text.strip()

    elif not text and not file_type:
        send_message(update.effective_message,
                     tl(update.effective_message, "Anda harus memberi nama untuk filter ini!"))
        return

    elif msg.reply_to_message:
        if msg.reply_to_message.text:
            text_to_parsing = msg.reply_to_message.text
        elif msg.reply_to_message.caption:
            text_to_parsing = msg.reply_to_message.caption
        else:
            text_to_parsing = ""
        offset = len(text_to_parsing)  # set correct offset relative to command + notename
        text, buttons = button_markdown_parser(text_to_parsing, entities=msg.parse_entities(), offset=offset)
        text = text.strip()
        if (msg.reply_to_message.text or msg.reply_to_message.caption) and not text:
            send_message(update.effective_message, tl(update.effective_message,
                                                      "Tidak ada pesan catatan - Anda tidak bisa HANYA menekan tombol, Anda perlu pesan untuk melakukannya!"))
            return

    else:
        send_message(update.effective_message, tl(update.effective_message, "Invalid filter!"))
        return

    sql.new_add_filter(chat_id, keyword, text, file_type, file_id, buttons)

    send_message(update.effective_message,
                 tl(update.effective_message, "Handler '{}' ditambahkan di *{}*!").format(keyword, chat_name),
                 parse_mode=telegram.ParseMode.MARKDOWN)
    raise DispatcherHandlerStop


# NOT ASYNC BECAUSE DISPATCHER HANDLER RAISED
@spamcheck
@user_admin
def stop_filter(update, context):
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user
    args = update.effective_message.text.split(None, 1)

    conn = connected(context.bot, update, chat, user.id)
    if conn is not False:
        chat_id = conn
        chat_name = dispatcher.bot.getChat(conn).title
    else:
        chat_id = update.effective_chat.id
        if chat.type == "private":
            chat_name = tl(update.effective_message, "catatan lokal")
        else:
            chat_name = chat.title

    if len(args) < 2:
        send_message(update.effective_message, tl(update.effective_message, "Apa yang harus saya hentikan?"))
        return

    chat_filters = sql.get_chat_triggers(chat_id)

    if not chat_filters:
        send_message(update.effective_message, tl(update.effective_message, "Tidak ada filter aktif di sini!"))
        return

    for keyword in chat_filters:
        if keyword == args[1].lower():
            sql.remove_filter(chat_id, args[1].lower())
            send_message(update.effective_message,
                         tl(update.effective_message, "Ya, saya akan berhenti menjawabnya di *{}*.").format(chat_name),
                         parse_mode=telegram.ParseMode.MARKDOWN)
            raise DispatcherHandlerStop

    send_message(update.effective_message, "Itu bukan filter aktif - jalankan /filter untuk semua filter aktif.")


@run_async
def reply_filter(update, context):
    chat = update.effective_chat  # type: Optional[Chat]
    message = update.effective_message  # type: Optional[Message]

    if update.effective_user.id == 777000:
        return

    to_match = extract_text(message)
    if not to_match:
        return

    chat_filters = sql.get_chat_triggers(chat.id)
    for keyword in chat_filters:
        pattern = r"( |^|[^\w])" + re.escape(keyword) + r"( |$|[^\w])"
        if re.search(pattern, to_match, flags=re.IGNORECASE):
            filt = sql.get_filter(chat.id, keyword)
            if filt.reply == "there is should be a new reply":
                buttons = sql.get_buttons(chat.id, filt.keyword)
                keyb = build_keyboard_parser(context.bot, chat.id, buttons)
                keyboard = InlineKeyboardMarkup(keyb)

                VALID_WELCOME_FORMATTERS = ['first', 'last', 'fullname', 'username', 'id', 'chatname', 'mention']
                if filt.reply_text:
                    valid_format = escape_invalid_curly_brackets(filt.reply_text, VALID_WELCOME_FORMATTERS)
                    if valid_format:
                        filtext = valid_format.format(first=escape_markdown(message.from_user.first_name),
                                                      last=escape_markdown(
                                                          message.from_user.last_name or message.from_user.first_name),
                                                      fullname=escape_markdown(" ".join([message.from_user.first_name,
                                                                                         message.from_user.last_name] if message.from_user.last_name else [
                                                          message.from_user.first_name])),
                                                      username="@" + message.from_user.username if message.from_user.username else mention_markdown(
                                                          message.from_user.id, message.from_user.first_name),
                                                      mention=mention_markdown(message.from_user.id,
                                                                               message.from_user.first_name),
                                                      chatname=escape_markdown(
                                                          message.chat.title if message.chat.type != "private" else message.from_user.first_name),
                                                      id=message.from_user.id)
                    else:
                        filtext = ""
                else:
                    filtext = ""

                if filt.file_type in (sql.Types.BUTTON_TEXT, sql.Types.TEXT):
                    try:
                        context.bot.send_message(chat.id, filtext, reply_to_message_id=message.message_id,
                                                 parse_mode="markdown", disable_web_page_preview=True,
                                                 reply_markup=keyboard)
                    except BadRequest as excp:
                        error_catch = get_exception(excp, filt, chat)
                        if error_catch == "noreply":
                            try:
                                context.bot.send_message(chat.id, filtext, parse_mode="markdown",
                                                         disable_web_page_preview=True, reply_markup=keyboard)
                            except BadRequest as excp:
                                LOGGER.exception("Gagal mengirim pesan: ", excp.message)
                                send_message(update.effective_message,
                                             tl(update.effective_message, get_exception(excp, filt, chat)))
                                pass
                        else:
                            try:
                                send_message(update.effective_message,
                                             tl(update.effective_message, get_exception(excp, filt, chat)))
                            except BadRequest as excp:
                                LOGGER.exception("Gagal mengirim pesan: ", excp.message)
                                pass
                else:
                    ENUM_FUNC_MAP[filt.file_type](chat.id, filt.file_id, caption=filtext,
                                                  reply_to_message_id=message.message_id, parse_mode="markdown",
                                                  disable_web_page_preview=True, reply_markup=keyboard)
                break
            else:
                if filt.is_sticker:
                    message.reply_sticker(filt.reply)
                elif filt.is_document:
                    message.reply_document(filt.reply)
                elif filt.is_image:
                    message.reply_photo(filt.reply)
                elif filt.is_audio:
                    message.reply_audio(filt.reply)
                elif filt.is_voice:
                    message.reply_voice(filt.reply)
                elif filt.is_video:
                    message.reply_video(filt.reply)
                elif filt.has_markdown:
                    buttons = sql.get_buttons(chat.id, filt.keyword)
                    keyb = build_keyboard_parser(context.bot, chat.id, buttons)
                    keyboard = InlineKeyboardMarkup(keyb)

                    try:
                        send_message(update.effective_message, filt.reply, parse_mode=ParseMode.MARKDOWN,
                                     disable_web_page_preview=True,
                                     reply_markup=keyboard)
                    except BadRequest as excp:
                        if excp.message == "Unsupported url protocol":
                            try:
                                send_message(update.effective_message, tl(update.effective_message,
                                                                          "Anda tampaknya mencoba menggunakan protokol url yang tidak didukung. Telegram "
                                                                          "tidak mendukung tombol untuk beberapa protokol, seperti tg://. Silakan coba "
                                                                          "lagi."))
                            except BadRequest as excp:
                                LOGGER.exception("Gagal mengirim pesan: ", excp.message)
                                pass
                        elif excp.message == "Reply message not found":
                            try:
                                context.bot.send_message(chat.id, filt.reply, parse_mode=ParseMode.MARKDOWN,
                                                         disable_web_page_preview=True,
                                                         reply_markup=keyboard)
                            except BadRequest as excp:
                                LOGGER.exception("Gagal mengirim pesan: ", excp.message)
                                pass
                        else:
                            try:
                                send_message(update.effective_message, tl(update.effective_message,
                                                                          "Catatan ini tidak dapat dikirim karena formatnya salah."))
                            except BadRequest as excp:
                                LOGGER.exception("Gagal mengirim pesan: ", excp.message)
                                pass
                            LOGGER.warning("Message %s could not be parsed", str(filt.reply))
                            LOGGER.exception("Could not parse filter %s in chat %s", str(filt.keyword), str(chat.id))

                else:
                    # LEGACY - all new filters will have has_markdown set to True.
                    try:
                        send_message(update.effective_message, filt.reply)
                    except BadRequest as excp:
                        LOGGER.exception("Gagal mengirim pesan: ", excp.message)
                        pass
                break


def get_exception(excp, filt, chat):
    if excp.message == "Unsupported url protocol":
        return "Anda tampaknya mencoba menggunakan protokol url yang tidak didukung. Telegram tidak mendukung tombol untuk beberapa protokol, seperti tg://. Silakan coba lagi."
    elif excp.message == "Reply message not found":
        return "noreply"
    else:
        LOGGER.warning("Message %s could not be parsed", str(filt.reply))
        LOGGER.exception("Could not parse filter %s in chat %s", str(filt.keyword), str(chat.id))
        return "Catatan ini tidak dapat dikirim karena formatnya salah."


@run_async
@spamcheck
@user_admin
def stop_all_filters(update, context):
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message

    if chat.type == "private":
        chat.title = tl(chat.id, "local filters")
    else:
        owner = chat.get_member(user.id)
        chat.title = chat.title
        if owner.status != 'creator':
            message.reply_text(tl(chat.id, "You must be this chat creator."))
            return

    x = 0
    flist = sql.get_chat_triggers(chat.id)

    if not flist:
        message.reply_text(
            tl(chat.id, "There aren't any active filters in {}!").format(chat.title))
        return

    f_flist = []
    for f in flist:
        x += 1
        f_flist.append(f)

    for fx in f_flist:
        sql.remove_filter(chat.id, fx)

    message.reply_text(tl(chat.id, "{} filters from this chat have been removed.").format(x))


def __stats__():
    return tl(OWNER_ID, "`{}` filters, across `{}` chats.").format(sql.num_filters(), sql.num_chats())


def __import_data__(chat_id, data):
    # set chat filters
    filters = data.get('filters', {})
    for trigger in filters:
        sql.add_to_blacklist(chat_id, trigger)


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


def __chat_settings__(chat_id, user_id):
    cust_filters = sql.get_chat_triggers(chat_id)
    return tl(user_id, "There are `{}` custom filters here.").format(len(cust_filters))


__help__ = "filters_help"

__mod_name__ = "Filters"

FILTER_HANDLER = CommandHandler("filter", filters)
STOP_HANDLER = CommandHandler("stop", stop_filter)
STOPALL_HANDLER = DisableAbleCommandHandler("stopall", stop_all_filters)
LIST_HANDLER = DisableAbleCommandHandler("filters", list_handlers, admin_ok=True)
CUST_FILTER_HANDLER = MessageHandler(CustomFilters.has_text & ~Filters.update.edited_message, reply_filter)

dispatcher.add_handler(FILTER_HANDLER)
dispatcher.add_handler(STOP_HANDLER)
dispatcher.add_handler(STOPALL_HANDLER)
dispatcher.add_handler(LIST_HANDLER)
dispatcher.add_handler(CUST_FILTER_HANDLER, HANDLER_GROUP)
