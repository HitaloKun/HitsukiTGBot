#    Hitsuki (A telegram bot project)

#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.

#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.

import rapidjson as json
from requests import get
from telethon import custom

from hitsuki.events import register
from hitsuki.modules.tr_engine.strings import tld

# orangefox: By @MrYacha, powered by OrangeFox API v2
# modified by @Hitalo on Telegram

API_HOST = 'https://api.orangefox.download/v2'


@register(pattern=r"^/(orangefox|of|fox|ofox)(?: |$)(\S*)")
async def orangefox(event):
    if event.sender_id is None:
        return

    chat_id = event.chat_id

    try:
        codename = event.pattern_match.group(2)
    except Exception:
        codename = ''

    if codename == '':
        reply_text = tld(chat_id, "fox_devices_title")

        devices = _send_request('device/releases/stable')
        for device in devices:
            reply_text += f"\n • {device['fullname']} (`{device['codename']}`)"

        reply_text += '\n\n' + tld(chat_id, "fox_get_release")
        await event.reply(reply_text)
        return

    device = _send_request(f'device/{codename}')
    if not device:
        reply_text = tld(chat_id, "fox_device_not_found")
        await event.reply(reply_text)
        return

    release = _send_request(f'device/{codename}/releases/stable/last')
    if not release:
        reply_text = tld(chat_id, "fox_release_not_found")
        await event.reply(reply_text)
        return

    reply_text = tld(chat_id, "fox_release_device").format(
        fullname=device['fullname'],
        codename=device['codename']
    )
    reply_text += tld(chat_id,
                      "fox_release_version").format(release['version'])
    reply_text += tld(chat_id, "fox_release_date").format(release['date'])
    reply_text += tld(chat_id, "fox_release_md5").format(release['md5'])

    if device['maintained'] == 3:
        status = tld(chat_id, "fox_release_maintained_3")
    else:
        status = tld(chat_id, "fox_release_maintained_1")

    reply_text += tld(chat_id, "fox_release_maintainer").format(
        name=device['maintainer']['name'],
        status=status
    )

    keyboard = [custom.Button.url(tld(chat_id, "btn_dl"), release['url'])]
    await event.reply(reply_text, buttons=keyboard, link_preview=False)
    return


def _send_request(endpoint):
    response = get(API_HOST + "/" + endpoint)
    if response.status_code == 404:
        return False

    return json.loads(response.text)
