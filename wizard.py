# -*- coding: utf-8 -*-
#!/usr/bin/env python

"""
<Program Name>
  wizard.py

<Author>
  Lukas Puehringer <lukas.puehringer@nyu.edu>

<Started>
  April 06, 2017

<Copyright>
  See LICENSE for licensing information.

<Purpose>
  Flask web app that provides a wizard to guide through an in-toto
  software supply chain layout creation.

"""



from flask import (Flask, render_template, session, redirect, url_for, request,
    flash, send_from_directory, abort, jsonify)

app = Flask(__name__, static_url_path="", instance_relative_config=True)

app.config.update(dict(
    DEBUG=True,
    SECRET_KEY="do not use the development key in production!!!"
))

# Supply a config file at "instance/config.py" that carries
# e.g. your deployment secret key
app.config.from_pyfile("config.py")


if __name__ == "__main__":
  app.run()
