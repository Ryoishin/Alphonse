

from io import BytesIO
from re import IGNORECASE, escape, search

from alphonsebot import HELP, LOGS
from alphonseecem.core import (
    edit,
    extract_args,
    get_translation,
    reply,
    reply_doc,
    alphonseify,
    send_log,
)


def blacklist_init():
    try:
        global sql
        from importlib import import_module

        sql = import_module('alphonseecem.sql.blacklist_sql')
    except Exception as e:
        sql = None
        LOGS.warn(get_translation('blacklistSqlLog'))
        raise e


blacklist_init()


@alphonseify(incoming=True, outgoing=False)
def blacklist(message):
    if message.from_user and message.from_user.is_self:
        message.continue_propagation()

    if not sql:
        message.continue_propagation()

    name = message.text
    if not name:
        message.continue_propagation()

    snips = None
    try:
        snips = sql.get_chat_blacklist(message.chat.id)
    except BaseException:
        message.continue_propagation()

    msg_removed = False
    for snip in snips:
        regex1 = r'( |^|[^\w])'
        regex2 = r'( |$|[^\w])'
        pattern = f"{regex1}{escape(snip)}{regex2}"
        if search(pattern, name, flags=IGNORECASE):
            try:
                message.delete()
                msg_removed = True
            except Exception:
                reply(message, f'`{get_translation("blacklistPermission")}`')
                sql.rm_from_blacklist(message.chat.id, snip.lower())
            break

    if not msg_removed:
        message.continue_propagation()


@alphonseify(pattern='^.addblacklist')
def addblacklist(message):
    if not sql:
        edit(message, f'`{get_translation("nonSqlMode")}`')
        return
    text = extract_args(message)
    if len(text) < 1:
        edit(message, f'`{get_translation("blacklistText")}`')
        return
    to_blacklist = list(
        set(trigger.strip() for trigger in text.split("\n") if trigger.strip())
    )
    for trigger in to_blacklist:
        sql.add_to_blacklist(message.chat.id, trigger.lower())
    edit(message, get_translation('blacklistAddSuccess', ['**', '`', text]))

    send_log(get_translation('blacklistLog', ['`', message.chat.id, text]))


@alphonseify(pattern='^.showblacklist$')
def showblacklist(message):
    if not sql:
        edit(message, f'`{get_translation("nonSqlMode")}`')
        return
    all_blacklisted = sql.get_chat_blacklist(message.chat.id)
    OUT_STR = f'**{get_translation("blacklistChats")}**\n'
    if len(all_blacklisted) > 0:
        for trigger in all_blacklisted:
            OUT_STR += f'`{trigger}`\n'
    else:
        OUT_STR = f'**{get_translation("blankBlacklist")}**'
    if len(OUT_STR) > 4096:
        with BytesIO(str.encode(OUT_STR)) as out_file:
            out_file.name = 'blacklist.text'
            reply_doc(
                message, out_file, caption=f'**{get_translation("blacklistChats")}**'
            )
            message.delete()
    else:
        edit(message, OUT_STR)


@alphonseify(pattern='^.rmblacklist')
def rmblacklist(message):
    if not sql:
        edit(message, f'`{get_translation("nonSqlMode")}`')
        return
    text = extract_args(message)
    if len(text) < 1:
        edit(message, f'`{get_translation("blacklistText")}`')
        return
    to_unblacklist = list(
        set(trigger.strip() for trigger in text.split("\n") if trigger.strip())
    )
    successful = 0
    for trigger in to_unblacklist:
        if sql.rm_from_blacklist(message.chat.id, trigger.lower()):
            successful += 1
    edit(message, get_translation('blacklistRemoveSuccess', ['**', '`', text]))


HELP.update({'blacklist': get_translation('blacklistInfo')})
