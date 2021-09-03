# icinga2alerta

icinga2alerta is a small Python script to send your [Icinga2](https://icinga.com) alerts to
an Alerta.io server.

This script is based on the work of icinga2telegram (link). Thanks for the starting point.

## Why Python instead of a simple Bash script?
Several other people implemented Icinga2-Telegram notifications by writing a simple Bash
script. Most of the time this works but there are a few things I do not like about the
Bash solutions:

1. They use two scripts with almost the same content.
2. Bash can screw up really bad when your alert output contains special characters.
3. The Bash solutions are based on environment variables. This does not work natively with
Icinga2 director as it only supports arguments in command definitions.

Obviously the Python implementation has a bigger footprint than the Bash solution. It
requires a Python interpreter and installs several Python packages as dependencies. This
could be a problem for an embedded system with very limited resources but most Icinga2
instances run on powerful machines and the icinga2telegram footprint does not matter there.
In return you get a single maintainable and robust script that you can use for host and
service notifications.

## Installation and Setup

1. create api-key in alerta server
2. copy alerta-notification-command.conf into icinga2 conf dir ```/etc/icinga2/conf.d ir /values.d/global something```
3. copy icinga2alerta.json to /etc/icinga2/
3. copy the other conf file bits over too. adjust for user
4. clone this repo onto your server, install python 3 and run ```pip3 install .``` 

## Supported Features
    create alert
    resolve alert
    

## License
```
Send your Icinga2 alerts to Alerta
Copyright (C) 2021 Pete Smith

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
```
