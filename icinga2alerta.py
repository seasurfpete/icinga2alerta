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
    "UP": "ok",
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

@cli.command()
@click.option('--token', required=True, help='API of Alerta')
@click.option('--time', required=True, type=click.INT, help='Time of the event as a UNIX timestamp')
@click.option('--alerttype', required=True, type=click.Choice(["host", "service"]))
@click.option('--hostname', required=True)
@click.option('--hostdisplayname')
@click.option('--hostoutput')
@click.option('--hoststate', required=True)
@click.option('--resource', required=True)
@click.option('--address6')
@click.option('--event')
@click.option('--service')
@click.option('--servicedisplayname')
@click.option('--text')
@click.option('--max-attempts')
@click.option('--attempts')
@click.option('--state-type', type=click.Choice(['SOFT', 'HARD']))
@click.option('--severity')
@click.option('--environment', default=ALERTA_ENVIRONMENT)
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
                 hostname, hostdisplayname, hostoutput, hoststate, resource, address6, alerttype,
                 event, servicedisplayname, text, severity, state_type, max_attempts, service, environment,
                 notification_type, notification_author, notification_comment, icingaweb2url, ack, attempts, vars, groups):

    hostdisplayname = hostname if hostdisplayname is None else hostdisplayname
    time_human = datetime.fromtimestamp(time).isoformat()

    # Create an alertID from the hostname.servicename so we can always find it to delete it etc.
    # alert_id = str(uuid.uuid3(uuid.NAMESPACE_DNS, f'{hostdisplayname}.{servicename}'))

    alert = Alert(
                  resource=resource,
                  event=f'{event}',
                  service=[service],
                  severity=severity_mapping.get(severity) or 'warning',
                  correlate=[event],
                  value=f'{attempts}/{max_attempts} ({state_type})',
                  text=f'{notification_type} {text}',
                  group=resource,
                  environment=environment,
                  origin=icingaweb2url)
    alert.rawData = alert.json()
    alert.attributes["moreInfo"] = f"<a href=\"{icingaweb2url}/icingaweb2/dashboard#!/icingaweb2/monitoring/service/show?host={hostname}&service={service}\">Incinga GUI</a>"
    apihost: str = icingaweb2url.replace('http', 'https')
    alert.attributes['externalUrl'] = f'{apihost}:5665'
    alert.attributes['alertType'] = alerttype
    log_file.write(f' VARS={vars}')
    log_file.write(f' GOT toek={token}, time={time}, hostname={hostname}, hostdisplayname={hostdisplayname}, hostoutput={hostoutput}, hoststate={hoststate}, resource={resource}, '
                   f'address={address6}, \
    event={event}, servicedisplayname={servicedisplayname}, text={text}, severity={severity}, state_type={state_type}, max_attempts={max_attempts}, env={environment},\
    notification_type={notification_type}, notification_author={notification_author}, notification_comment={notification_comment}, icinga2url={icingaweb2url}, ack={ack}, attempts={attempts}, '
                   f'{vars}, \
    groups={groups}')

    if notification_type == "ACKNOWLEDGEMENT":
        # alert was ack'd in icinga, ack in alerta
        ack_alert(alert, note=f'remote ack from {alert.origin}: {notification_author}: {notification_comment}')

    elif notification_type == "CUSTOM":
        add_note_to_alert(alert, f'{notification_author}: {notification_comment}')

    elif notification_type == "RECOVERY":
        close_alert(alert)

    else:
        # to close we can send a status of ok, this seems to work as we need to match an id from the values
        create_alert(alert)

    log_file.close()



# todo: add raw data
#       add tags and align fields
#       configurable settings
#
