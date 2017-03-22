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

app = Flask(__name__, static_url_path="", instance_relative_config=True)

app.config.update(dict(
    DEBUG=True,
    SECRET_KEY="do not use the development key in production!!!",
    SESSIONS_DIR=os.path.join(os.path.dirname(os.path.abspath(__file__)), "sessions"),
    LAYOUT_SUBDIR="layouts",
    PUBKEYS_SUBDIR="pubkeys",
    LINK_SUBDIR="links"
))

# Supply a config file at "instance/config.py" that carries e.g. your deployment
# secret key
app.config.from_pyfile("config.py")

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

def _session_link_dir(session_id):
  return os.path.join(app.config["SESSIONS_DIR"],
      session_id, app.config["LINK_SUBDIR"])

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
    link_dir = _session_link_dir(session_id)

    if not (os.path.isdir(layout_dir) and os.path.isdir(pubkey_dir) and
      os.path.isdir(link_dir)):
      abort(404)

    # Let's up date the session id just in case
    session["id"] = session_id
    return wrapped_func(*args, **kwargs)
  return decorated_function





# -----------------------------------------------------------------------------
# Views
# -----------------------------------------------------------------------------
@app.route("/")
def index():
  """Entry point for layout creation tool.
  If the user has an ongoing session we redirect to the session page, where
  s/he can access uploaded or created layouts and keys. Otherwise we create a
  session directory with layouts and pubkeys subdirectories. """

  # This is a new session so we have to create an id and some directories
  if not session.get("id"):
    # Sessions use a MD5 hexdigest of a random value
    # Security is not paramount, because we don't store sensitive data, right?
    session_id = hashlib.md5(str(random.random())).hexdigest()

    # Assign the id to the user's session variable
    session["id"] = session_id
    app.logger.info("New session '{}'".format(session_id))

    try:
      # Create new session directory where we store layouts and pubkeys
      app.logger.info("Creating session dir and subdirs for '{}'".format(
          session_id))
      os.mkdir(_session_path(session_id))
      os.mkdir(_session_layout_dir(session_id))
      os.mkdir(_session_pubkey_dir(session_id))
      os.mkdir(_session_link_dir(session_id))

    except Exception as e:
      msg = ("Could not create session directories for '{0}'"
          " - Error: {1}".format(session_id, e))
      app.logger.error(msg)
      abort(500, msg)

    else:
      msg = "Successfully created new in-toto layout session!"
      app.logger.info(msg)
      flash(msg)

  return redirect(url_for("layout_wizzard", session_id=session["id"]))

@app.route("/<md5:session_id>/wizz", methods=["GET"])
def layout_wizzard(session_id):
  return render_template("base-wizzard.html", session_id=session_id,)

# @app.route("/<md5:session_id>/", defaults={"layout_name": None}, methods=["GET"])
@app.route("/<md5:session_id>/edit", defaults={"layout_name": None}, methods=["GET"])
@app.route("/<md5:session_id>/<layout:layout_name>/edit", methods=["GET"])
@session_exists # Returns 404 if the directories are not there
def layout_editor(session_id, layout_name):
  """ Main page shows:
  - session link
  - select layout
  - upload public keys
  - create new layout
  - layout form (if a layout_name was specified as path or query parameter)
  """

  # We accept the layout_name also as query param, e.g.: when sent through the
  # select layout form, but then we redirect to the view using it as path param.
  # Why? Because it looks better and because we can.
  if request.args.get("layout_name"):
    return redirect(url_for('layout_editor', session_id=session_id,
        layout_name=request.args.get("layout_name")))

  layout_dir = _session_layout_dir(session_id)
  pubkey_dir = _session_pubkey_dir(session_id)

  layout = None

  # Assume all files are layouts (sanitized on upload/create)
  available_layouts = os.listdir(layout_dir)

  # Assume all files are pubkeys (sanitized on upload)
  available_pubkeys = []
  for pubkey_name in os.listdir(pubkey_dir):
    try:
      pubkey_path = os.path.join(pubkey_dir, pubkey_name)
      key = in_toto.util.import_rsa_key_from_file(pubkey_path)
      available_pubkeys.append(key["keyid"])

    except Exception as e:
      app.logger.info("Ignoring wrong format pubkey '{0}' - {1}".format(
          pubkey_name, e))
      continue

  # If the user queried for a layout we try to load it
  if layout_name:
    layout_path = os.path.join(layout_dir, layout_name)
    try:
      layout = in_toto.models.layout.Layout.read_from_file(layout_path)
    except Exception as e:
      msg = "Could not read layout '{0}' - {1}".format(layout_path, e)
      app.logger.warning(msg)
      flash(msg)

  return render_template("base-editor.html",
      session_id=session_id, layout=layout,
      layout_name=layout_name, available_layouts=available_layouts,
      available_pubkeys=available_pubkeys)


@app.route("/<md5:session_id>/upload-layout", methods=["POST"])
@session_exists
def upload_layout(session_id):
  """Receives a form posted layout file and stores it to the session directory,
  redirects to the edit form for the uploaded layout. """

  layout_dir = _session_layout_dir(session_id)
  layout_name = None

  # Check if the post request has the file part
  if "layout_file" not in request.files:
    msg = "Could not store uploaded file - No file uploaded"
    app.logger.error(msg)
    flash(msg)
    return redirect(url_for("layout_editor", session_id=session_id))

  file = request.files["layout_file"]

  # If user does not select file, browser also
  # submit a empty part without filename
  if file.filename == "":
    msg = "Could not store uploaded file - No file selected"
    app.logger.error(msg)
    flash(msg)
    return redirect(url_for("layout_editor", session_id=session_id))

  # Try reading the uploaded file as in-toto layout
  try:
    layout_name = secure_filename(file.filename)
    layout_path = os.path.join(layout_dir, layout_name)
    layout = in_toto.models.layout.Layout.read(json.load(file))
    layout.dump(layout_path)

  except Exception as e:
    msg = "Could not store uploaded file as in-toto layout - Error: {}".format(e)
    app.logger.error(msg)
    flash(msg)
    return redirect(url_for("layout_editor", session_id=session_id))

  # Extract public keys from uploaded layout and store them to the session dir
  # Henceforth user can use the keys for other layouts too.
  if layout.keys and isinstance(layout.keys, dict):
    for keyid, key in layout.keys.iteritems():
      try:
        pubkey_name = _store_pubkey_to_session_dir(session_id, key)
      except Exception as e:
        msg = ("Tried to extracted pubkey from layout but failed "
            " - Error:  {}".format(e))
        app.logger.error(msg)
        flash(msg)
      else:
        msg = ("Extracted public key '{}' from uploaded layout and added it to"
            " session directory. You can include the key now in all layouts."
            .format(pubkey_name))
        app.logger.info(msg)
        flash(msg)

  return redirect(url_for("layout_editor", session_id=session_id,
      layout_name=layout_name))


@app.route("/<md5:session_id>/upload-pubkeys/", methods=["POST"])
@session_exists
def upload_pubkeys(session_id):
  """Receives multiple form posted public key files and stores them to session
  directory, so the user can add them to the created layout(s). If the user was
  on an edit layout page, this view redirects to that layout.

  TODO: if the user edited a layout and hasn't saved it, uploading keys will
  override those saves. Maybe we should add a confirm/warning box or
  autosafe? """

  pubkey_dir = _session_pubkey_dir(session_id)
  pubkey_files = request.files.getlist("pubkey_file[]")
  layout_name = request.form.get("layout_name", None)

  # If nothing was uploaded abort early
  if not pubkey_files:
    msg = "Could not store uploaded file - No file uploaded"
    app.logger.warning(msg)
    flash(msg)
    return redirect(url_for("layout_editor", session_id=session_id,
        layout_name=layout_name))

  # Iterate over uploaded files and try to store, don't abort but skip on error
  for pubkey_file in pubkey_files:
    try:
      pubkey = securesystemslib.keys.import_rsakey_from_public_pem(
          pubkey_file.read())
      pubkey_name = _store_pubkey_to_session_dir(session_id, pubkey)
    except Exception as e:
      msg = ("Could not store uploaded file as in-toto public key '{0}'"
          " - Error: {1}".format(pubkey_file.name, e))
      app.logger.warning(msg)
      flash(msg)
    else:
      msg = ("Added uploaded public key '{}' to session directory."
            " You can include the key now in all layouts."
            .format(pubkey_name))
      app.logger.info(msg)
      flash(msg)

  return redirect(url_for("layout_editor", session_id=session_id,
      layout_name=layout_name))


@app.route("/<md5:session_id>/create-layout", methods=["POST"])
@session_exists
def create_layout(session_id):
  """Creates and adds a new empty layout with a default name to the session
  directory, redirects to the edit form for the created layout.

  Name is "untitled-<unix-timestamp>.layout". It can be changed later.
  """
  layout_dir = _session_layout_dir(session_id)

  # A timestamped file name seems rather unique (for one session on one machine)
  layout_name = "untitled-" + str(time.time()).replace(".", "") + ".layout"

  try:
    layout = in_toto.models.layout.Layout()
    # FIXME: Moving default setup to the layout constructor would be nicer
    # Cf. https://github.com/in-toto/in-toto/issues/36
    layout.expires = (datetime.datetime.today()
        + dateutil.relativedelta.relativedelta(months=1)
        ).isoformat() + "Z"

    layout_path = os.path.join(layout_dir, layout_name)
    layout.dump(layout_path)

  except Exception as e:
      msg = "Could not create new layout - Error: '{}'".format(e)
      app.logger.error(msg)
      flash(msg)

  else:
    msg = "Successfully created new layout '{}'".format(layout_name)
    app.logger.info(msg)
    flash(msg)

  return redirect(url_for("layout_editor", session_id=session_id,
      layout_name=layout_name))


@app.route("/<md5:session_id>/<layout:layout_name>/save", methods=["POST"])
@session_exists
def save_layout(session_id, layout_name):
  """Receives form with one field, which is a stringified JSON object containing
  an in-toto layout as edited by the user in the layout form, stores it as to
  the session dir and redirects to the edit form.

  The received layout can almost be stored as is, except for:
    layout_name_new - we pop this property and use it as filename
    expires - we have to convert the datetime to be in-toto conformant
    layout_pubkey_ids - the posted layout object only contains pubkey_ids,
        we have to load the actual keys from the sessions's pubkeys dir and
        add them to the layout instead of the ids

  NOTE:
  Since the layout form is nested and dynamic the JSON approach is preferred over
  keeping track of nested form data names. Which would require to increment
  or decrement indices in the name attributes of input elements each time
  we add or remove dynamic form elements.

  """
  layout_dir = _session_layout_dir(session_id)
  pubkey_dir = _session_pubkey_dir(session_id)

  json_data = request.form.get("json_data")

  try:
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

    # Load the public keys from the file paths created above into a key
    # dictionary conformant with the layout's pubkeys property and assign it
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

  except Exception as e:
    msg = "Could not update layout - Error: {}".format(e)
    app.logger.error(msg)
    flash(msg)

  else:
    msg = "Successfully update layout as '{}' !".format(layout_name_new)
    app.logger.info(msg)
    flash(msg)

    # If the file is actually new (differs from the old filename), we can
    # remove the old file
    if layout_name_new != layout_name:
      try:
        layout_path_old = os.path.join(layout_dir, layout_name)
        os.remove(layout_path_old)

      except Exception as e:
        msg = "Could not remove old layout '{0}' - Error: {1}".format(layout_name,
            e)
        app.logger.error(msg)
        flash(msg)

      else:
        msg = "Successfully removed old layout '{}' !".format(layout_name)
        app.logger.info(msg)
        flash(msg)

  return redirect(url_for("layout_editor", session_id=session_id,
      layout_name=layout_name_new))


@app.route("/<md5:session_id>/<layout:layout_name>/download", methods=["GET"])
def download_layout(session_id, layout_name):
  """Serves layout with layout name from session directory as attachment
  (Content-Disposition: attachment). """

  layout_dir = _session_layout_dir(session_id)
  return send_from_directory(layout_dir, layout_name, as_attachment=True)




if __name__ == "__main__":
  app.run()
