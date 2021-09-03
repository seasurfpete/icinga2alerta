from setuptools import setup

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name='icinga2alerta',
    version='0.0.1',
    author='Pete Smith',
    url='https://github.com/seasurfpete/icinga2alerta',
    author_email='seasurfpete@gmail.com',
    description='Send your Icinga2 alerts to Alerta',
    long_description=long_description,
    long_description_content_type='text/markdown',
    license='LICENSE',
    py_modules=['icinga2alerta'],
    install_requires=[
        'Click',
        'alerta',
        'pydantic',
    ],
    entry_points='''
        [console_scripts]
        icinga2alerta=icinga2alerta:cli
    ''',
)
