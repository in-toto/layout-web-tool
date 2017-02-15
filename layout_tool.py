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
import time
import datetime
import dateutil.relativedelta
import dateutil.parser

import in_toto.models.layout
import in_toto.artifact_rules
import in_toto.util
import securesystemslib.keys

from flask import (Flask, render_template, session, redirect, url_for, request,
    flash)
from werkzeug.routing import BaseConverter, ValidationError
from werkzeug.utils import secure_filename



app = Flask(__name__, static_url_path="")

app.config.update(dict(
    DEBUG=True,
    SECRET_KEY="do not use the development key in production!!!",
    SESSIONS_DIR=os.path.join(os.path.dirname(os.path.abspath(__file__)), "sessions"),
    LAYOUT_SUBDIR="layouts",
    PUBKEYS_SUBDIR="pubkeys"
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

def _session_layout_dir(session_id):
  return os.path.join(app.config["SESSIONS_DIR"],
      session_id, app.config["LAYOUT_SUBDIR"])

def _session_pubkey_dir(session_id):
  return os.path.join(app.config["SESSIONS_DIR"],
      session_id, app.config["PUBKEYS_SUBDIR"])

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
    Creates session directory and subdirs for layouts and pubkeys
    if the session is new

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
    layout_path = _session_path(session["id"])
    app.logger.debug("Create session dir and subdirs '{}'".format(
        session_path))

    try:
      os.mkdir(_session_path(session["id"]))
      os.mkdir(_session_layout_dir(session["id"]))
      os.mkdir(_session_pubkey_dir(session["id"]))
    except Exception as e:
      msg = "Could not create directory for session '{0}' - {1}".format(
          session["id"], e)
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
  layout_dir = _session_layout_dir(session_id)
  pubkey_dir = _session_pubkey_dir(session_id)

  layout = None
  layout_name = None

  if request.args.get("layout_name"):
    layout_name = urllib.unquote(request.args.get("layout_name"))

  # Assume all files are layouts (sanatized on upload/create)
  available_layouts = os.listdir(layout_dir)

  # Assume all files are pubkeys (sanatized on upload)
  available_pubkeys = []
  for pubkey_name in os.listdir(pubkey_dir):
    try:
      pubkey_path = os.path.join(pubkey_dir, pubkey_name)
      key = in_toto.util.import_rsa_key_from_file(pubkey_path)
      available_pubkeys.append(key["keyid"])
    except Exception as e:
      app.logger.debug("Ignoring wrong format pubkey '{0}' - {1}".format(
          pubkey_name, e))
      continue

  # If the user has already chosen, passed a layout_name as get parameter
  # we try to load that layout
  if layout_name:
    layout_path = os.path.join(layout_dir, layout_name)
    try:
      layout = in_toto.models.layout.Layout.read_from_file(layout_path)
    except Exception as e:
      msg = "Could not read layout '{0}' - {1}".format(layout_path, e)
      app.logger.error(msg)
      flash(msg)

  return render_template("index.html",
      session_id=session_id, layout=layout,
      layout_name=layout_name, available_layouts=available_layouts,
      available_pubkeys=available_pubkeys)


@app.route("/<md5:session_id>/upload-layout", methods=["POST"])
def upload_layout(session_id):
  """
  <Purpose>
    Adds a posted layout to the session directory and redirects to show
    layout passing the layout name as parameter.

  <Returns>
    Redirects to show layout page

  """
  layout_dir = _session_layout_dir(session_id)
  layout_name = None

  if "layout_file" not in request.files:
    flash("No file sent")
    return redirect(url_for("show_layout", session_id=session["id"]))

  file = request.files["layout_file"]
  if file.filename == "":
    flash("No file selected")
    return redirect(url_for("show_layout", session_id=session["id"]))

  # TODO: We should check if the layout is an (empty/unfinished) layout
  # TODO: store pubkeys to pubkeys file
  layout_name = secure_filename(file.filename)
  layout_path = os.path.join(layout_dir, layout_name)
  file.save(layout_path)

  return redirect(url_for("show_layout", session_id=session["id"],
      layout_name=layout_name))


@app.route("/<md5:session_id>/upload-pubkeys", methods=["POST"])
def upload_pubkeys(session_id):
  """
  <Purpose>
    Adds posted pub keys to the session directory

  """
  pubkey_dir = _session_pubkey_dir(session_id)
  pubkey_files = request.files.getlist("pubkey_file[]")

  for pubkey_file in pubkey_files:
    try:
      pubkey = securesystemslib.keys.import_rsakey_from_public_pem(
          pubkey_file.read())
    except Exception as e:
      app.logger.error("Could not parse uploaded pubkey file '{0}' - {1}".format(
          pubkey_file.name, e))
      continue

    try:
      # We create our own name using the first six bytes of the pubkeys keyid
      pubkey_name = pubkey["keyid"][:6] + ".pub"
      pubkey_path = os.path.join(pubkey_dir, pubkey_name)
      pubkey_file.seek(0)
      pubkey_file.save(pubkey_path)
      flash("Succesfully stored uploaded file '{0}' as {1}".format(
          pubkey_file.filename, pubkey_name))

    except Exception as e:
      app.logger.error("Could not save pubkey file '{0}' - '{1}'".format(
          pubkey_file.filename, e))

  return redirect(url_for("show_layout", session_id=session["id"]))


@app.route("/<md5:session_id>/add-layout", methods=["POST"])
def add_layout(session_id):
  """
  <Purpose>
    Adds a new empty layout with a default name to the session directory.
    The name is "untitled-<unixtimestamp>.layout" and can be changed later.
  <Returns>
    Redirects to show layout page

  """
  layout_dir = _session_layout_dir(session_id)

  # A timestamped file name seems rather unique (for one session on one machine)
  layout_name = "untitled-" + str(time.time()).replace(".", "") + ".layout"

  layout = in_toto.models.layout.Layout()
  # FIXME: Moving default setup to the layout constructor would be nicer
  # Cf. https://github.com/in-toto/in-toto/issues/36
  layout.expires = (datetime.datetime.today()
      + dateutil.relativedelta.relativedelta(months=1)
      ).isoformat() + 'Z'

  layout_path = os.path.join(layout_dir, layout_name)
  layout.dump(layout_path)
  flash("Successfully created new layout '{}'".format(layout_name))

  return redirect(url_for("show_layout", session_id=session["id"],
      layout_name=layout_name))


@app.route("/<md5:session_id>/save-layout", methods=["POST"])
def save_layout(session_id):
  """
  <Purpose>
    Update layout with posted arguments.
    Each time re-sends and re-writes the entire layout.
    In case the file name is changed we delete the old filename.

  <Returns>
    Redirects to show layout page

  """
  session_path = _session_path(session_id)
  # Get new and old layout file name and create session paths
  old_layout_name = secure_filename(request.form.get("layout_name"))
  new_layout_name = secure_filename(request.form.get("new_layout_name"))
  old_layout_path = os.path.join(session_path, old_layout_name)
  new_layout_path = os.path.join(session_path, new_layout_name)

  # Fetch other form properties
  expires = request.form.get("expires")

  # Load layout from file
  layout = in_toto.models.layout.Layout.read_from_file(old_layout_path)

  # Set attributes
  expires_zulu_fmt = dateutil.parser.parse(expires).isoformat() + 'Z'
  layout.expires = expires_zulu_fmt

  # If the filename has changed, we can replace the old layout
  if old_layout_path != new_layout_path:
    layout.dump(new_layout_path)
    os.remove(old_layout_path)
    layout_name = new_layout_name
  else:
    layout.dump(old_layout_path)
    layout_name = old_layout_name

  return redirect(url_for("show_layout", session_id=session["id"],
      layout_name=layout_name))


@app.context_processor
def in_toto_processor():
  def unpack_rule(rule):
    """
    <Purpose>
      Adds in_toto unpack_rule as tag to the template engine, use like:
      {{ unpack_rule(rule) }}

    <Arguments>
      rule:
              In-toto artifact rule in list format
              cf. in_toto.artifact_rules.unpack_rule

    <Returns>
      Returns rule_data cf. in_toto.artifact_rules.unpack_rule

    """
    return in_toto.artifact_rules.unpack_rule(rule)
  return dict(unpack_rule=unpack_rule)


@app.template_filter('zulu_to_html')
def _zulu_to_html(date):
  """Converts Zulu datetime object to "yyyy-MM-ddThh:mm as required by
  HTML widget. """
  datetime = dateutil.parser.parse(date)
  return datetime.strftime("%Y-%m-%dT%H:%M")

if __name__ == "__main__":
  app.run()
