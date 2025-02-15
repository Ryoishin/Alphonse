

from alphonsebot import BRAIN, HELP, SPAMWATCH_KEY
from alphonseecem.core import get_translation, is_admin_myself, reply, alphonseify, send_log
from spamwatch import Client as SpamWatch


class SWClient:
    spamwatch_client = SpamWatch(SPAMWATCH_KEY) if SPAMWATCH_KEY else None


@alphonseify(compat=False, outgoing=False, incoming=True, disable_notify=True, disable_edited=True)
def spamwatch_action(client, message):
    if not SWClient.spamwatch_client:
        message.continue_propagation()

    uid = message.from_user.id
    if uid in BRAIN:
        message.continue_propagation()

    ban_status = SWClient.spamwatch_client.get_ban(uid)
    if not ban_status:
        message.continue_propagation()

    if is_admin_myself(message.chat):
        text = get_translation('spamWatchBan', [message.from_user.first_name, uid])

        if 'private' == message.chat.type:
            reply(message, text)
            client.block_user(uid)
        else:
            myself = message.chat.get_member('me')
            if myself.can_restrict_members:
                message.chat.kick_member(uid)
                reply(message, text)
            else:
                return

        send_log(text)

HELP.update({'spamwatch': get_translation('spamWatchInfo')})
