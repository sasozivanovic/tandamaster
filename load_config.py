class Config:
    pass
config = Config()

import fileinput
_configstr = ''
with fileinput.input(files = 'config.py') as f:
    for line in f:
        _configstr += line
exec(_configstr)
