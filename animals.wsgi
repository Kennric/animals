import animals

application = animals.create_app()

activate_this = '/var/www/animals.hypothetical.net/venv/bin/activate_this.py'
execfile(activate_this, dict(__file__=activate_this))

import sys
sys.path.insert(0, '/var/www/animals.hypothetical.net')
