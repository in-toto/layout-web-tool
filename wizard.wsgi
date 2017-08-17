"""
<Program Name>
  wizard.wsgi

<Author>
  Lukas Puehringer <lukas.puehringer@nyu.edu>

<Started>
  April 06, 2017

<Copyright>
  See LICENSE for licensing information.

<Purpose>
  Sample WSGI file to serve Flask app with Apache, as suggested in
  http://flask.pocoo.org/docs/0.12/deploying/mod_wsgi/

  Note:
    Expects the app's dependencies to be installed in a virtualenv
    called `in-toto-layout` at below path.

"""

activate_this = "~/.virtualenvs/in-toto-layout/bin/activate_this.py"

# It seems like execfile does not expand ~
import os
activate_this = os.path.expanduser(activate_this)
execfile(activate_this, dict(__file__=activate_this))

# Flask app needs to be in the same directory as wsgi script or on PYTHONPATH
from wizard import app as application
