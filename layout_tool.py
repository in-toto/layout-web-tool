# -*- coding: utf-8 -*-
#!/usr/bin/env python

"""
<Program Name>
  layout_tool.py

<Author>
  Lukas Puehringer <lukas.puehringer@nyu.edu>

<Started>
  February 10, 2017

<Copyright>
  See LICENSE for licensing information.

<Purpose>
  Provides a simple web app to create, visualize and modify in-toto
  software supply chain layouts.

"""
import os
import sys
import hashlib
import random
import urllib

import in_toto.models.layout

from flask import Flask, render_template, session, redirect, url_for, request
from werkzeug.routing import BaseConverter, ValidationError


app = Flask(__name__)

app.config.update(dict(
    DEBUG=True,
    SECRET_KEY="do not use the development key in production!!!",
    SESSIONS_DIR=os.path.join(os.path.dirname(os.path.abspath(__file__)), "sessions")
))

def _session_path(session_id):
  return os.path.join(app.config["SESSIONS_DIR"], session_id)

@app.route("/")
def index():
  """
  <Purpose>
    Index page for layout creation tool.
    If it is a new session we create a session id -- md5 hexdigest of random
    value -- and a directory for this session, which will be used to store
    layout files.

    Redirect to show layout view with session path.

  <Side Effects>
    Creates session directory if the session is new

  <Returns>
    Redirects to session view

  """

  # Redirect to existing or new session page
  if not session.get("id"):
    # Sessions use a MD5 hexdigest of a random value
    # Security is not paramount, because we don't store sensitive data, right?
    session["id"] = hashlib.md5(str(random.random())).hexdigest()
    app.logger.debug("New session '{}'".format(session["id"]))

    # Create new session directory where we store the layout
    session_path = _session_path(session["id"])
    app.logger.debug("Create session directory '{}'".format(session_path))

    try:
      os.mkdir(session_path)
    except Exception as e:
      app.logger.error("Could not create session directory '{0}' - {1}"
          .format(session_path, e))

  return redirect(url_for("show_layout", session_id=session["id"]))


@app.route("/<session_id>", methods=['GET'])
def show_layout(session_id):
  """
  <Purpose>
    Renders layout page.

    The layout page presents a selection list of files in the session
    directory, so that the user can chose a layout to show.

    If a layout_name was specified as urlencoded GET parameter show_layout
    loads the layout file as in-toto Layout object and passes it to the
    template to display all parameters.

  <Returns>
    Renders layout page

  """

  # Override session, if someone calls a session url explicitly
  session["id"] = session_id
  session_path = _session_path(session_id)

  layout = None
  layout_name = None

  if request.args.get("layout_name"):
    layout_name = urllib.unquote(request.args.get("layout_name"))

  # Assume that all files in the session directory are layouts
  # and let the user choose one of them
  layout_choices = os.listdir(session_path)

  # If the user has already chosen, passed a layout_name as get parameter
  # we try to load that layout
  if layout_name:
    layout_path = os.path.join(session_path, layout_name)
    try:
      layout = in_toto.models.layout.Layout.read_from_file(layout_path)
    except Exception as e:
      app.logger.error("Could not read layout '{0}' - {1}"
          .format(layout_path, e))

  return render_template("index.html",
      session_id=session_id, layout=layout, layout_choices=layout_choices,
      layout_name=layout_name)


if __name__ == "__main__":
  app.run()