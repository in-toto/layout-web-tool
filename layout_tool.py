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

from flask import (Flask, render_template, session, redirect, url_for, request,
    flash)
from werkzeug.routing import BaseConverter, ValidationError
from werkzeug.utils import secure_filename



app = Flask(__name__)

app.config.update(dict(
    DEBUG=True,
    SECRET_KEY="do not use the development key in production!!!",
    SESSIONS_DIR=os.path.join(os.path.dirname(os.path.abspath(__file__)), "sessions")
))

class Md5HexValidator(BaseConverter):
  """Custom converter to validate if a string is an MD5 hexdigest. Used as
  validator for session ids in paths.
  `to_python` and `to_url` have to be implemented by subclasses of
  BaseConverter. """
  def to_python(self, value):
    try:
      # MD5 Hex Digests  should 32 byte long
      if len(value) != 32:
        raise ValueError
      # and hex
      int(value, 16)
    except ValueError:
      raise ValidationError()
    else:
      return str(value)

  def to_url(self, value):
      return str(value)

# Add custom converter (validator)
app.url_map.converters['md5'] = Md5HexValidator


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
    Redirects to show layout page

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
      msg = "Could not create session directory '{0}' - {1}".format(
          session_path, e)
      app.logger.error(msg)
      flash(msg)

  return redirect(url_for("show_layout", session_id=session["id"]))


@app.route("/<md5:session_id>", methods=["GET"])
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
    Renders show layout page

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
      msg = "Could not read layout '{0}' - {1}".format(layout_path, e)
      app.logger.error(msg)
      flash(msg)

  return render_template("index.html",
      session_id=session_id, layout=layout, layout_choices=layout_choices,
      layout_name=layout_name)

@app.route("/<md5:session_id>/add-layout", methods=["POST"])
def add_layout(session_id):
  """
  <Purpose>
    Adds a posted layout to the session directory and redirects to show
    layout passing the layout name as parameter.

  <Returns>
    Redirects to show layout page

  """
  session_path = _session_path(session_id)
  layout_name = None

  if "layout-file" not in request.files:
    flash("No file sent")
    return redirect(url_for("show_layout", session_id=session["id"]))

  file = request.files["layout-file"]
  if file.filename == "":
    flash("No file selected")
    return redirect(url_for("show_layout", session_id=session["id"]))

  layout_name = secure_filename(file.filename)
  layout_path = os.path.join(session_path, layout_name)
  file.save(layout_path)

  return redirect(url_for("show_layout", session_id=session["id"],
      layout_name=layout_name))

if __name__ == "__main__":
  app.run()