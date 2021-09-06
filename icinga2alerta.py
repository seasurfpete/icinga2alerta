# Send your Icinga2 alerts to alerta (alerta.io)
# Copyright (C) 2021 Pete Smith
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import click
import json
import logging
import pathlib
import requests
import uuid
from pydantic import BaseModel
from typing import List
import os
from datetime import datetime

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)
logging.getLogger('requests').setLevel(logging.INFO)
log_file = open('/tmp/alerta.log', 'a')

CONFIG = {}

try:
    CONFIG_FILE = open('/etc/icinga2/icinga2alerta.json')
    CONFIG = json.loads(CONFIG_FILE.read())
    print('loaded config')
except Exception as err:
    logging.error(f'Error loading config file {err}')
    quit(1)

SPOOL = '/tmp/icinga2telegram/spool'
pathlib.Path(SPOOL).mkdir(parents=True, exist_ok=True)

icinga2client = None


class Alert(BaseModel):
    id: str = None
    attributes: dict = {"region": "AU"}
    correlate: List = []
    environment: str = 'dev'
    event: str = "httpIp"
    group: str = "Web"
    origin: str = "unknown"
    resource: str = "web01"
    service: List = ["example.com"]
    severity: str = "major"
    tags: List = ["tag"]
    text: str = 'None'
    type: str = 'Icinga2Alert'
    value: str = 'aval'
    timeout: int = 3600
    rawData: str = None
    note: str = "test"


severity_mapping = {
    "Up": "ok",
    "OK": "ok",
    "Down": "critical",
    "DOWN": "critical",
    "Critical": "critical",
    "CRITICAL": "critical",
    "Warning": "warning",
    "WARNING": "warning",
    "Unknown": "minor",
    "UNKNOWN": "minor",
    "UNREACHABLE": "minor",
}
# rcIUKhXXKi8YCVYFzPRtMv5U0WyBpJ5_ugnfI6MP

# ALERTA_API_KEY = "_ezEfniz-WYrDVMBDZpOyPOwOeTqPdEAPpV30iWQ"

ALERTA_API_HOST = CONFIG.get("ALERTA_API_HOST", os.environ.get("ALERTA_API_HOST", "http://m.origin.foxtel.com.au:8080/api/alert"))
ALERTA_API_KEY = CONFIG.get("ALERTA_API_KEY", os.environ.get("ALERTA_API_KEY", "_ezEfniz-WYrDVMBDZpOyPOwOeTqPdEAPpV30iWQ"))
ALERTA_ENVIRONMENT = CONFIG.get("ALERTA_ENVIRONMENT", os.environ.get("ALERTA_ENVIRONMENT", "dev"))

headers = {"Authorization": f"Key {ALERTA_API_KEY}",
           "Content-type": "application/json"}


def delete_alert_from_alerta(alert_id):
    r = requests.delete(f'{ALERTA_API_HOST}/{alert_id}', headers=headers)


def add_note_to_alert(alert: Alert, note: str):
    data = {"note": f"{note}"}
    c = requests.post(f"{ALERTA_API_HOST}", json=alert.dict(), headers=headers).json()
    r = requests.put(f'{ALERTA_API_HOST}/{c["id"]}/note', data=json.dumps(data), headers=headers)
    return r


def add_note_to_alert_id(alert_id, note: str):
    data = {"note": f"{note}"}
    r = requests.put(f'{ALERTA_API_HOST}/{alert_id}/note', data=json.dumps(data), headers=headers)
    return r


def reopen_alert(alert_id, action: str = 'open'):
    data = {"action": f"{action}", "text": f"{action.upper()} from icinga2", "timeout": 7200}
    r = requests.put(f'{ALERTA_API_HOST}/{alert_id}/action', data=json.dumps(data), headers=headers)
    return r


def ack_alert(alert: Alert, action: str = 'ack', note: str = 'no ack note'):
    data = {"action": f"{action}", "text": f"{action.upper()} from icinga2", "timeout": 7200}
    c = create_alert(alert).json()
    r = requests.put(f'{ALERTA_API_HOST}/{c["id"]}/action', data=json.dumps(data), headers=headers)
    add_note_to_alert_id(c['id'], f'ACK: {note}')
    return r


def unack_alert(alert_id, action: str = 'unack'):
    data = {"action": f"{action}", "text": f"{action.upper()} from icinga2", "timeout": 7200}
    r = requests.put(f'{ALERTA_API_HOST}/{alert_id}/action', data=json.dumps(data), headers=headers)
    return r


def shelve_alert(alert_id, action: str = 'shelve'):
    data = {"action": f"{action}", "text": f"{action.upper()} from icinga2", "timeout": 7200}
    r = requests.put(f'{ALERTA_API_HOST}/{alert_id}/action', data=json.dumps(data), headers=headers)
    return r


def unshelve_alert(alert_id, action: str = 'unshelve'):
    data = {"action": f"{action}", "text": f"{action.upper()} from icinga2", "timeout": 7200}
    r = requests.put(f'{ALERTA_API_HOST}/{alert_id}/action', data=json.dumps(data), headers=headers)
    return r


def close_alert(alert_id, action: str = 'close'):
    data = {"action": f"{action}", "text": f"{action.upper()} from icinga2", "timeout": 7200}
    r = requests.put(f'{ALERTA_API_HOST}/{alert_id}/action', data=json.dumps(data), headers=headers)
    return r


def create_alert(alert: Alert):
    r = requests.post(f"{ALERTA_API_HOST}", json=alert.dict(), headers=headers)
    log_file.write(f'Create Response {r.status_code} {r.text}')
    return r


def acknowledge_host(hostname, author):
    """
    Acknowledge a host alert.
    :param hostname: The hostname.
    :param author: The author.
    """
    print('ack host')
    icinga2client.actions.acknowledge_problem(object_type='Host',
                                              filters='host.name == "{}"'.format(hostname),
                                              author=author,
                                              comment='ACK via icinga2telegram',
                                              sticky=False,
                                              notify=True)


def acknowledge_service(hostname, servicename, author):
    """
    Acknowledge a service alert.
    :param hostname: The hostname.
    :param servicename: The servicename.
    :param author: The author.
    """
    print('ack_service')
    icinga2client.actions.acknowledge_problem(object_type='Service',
                                              filters='host.name == "{}" && service.name "{}"'.format(hostname,
                                                                                                      servicename),
                                              author=author,
                                              comment='ACK via icinga2telegram',
                                              sticky=False,
                                              notify=True)


def handler_start(bot, update):
    """Telegram command handler for /start and /whoami. Sends the chat ID to the user."""
    logging.debug('{}: start/whois handler'.format(update.message.chat_id))
    # bot.send_message(chat_id=update.message.chat_id, text='Your chat ID is: {}'.format(update.message.chat_id))


def handler_acknowledge(_, update):
    """Telegram query handler to acknowledge an alert."""
    logging.debug('{}: acknowledge handler for message {}'.format(update.callback_query.message.chat_id,
                                                                  update.callback_query.data))
    try:

        print(f'do handler_ack {_} {update}')
        # spool_file_path = '{}/{}-{}.json'.format(SPOOL,update.callback_query.message.chat_id, update.callback_query.data)
        #
        # with open(spool_file_path, 'r') as spool_file:
        #     logging.debug('{}: Reading message from {}'.format(update.callback_query.message.chat_id, spool_file_path))
        #     spool_content = json.load(spool_file)
        #
        # if 'servicename' in spool_content:
        #     acknowledge_service(spool_content['hostname'], spool_content['servicename'], update.callback_query.from_user.mention_markdown())
        # else:
        #     acknowledge_host(spool_content['hostname'], update.callback_query.from_user.mention_markdown())
        #
        # update.callback_query.message.edit_text(update.callback_query.message.text_markdown,
        #                                         parse_mode = telegram.ParseMode.MARKDOWN,
        #                                         disable_web_page_preview = True)
        # pathlib.Path(spool_file_path).unlink()
    except Exception as e:
        logging.error('Unable to acknowledge the alert: {}'.format(e))
        # update.callback_query.answer(text='Unable to acknowledge the alert. Please use icingaweb2 instead.')


@click.group()
def cli():
    pass


@cli.command()
@click.option('--token', required=True, help='API token of the Telegram bot')
@click.option('--icinga2-cacert', help='CA certificate of your Icinga2 API')
@click.option('--icinga2-api-url', required=True, help='Icinga2 API URL/')
@click.option('--icinga2-api-user', required=True, help='Icinga2 API user')
@click.option('--icinga2-api-password', required=True, help='Icinga2 API password')
def daemon(token, icinga2_cacert, icinga2_api_url, icinga2_api_user, icinga2_api_password):
    global icinga2client
    try:
        import icinga2api.client
    except ImportError:
        import sys
        logging.error(
            'If you want to run icinga2alerta as a daemon to handle acknowledgements you need to install icinga2api.')
        sys.exit(1)
    icinga2client = icinga2api.client.Client(url=icinga2_api_url,
                                             username=icinga2_api_user,
                                             password=icinga2_api_password,
                                             ca_certificate=icinga2_cacert)

    # updater = Updater(token=token)
    # dispatcher = updater.dispatcher
    # dispatcher.add_handler(CommandHandler('start', handler_start))
    # dispatcher.add_handler(CommandHandler('whoami', handler_start))
    # dispatcher.add_handler(CallbackQueryHandler(handler_acknowledge))
    # updater.start_polling()
    # updater.idle()


@cli.command()
@click.option('--token', required=True, help='API of Alerta')
@click.option('--time', required=True, type=click.INT, help='Time of the event as a UNIX timestamp')
@click.option('--hostname', required=True)
@click.option('--hostdisplayname')
@click.option('--hostoutput')
@click.option('--hoststate', required=True, type=click.Choice(['UP', 'DOWN']))
@click.option('--address', required=True)
@click.option('--address6')
@click.option('--servicename')
@click.option('--servicedisplayname')
@click.option('--serviceoutput')
@click.option('--max-attempts')
@click.option('--attempts')
@click.option('--state-type', type=click.Choice(['SOFT', 'HARD']))
@click.option('--servicestate', type=click.Choice(['OK', 'WARNING', 'CRITICAL', 'UNKNOWN']))
@click.option('--notification-type', required=True, type=click.Choice(
    ['ACKNOWLEDGEMENT', 'CUSTOM', 'DOWNTIMEEND', 'DOWNTIMEREMOVED', 'DOWNTIMESTART', 'FLAPPINGEND', 'FLAPPINGSTART',
     'PROBLEM', 'RECOVERY']))
@click.option('--notification-author')
@click.option('--notification-comment')
@click.option('--icingaweb2url', required=True)
@click.option('--ack/--no-ack', default=False,
              help='Enable or disable the acknowledgement button for alerts. (Disabled by default.)')
@click.option('--vars')
@click.option('--groups')
def notification(token, time,
                 hostname, hostdisplayname, hostoutput, hoststate, address, address6,
                 servicename, servicedisplayname, serviceoutput, servicestate, state_type, max_attempts,
                 notification_type, notification_author, notification_comment, icingaweb2url, ack, attempts, vars, groups):

    hostdisplayname = hostname if hostdisplayname is None else hostdisplayname
    time_human = datetime.fromtimestamp(time).isoformat()

    # Create an alertID from the hostname.servicename so we can always find it to delete it etc.
    # alert_id = str(uuid.uuid3(uuid.NAMESPACE_DNS, f'{hostdisplayname}.{servicename}'))
    alert = Alert(
                  resource=address,
                  event=f'{servicename}',
                  service=[servicename],
                  severity=severity_mapping.get(servicestate),
                  correlate=[servicename],
                  value=f'{attempts}/{max_attempts} ({state_type})',
                  text=f'{notification_type} {serviceoutput}',
                  group=servicename,
                  environment=ALERTA_ENVIRONMENT,
                  origin=icingaweb2url)
    alert.rawData = alert.json()
    alert.attributes["moreInfo"] = f"<a href=\"{icingaweb2url}/icingaweb2/dashboard#!/icingaweb2/monitoring/service/show?host={hostname}&service={servicename}\">Incinga GUI</a>"
    apihost: str = icingaweb2url.replace('http', 'https')
    alert.attributes['externalURL'] = f'{apihost}:5561'

    log_file.write(f' GOT {token}, {time}, {hostname}, {hostdisplayname}, {hostoutput}, {hoststate}, {address}, {address6}, \
    {servicename}, {servicedisplayname}, {serviceoutput}, {servicestate}, {state_type}, {max_attempts}, \
    {notification_type}, {notification_author}, {notification_comment}, {icingaweb2url}, {ack}, {attempts}, {vars}, \
    {groups}')

    if notification_type == "ACKNOWLEDGEMENT":
        # alert was ack'd in icinga, ack in alerta
        ack_alert(alert, note=f'remote ack from {alert.origin}: {notification_author}: {notification_comment}')

    elif notification_type == "CUSTOM":
        add_note_to_alert(alert, f'{notification_author}: {notification_comment}')

    else:
        # to close we can send a status of ok, this seems to work as we need to match an id from the values
        create_alert(alert)

    log_file.close()



# todo: add raw data
#       add tags and align fields
#       configurable settings
#


