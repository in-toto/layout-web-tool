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
from sassutils.wsgi import SassMiddleware

app = Flask(__name__, static_url_path="", instance_relative_config=True)

# Automatically compile scss on each request
app.wsgi_app = SassMiddleware(app.wsgi_app, {
    app.name: ('static/scss', 'static/css', '/css')
})

app.config.update(dict(
    DEBUG=True,
    SECRET_KEY="do not use the development key in production!!!"
))

# Supply a config file at "instance/config.py" that carries
# e.g. your deployment secret key
app.config.from_pyfile("config.py")

@app.route("/")
def start():
  """Step 0.
  Wizard entry point, static landing page. """
  return render_template("start.html")


@app.route("/versioning")
def versioning():
  """Step 1.
  Enter information about version control system. """
  return render_template("versioning.html")


@app.route("/building")
def building():
  """Step 2.
  Enter information about building. """
  return render_template("building.html")


@app.route("/quality")
def quality_management():
  """Step 3.
  Enter information about quality management. """
  return render_template("quality.html")


@app.route("/packaging")
def packaging():
  """Step 4.
  Enter information about packaging. """
  return render_template("packaging.html")


@app.route("/software-supply-chain")
def software_supply_chain():
  """Step 5.
  Visualize and edit software supply chain. """
  return render_template("software_supply_chain.html")


@app.route("/authorizing")
def authorizing():
  """Step 6.
  Functionary keys upload and keys dropzone. """
  return render_template("authorizing.html")


@app.route("/authorizing/upload")
def ajax_upload_key():
  """Ajax upload functionary keys. """
  pass


@app.route("/chaining")
def chaining():
  """Step 7.
  Dry run snippet and link metadata upload. """
  return render_template("chaining.html")


@app.route("/chaining/upload")
def ajax_upload_link():
  """Ajax upload link metadata. """
  pass


@app.route("/wrap-up")
def wrap_up():
  """Step 8.
  Explain what to do with generated layout.
   - Download layout
   - Create project owner key (keygen snippet)
   - Sign layout (signing snippet)
   - Per functionary commands (in-toto-run snippet)
   - Release instructions ??
  """
  return render_template("wrap_up.html")


@app.route("/guarantees")
def guarantees():
  """ Show what the software supply chain protects against and give advice for
  more guarantees. """
  return render_template("guarantees.html")

if __name__ == "__main__":
  app.run()
