python -m venv venv
. venv/bin/activate
pip install PyQt5
pip install PyGObject
pip install mutagen
pip install Unidecode
pip install bidict
pip install systemd-python
pip install pydantic
pip install ctypesgen
echo export PYTHONPATH=$${VIRTUAL_ENV%/venv}/src >> venv/bin/activate
echo exec python -m tandamaster $$@ > venv/bin/tandamaster
chmod +x venv/bin/tandamaster
