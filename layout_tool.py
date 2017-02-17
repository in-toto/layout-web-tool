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
import json
import datetime
import dateutil.relativedelta
import dateutil.parser

import in_toto.models.layout
import in_toto.artifact_rules
import in_toto.util
import securesystemslib.keys

from functools import wraps
from flask import (Flask, render_template, session, redirect, url_for, request,
    flash, send_from_directory, abort)
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

PUBKEY_FILENAME = "{keyid:.6}.pub"





# -----------------------------------------------------------------------------
# URL MAP converters
# -----------------------------------------------------------------------------
class Md5HexValidator(BaseConverter):
  """Custom converter to validate if a string is an MD5 hexdigest. Used as
  validator for session ids in paths.
  `to_python` and `to_url` have to be implemented by subclasses of
  BaseConverter. """
  def to_python(self, value):
    try:
      # MD5 Hex Digests must be 32 byte long
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


class FileNameConverter(BaseConverter):
  """Custom converter for file names in the URL path (quote/unquote)"""

  def to_python(self, value):
    return secure_filename(urllib.unquote(value))

  def to_url(self, value):
    return urllib.quote(value)

# Add custom converter/validator
app.url_map.converters["md5"] = Md5HexValidator
app.url_map.converters["layout"] = FileNameConverter





# -----------------------------------------------------------------------------
# Helper Functions
# -----------------------------------------------------------------------------
def _session_path(session_id):
  return os.path.join(app.config["SESSIONS_DIR"], session_id)

def _session_layout_dir(session_id):
  return os.path.join(app.config["SESSIONS_DIR"],
      session_id, app.config["LAYOUT_SUBDIR"])

def _session_pubkey_dir(session_id):
  return os.path.join(app.config["SESSIONS_DIR"],
      session_id, app.config["PUBKEYS_SUBDIR"])

def _store_pubkey_to_session_dir(session_id, pubkey):
  # We create our own name using the first six bytes of the pubkey's keyid
  pubkey_name = PUBKEY_FILENAME.format(keyid=pubkey["keyid"])
  pubkey_dir = _session_pubkey_dir(session_id)
  pubkey_path = os.path.join(pubkey_dir, pubkey_name)
  public_part = pubkey["keyval"]["public"]

  with open(pubkey_path, "w") as fo_public:
    fo_public.write(public_part.encode("utf-8"))

  return pubkey_name





# -----------------------------------------------------------------------------
# Context Processors
# -----------------------------------------------------------------------------
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




# -----------------------------------------------------------------------------
# Template Filters
# -----------------------------------------------------------------------------
@app.template_filter("zulu_to_html")
def _zulu_to_html(date):
  """Converts Zulu datetime object to "yyyy-MM-ddThh:mm as required by
  HTML widget. """
  datetime = dateutil.parser.parse(date)
  return datetime.strftime("%Y-%m-%dT%H:%M")





# -----------------------------------------------------------------------------
# View Decorator
# -----------------------------------------------------------------------------
def session_exists(wrapped_func):
  """Checks if the session a user tries to access actually exists (the
  directories have been created), returns 404 if not. """
  @wraps(wrapped_func)
  def decorated_function(*args, **kwargs):

    session_id = kwargs.get("session_id")
    layout_dir = _session_layout_dir(session_id)
    pubkey_dir = _session_pubkey_dir(session_id)

    if not (os.path.isdir(layout_dir) and os.path.isdir(pubkey_dir)):
      abort(404)

    # Let's up date the session id just in case
    session["id"] = session_id
    return wrapped_func(*args, **kwargs)
  return decorated_function

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

  return redirect(url_for("edit_layout", session_id=session["id"]))


@app.route("/<md5:session_id>/", defaults={"layout_name": None}, methods=["GET"])
@app.route("/<md5:session_id>/<layout:layout_name>", methods=["GET"])
def edit_layout(session_id, layout_name):
  """ Main page shows:
  - session link
  - select layout
  - upload public keys
  - create new layout
  - layout form (if a layout_name was specified as path or query parameter)
  """
  # We accept also the layout_name as query param, e.g.: when sent through the
  # select layout form. But then we redirect to the view using it as path param.
  # Why? Because it looks better and because we can.
  if request.args.get("layout_name"):
    return redirect(url_for('edit_layout', session_id=session_id,
        layout_name=request.args.get("layout_name")))

  # Override session, if someone calls a session url explicitly
  session["id"] = session_id
  layout_dir = _session_layout_dir(session_id)
  pubkey_dir = _session_pubkey_dir(session_id)

  layout = None

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

  # If the user queried for a layout we try to load it
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
    return redirect(url_for("edit_layout", session_id=session["id"]))

  file = request.files["layout_file"]
  if file.filename == "":
    flash("No file selected")
    return redirect(url_for("edit_layout", session_id=session["id"]))

  # Check if the layout is an (empty/unfinished) layout
  try:
    layout_name = secure_filename(file.filename)
    layout_path = os.path.join(layout_dir, layout_name)
    layout = in_toto.models.layout.Layout.read(json.load(file))
    layout.dump(layout_path)
  except Exception as e:
    flash("Uploaded file is not a layout - {}".format(e))
    return redirect(url_for("edit_layout", session_id=session["id"]))

  # Store pubkeys to pubkeys dir
  if layout.keys and isinstance(layout.keys, dict):
    for keyid, key in layout.keys.iteritems():
      try:
        pubkey_name = _store_pubkey_to_session_dir(session["id"], key)
      except Exception as e:
        app.logger.warning(
            "Tried to extracted pubkey from layout but failed - {}".format(
            e))
      else:
        flash("Extracted public key '{}' from uploaded layout and added it"
            " session directory. You can use this key now for all layouts."
            .format(pubkey_name))

  return redirect(url_for("edit_layout", session_id=session["id"],
      layout_name=layout_name))


@app.route("/<md5:session_id>/upload-pubkeys/", methods=["POST"])
def upload_pubkeys(session_id):
  """
  <Purpose>
    Adds posted pub keys to the session directory

  """
  pubkey_dir = _session_pubkey_dir(session_id)
  pubkey_files = request.files.getlist("pubkey_file[]")
  layout_name = request.form.get("layout_name", None)

  for pubkey_file in pubkey_files:
    try:
      pubkey = securesystemslib.keys.import_rsakey_from_public_pem(
          pubkey_file.read())
    except Exception as e:
      app.logger.error("Could not parse uploaded pubkey file '{0}' - {1}".format(
          pubkey_file.name, e))
      continue

    try:
      _store_pubkey_to_session_dir(session_id, pubkey)
    except Exception as e:
      app.logger.error("Could not save pubkey file '{0}' - '{1}'".format(
          pubkey_file.filename, e))

  return redirect(url_for("edit_layout", session_id=session["id"],
      layout_name=layout_name))


@app.route("/<md5:session_id>/create-layout", methods=["POST"])
def create_layout(session_id):
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
      ).isoformat() + "Z"

  layout_path = os.path.join(layout_dir, layout_name)
  layout.dump(layout_path)
  flash("Successfully created new layout '{}'".format(layout_name))

  return redirect(url_for("edit_layout", session_id=session["id"],
      layout_name=layout_name))


@app.route("/<md5:session_id>/<layout:layout_name>/save", methods=["POST"])
def save_layout(session_id, layout_name):
  """
  <Purpose>
    Update layout with posted arguments.
    Each time re-sends and re-writes the entire layout.
    In case the file name is changed we delete the old filename.

  <Returns>
    Redirects to show layout page

  """
  layout_dir = _session_layout_dir(session_id)
  pubkey_dir = _session_pubkey_dir(session_id)

  json_data = request.form.get("json_data")
  layout_dict = json.loads(json_data)

  # Extract non-in-toto conformant properties from the layout dictionary
  layout_name_new = layout_dict.pop("layout_name_new")
  layout_expires = layout_dict.pop("expires")
  layout_pubkey_ids = layout_dict.pop("layout_pubkey_ids")

  # Create a list file paths where we expect the publickeys associated with
  # the keyids we got posted
  layout_pubkey_paths = []
  for pubkey_id in layout_pubkey_ids:
    pubkey_fn = PUBKEY_FILENAME.format(keyid=pubkey_id)
    pubkey_path = os.path.join(pubkey_dir, pubkey_fn)
    layout_pubkey_paths.append(pubkey_path)

  # Load the public keys from the file paths created above into a key dictionary
  # conformant with the layout's pubkeys property and assign it
  layout_pubkeys = in_toto.util.import_rsa_public_keys_from_files_as_dict(
      layout_pubkey_paths)
  layout_dict["keys"] = layout_pubkeys


  # Convert the passed timestamp into the required format
  # NOTE: This is really something in-toto should do!!
  expires_zulu_fmt = dateutil.parser.parse(layout_expires).isoformat() + "Z"
  layout_dict["expires"] = expires_zulu_fmt

  # Create in-toto layout object from the dictionary
  layout = in_toto.models.layout.Layout.read(layout_dict)

  # Make filenames secure
  layout_name_new = secure_filename(layout_name_new)

  # Store the new layout in the session's layout dir
  layout_path_new = os.path.join(layout_dir, layout_name_new)
  layout.dump(layout_path_new)

  # If the file is actually new (differs from the old filename), we can
  # remove the old file
  if layout_name_new != layout_name:
    layout_path_old = os.path.join(layout_dir, layout_name)
    os.remove(layout_path_old)

  return redirect(url_for("edit_layout", session_id=session["id"],
      layout_name=layout_name_new))


@app.route("/<md5:session_id>/<layout:layout_name>/download", methods=["GET"])
def download_layout(session_id, layout_name):
  """Serves layout with layout name from session directory as attachement
  (Content-Disposition: attachment). """

  layout_dir = _session_layout_dir(session_id)
  return send_from_directory(layout_dir, layout_name, as_attachment=True)




if __name__ == "__main__":
  app.run()
