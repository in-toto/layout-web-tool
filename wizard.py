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
import os
import random
import hashlib
import time
import StringIO
import tarfile


from functools import wraps
from flask import (Flask, render_template, session, redirect, url_for, request,
    flash, send_file, abort, json, jsonify)
from flask_pymongo import PyMongo

import in_toto.util
import in_toto.models.link
import in_toto.models.mock_link
import in_toto.models.layout
import in_toto.artifact_rules
import securesystemslib.keys

import tooldb
import reverse_layout

app = Flask(__name__, static_url_path="", instance_relative_config=True)
mongo = PyMongo(app)

app.config.update(dict(
    DEBUG=True,
    SECRET_KEY="do not use the development key in production!!!",
))

# Supply a config file at "instance/config.py" that carries
# e.g. your deployment secret key
app.config.from_pyfile("config.py")

# -----------------------------------------------------------------------------
# Utils
# -----------------------------------------------------------------------------
def session_to_ssc(session_data):
  """
  <Purpose>
    Takes a session document, which can contain form posted data from previous
    pages (vcs, building, qa, ...) to generate a dict of lists of step data and
    inspection data dicts.

  <Returns>
    Software Supply Chain Data, i.e. a dictionary of step and inspection data
    (these are not not actual in-toto Step and Inspection objects), e.g.:
    {
      steps: [
        {
          "name": <unique step name>,
          "cmd": <expected command>,
          "modifies": boolean
        }, ...
      ],
      inspections: [
        {
          "name": <unique inspection name>,
          "cmd": <command to run inspecting>,
          "based_on": <step name whose products are used for that inspection>
        }
      ]
    }
  """
  ssc_steps = []
  ssc_inspections = []

  for step_type in ["vcs", "building", "qa", "package"]:
    for idx, step in enumerate(session_data.get(step_type, {}).get(
        "items", [])):
      # FIXME: Come up with better naming (low priority)
      step_name = "{}-{}".format(step_type, idx + 1)
      ssc_step = {
        "name": step_name,
        "cmd" : step["cmd"],
        "modifies": True
      }

      # We suggest an inspection for each set retval, stdout and stderr for
      # each specified QA step
      if step_type == "qa":
        # QA steps don't have products, we need this information to visualize
        # this ssc graph
        ssc_step["modifies"] = False

        for inspect_type in ["retval", "stdout", "stderr"]:
          enabled = step.get(inspect_type)
          val = step.get(inspect_type + "_value")
          operator = step.get(inspect_type + "_operator")

          if enabled:
            # The (QA) link file we want to inspect uses the link step name
            # created above
            link = in_toto.models.link.FILENAME_FORMAT_SHORT.format(
                step_name=step_name)
            value = step.get(inspect_type + "_value")

            if inspect_type == "retval":
              run = ("inspect-return-value --link={link} --{operator} {value}"
                  .format(link=link, operator=operator, value=value))

            elif inspect_type in ["stdout", "stderr"]:
              if operator == "empty":
                operator = "is"
                value = ""

              run = ("inspect-byproducts"
                  " --link={link} --{inspect_type} --{operator} \"{value}\""
                  .format(link=link, inspect_type=inspect_type,
                  operator=operator, value=value))

            inspect_name = "inspection-" + str(len(ssc_inspections) + 1)
            ssc_inspections.append({
              "name": inspect_name,
              "cmd": run,
              "based_on": step_name
            })

      ssc_steps.append(ssc_step)

  ssc_data = {
    "steps": ssc_steps,
    "inspections": ssc_inspections
  }
  return ssc_data


def form_data_to_ssc(step_names, step_commands, step_modifies,
    inspection_names, inspection_commands, inspection_step_names):
  """
  <Purpose>
    Takes form posted data (lists) to generate a dict of lists of step data and
    inspection data dicts.
    Each item aggregates the step or inspection data by list index

  <Returns>
    Software Supply Chain Data, i.e. a dictionary of step and inspection data
    (these are not not actual in-toto Step and Inspection objects), e.g.:
    {
      steps: [
        {
          "name": <unique step name>,
          "cmd": <expected command>
          "modifies": boolean
        }, ...
      ],
      inspections: [
        {
          "name": <unique inspection name>,
          "cmd": <command to run inspecting>,
          "based_on": <step name whose products are used for that inspection>
        }
      ]
    }

  """
  steps = []
  for i in range(len(step_names)):
    steps.append({
        "name": step_names[i],
        "cmd": step_commands[i],
        "modifies": step_modifies[i] == "true"
      })

  inspections = []
  for i in range(len(inspection_names)):
    inspections.append({
        "name": inspection_names[i],
        "cmd": inspection_commands[i],
        "based_on": inspection_step_names[i]
      })

  ssc_data = {
    "steps": steps,
    "inspections": inspections
  }
  return ssc_data

# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------
def _auth_items_to_dict(auth_items):
  """Maps auth_items to their respective step names """
  auth_dict = {}
  for auth_item in auth_items:
    auth_dict[auth_item["step_name"]] = auth_item
  return auth_dict


# -----------------------------------------------------------------------------
# NoSQL Helpers
# -----------------------------------------------------------------------------

# NOTE:
# Below functions rely on the current session having an id. If there is no id
# in the session, all functions redirect to `404`.
# This should never happen because all calling views should be decorated with
# @with_session_id, which ensures that the current session does have an id.
def _persist_session_subdocument(subdocument):
  """Update a subdocument (e.g. vcs, ssc, functionaries...) in session document
  identified by current session id. """
  if not session.get("id"):
    abort(404)

  # Search session document by session ID and update (replace) sub-document
  # If the entire document does not exist it is inserted
  mongo.db.session_collection.update_one(
    {"_id": session["id"]},
    {"$set": subdocument},
    upsert=True)


def _persist_session_subdocument_ts(subdocument):
  """Updates/adds last_modified to the subdocument before persisting it. """

  for key in subdocument.keys():
    subdocument[key]["last_modified"] = time.time()
  _persist_session_subdocument(subdocument)


def _get_session_subdocument(key):
  """Returns a subdocument (e.g. vcs, ssc, functionaries...) identified by
  passed key from session document identified by current session id.
  Returns an empty dict if document or subdocument are not found.  """
  if not session.get("id"):
    abort(404)

    # Get session document (use short circuit for default empty dict)
  session_doc = mongo.db.session_collection.find_one(
      {"_id": session["id"]})

  if not session_doc:
    return {}

  # Get vcs data from session document or empty dict
  return session_doc.get(key, {})


def _get_session_document():
  """Returns the entire session document (default: {}) """
  if not session.get("id"):
    abort(404)

  session_doc = mongo.db.session_collection.find_one(
    {"_id": session["id"]})

  if not session_doc:
    return {}

  return session_doc


# -----------------------------------------------------------------------------
# View Decorator
# -----------------------------------------------------------------------------
def with_session_id(wrapped_func):
  """
  Generate new session id if it does not exist.

  For now, a user could start a new session on any page
  TODO: Should we redirect to the start page if the session is new?
  """
  @wraps(wrapped_func)
  def decorated_function(*args, **kwargs):
    if not session.get("id"):
      # Sessions use a MD5 hexdigest of a random value
      # Security is not paramount, we don't store sensitive data, right?
      session["id"] = hashlib.md5(str(random.random())).hexdigest()

    return wrapped_func(*args, **kwargs)
  return decorated_function


# -----------------------------------------------------------------------------
# Views
# -----------------------------------------------------------------------------
@app.route("/")
@with_session_id
def start():
  """Step 0.
  Wizard entry point, static landing page. """
  return render_template("start.html")


@app.route("/versioning", methods=["GET", "POST"])
@with_session_id
def versioning():
  """Step 1.
  Enter information about version control system. """
  options = tooldb.collection["vcs"]

  if request.method == "POST":
    # Grab the form posted vcs commands and persist
    # FIXME: Needs sanitizing
    vcs_data = {
      "items": [{"cmd": cmd} for cmd in request.form.getlist("vcs_cmd[]")],
      "comment": request.form.get("comment", "")
    }
    _persist_session_subdocument_ts({"vcs": vcs_data})

    # We are done here, let's go to the next page
    flash("Success! Now let's see how you build your software...",
        "alert-success")
    return redirect(url_for("building"))

  user_data = _get_session_subdocument("vcs")
  return render_template("versioning.html", options=options,
      user_data=user_data)


@app.route("/building", methods=["GET", "POST"])
@with_session_id
def building():
  """Step 2.
  Enter information about building. """
  options = tooldb.collection["building"]

  if request.method == "POST":
    # Grab the form posted building commands and persist
    # FIXME: Needs sanitizing
    building_data = {
      "items": [{"cmd": cmd} for cmd in request.form.getlist("build_cmd[]")],
      "comment": request.form.get("comment", "")
    }
    _persist_session_subdocument_ts({"building": building_data})

    flash("Success! Let's talk about quality management next...",
        "alert-success")
    return redirect(url_for("quality_management"))

  user_data = _get_session_subdocument("building")
  return render_template("building.html", options=options, user_data=user_data)


@app.route("/quality", methods=["GET", "POST"])
@with_session_id
def quality_management():
  """Step 3.
  Enter information about quality management. """
  options = tooldb.collection["qa"]

  if request.method == "POST":
    # Grab the form posted quality management data and persist
    # FIXME: Needs sanitizing
    cmd_list = request.form.getlist("cmd[]")

    retval_include_list = request.form.getlist("retval_include[]")
    retval_operator_list = request.form.getlist("retval_operator[]")
    retval_value_list = request.form.getlist("retval_value[]")

    stdout_include_list = request.form.getlist("stdout_include[]")
    stdout_operator_list = request.form.getlist("stdout_operator[]")
    stdout_value_list = request.form.getlist("stdout_value[]")

    stderr_include_list = request.form.getlist("stderr_include[]")
    stderr_operator_list = request.form.getlist("stderr_operator[]")
    stderr_value_list = request.form.getlist("stderr_value[]")

    # Values of a step are related by the same index
    # All lists should be equally long
    # FIXME: Don't assert, try!
    assert(len(cmd_list) ==
        len(retval_include_list) == len(retval_operator_list) ==
        len(retval_value_list) == len(stdout_include_list) ==
        len(stdout_operator_list) == len(stdout_value_list) ==
        len(stderr_include_list) == len(stderr_operator_list) ==
        len(stderr_value_list))

    qa_steps_cnt = len(cmd_list)

    # There can only be one comment
    posted_coment = request.form.get("comment", "")

    posted_items = []
    for i in range(qa_steps_cnt):
      posted_items.append({
          "cmd": cmd_list[i],
          "retval": retval_include_list[i] == "true",
          "retval_operator": retval_operator_list[i],
          "retval_value": retval_value_list[i],
          "stdout": stdout_include_list[i] == "true",
          "stdout_operator": stdout_operator_list[i],
          "stdout_value": stdout_value_list[i],
          "stderr": stderr_include_list[i] == "true",
          "stderr_operator": stderr_operator_list[i],
          "stderr_value": stderr_value_list[i],
        })

    qa_data = {
      "items": posted_items,
      "comment": posted_coment
    }
    _persist_session_subdocument_ts({"qa": qa_data})

    flash("Success! Nice quality management, but how to you package"
        " up your software?", "alert-success")
    return redirect(url_for("packaging"))

  user_data = _get_session_subdocument("qa")
  return render_template("quality.html", options=options, user_data=user_data)


@app.route("/packaging", methods=["GET", "POST"])
@with_session_id
def packaging():
  """Step 4.
  Enter information about packaging. """
  options = tooldb.collection["package"]

  if request.method == "POST":
    # Grab the form posted building commands and persist
    # FIXME: Needs sanitizing
    package_data = {
      "items": [{"cmd": cmd} for cmd in request.form.getlist("cmd[]")],
      "comment": request.form.get("comment", "")
    }
    _persist_session_subdocument_ts({"package": package_data})

    flash("Success! Now let's see if we got your software supply chain right...",
        "alert-success")
    return redirect(url_for("software_supply_chain"))

  user_data = _get_session_subdocument("package")
  return render_template("packaging.html", options=options, user_data=user_data)


@app.route("/software-supply-chain", methods=["GET", "POST"])
@with_session_id
def software_supply_chain():
  """Step 5.
  Serve software supply chain graph based on form data posted on previous
  pages and stored to session (`session_to_graph`).
  Alternatively accepts a post request to override the generated software
  supply chain as edited in the here served form (`form_data_to_graph`).

  Latter will be used on subsequent pages.

  FIXMEs/TODOs:

  - Data sanitizing: e.g. restrict step names (unique) and inspection
    step names (must reference an existing step)
  """

  if request.method == "POST":
    step_names = request.form.getlist("step_name[]")
    step_commands = request.form.getlist("step_cmd[]")
    step_modifies = request.form.getlist("step_modifies[]")
    inspection_names = request.form.getlist("inspection_name[]")
    inspection_commands = request.form.getlist("inspection_cmd[]")
    inspection_step_names = request.form.getlist("inspection_step_name[]")

    comment = request.form.get("comment", "")

    # Names and Commands of a step or inspection are related by the same index
    # All lists should be equally long
    # FIXME: Don't assert, try!
    assert(len(step_names) == len(step_commands) == len(step_modifies))
    assert(len(inspection_names) == len(inspection_commands) ==
        len(inspection_step_names))

    # Create and persist software supply chain data from posted form
    ssc_data = form_data_to_ssc(step_names, step_commands, step_modifies,
        inspection_names, inspection_commands, inspection_step_names)
    ssc_data["comment"] = comment
    _persist_session_subdocument_ts({"ssc": ssc_data})

    return redirect(url_for("functionaries"))

  # Only re-generate software supply chain from data the user has posted on
  # previous pages, if there is no ssc data in the db or the user has sent
  # the `refresh` get parameter, otherwise serve existing ssc data


  show_refresh = False
  session_data = _get_session_document()
  ssc_data = session_data.get("ssc", {})
  ssc_last_modified = ssc_data.get("last_modified", 0)
  if not ssc_data or request.args.get("refresh"):
    ssc_data = session_to_ssc(session_data)

  else:
    # If existing ssc data is older than any of stored vcs/building/qa/package
    # datawe show a "do you want to re-generate
    # the software supply chain" dialog but serve the stored software supply
    # chain
    for subdocument in ["vcs", "building", "qa", "package"]:
      data_last_modified = session_data.get(subdocument,
          {}).get("last_modified", 0)
      if ssc_last_modified < data_last_modified:
        show_refresh = True
        break

  return render_template("software_supply_chain.html",
      ssc_data=ssc_data, show_refresh=show_refresh)


@app.route("/functionaries", methods=["GET", "POST"])
@with_session_id
def functionaries():
  """Step 6.
  On GET:
    Serve functionary keys upload and keys dropzone.
    Pubkeys are uploaded using ajax (c.f. ajax_upload_key)
  On POST:
    Store comment and redirect to next page"""
  functionaries = _get_session_subdocument("functionaries")
  if request.method == "POST":
    functionaries["comment"] = request.form.get("comment", "")
    _persist_session_subdocument({"functionaries": functionaries})

    flash("Great! Now tell us who is authorized to do what...",
        "alert-success")
    return redirect(url_for("authorizing"))

  return render_template("functionaries.html", functionaries=functionaries)


@app.route("/functionaries/upload", methods=["POST"])
@with_session_id
def ajax_upload_key():
  """Ajax upload a functionary key. """
  functionary_key = request.files.get("functionary_key", None)
  functionary_name = request.form.get("functionary_name", None)

  if not functionary_name:
    flash = {
      "msg": ("Something went wrong - we don't know which functionary,"
              " this key belongs to"),
      "type":  "alert-danger"
    }
    return jsonify({"flash": flash, "error": True})

  if not functionary_key:
    flash = {
      "msg": "Could not store uploaded file - No file uploaded",
      "type":  "alert-danger"
    }
    return jsonify({"flash": flash, "error": True})

  if functionary_key.filename == "":
    flash = {
      "msg": "Could not store uploaded file - No file selected",
      "type":  "alert-danger"
    }
    return jsonify({"flash": flash, "error": True})

  try:
    # We try to load the public key to check the format
    key = securesystemslib.keys.import_rsakey_from_public_pem(
        functionary_key.read())

    securesystemslib.formats.PUBLIC_KEY_SCHEMA.check_match(key)
    file_name = functionary_key.filename

    functionary_db_item = {
      "functionary_name": functionary_name,
      "file_name": file_name,
      "key_dict": key
    }

    # Clumsy update or insert for functionary array embedded subdocument
    # NOTE: Unfortunately we can't "upsert" on arrays but must first try to
    # update and if that does not work insert.
    # https://docs.mongodb.com/manual/reference/operator/update/positional/#upsert
    # https://stackoverflow.com/questions/23470658/mongodb-upsert-sub-document
    query_result = mongo.db.session_collection.update_one(
        {
          "_id": session["id"],
          "functionaries.items.functionary_name": functionary_name
        },
        {
          "$set": {"functionaries.items.$": functionary_db_item}
        })

    if not query_result.matched_count:
      query_result = mongo.db.session_collection.update_one(
          {
            "_id": session["id"],
            # This query part should deal with concurrent requests
            "functionaries.items.functionary_name": {"$ne": functionary_name}
          },
          {
            "$push": {"functionaries.items": functionary_db_item}
          }, upsert=True)

      msg = ("Successfully added key '{fn}' for functionary "
        "'{functionary}'.".format(fn=file_name, functionary=functionary_name))

    else:
      msg =("Successfully updated key '{fn}' for functionary "
        "'{functionary}'.".format(fn=file_name, functionary=functionary_name))

    # TODO: Throw more rocks at query_result

  except Exception as e:
    flash = {
      "msg": ("Could not store uploaded file. Error: {}".format(e)),
      "type":  "alert-danger"
    }
    return jsonify({"flash": flash, "error": True})

  else:
      flash = {
        "msg": msg,
        "type": "alert-success"
      }


  return jsonify({"flash": flash, "error": False})


@app.route("/functionaries/remove", methods=["POST"])
@with_session_id
def ajax_remove_functionary():
  """ Remove the posted functionary (by name) from the functionary session
  store.
  """
  functionary_name = request.form.get("functionary_name")

  try:
    # Remove the link entry with posted file name in the session
    # document's functionaries.items list
    query_result = mongo.db.session_collection.update_one(
        {"_id": session["id"]},
        {"$pull": {"functionaries.items":
          {"functionary_name": functionary_name}}})
    # TODO: Throw rocks at query_result

  except Exception as e:
    flash = {
      "msg": "Could not remove functionary '{name}'. {e}".
        format(name=functionary_name, e=e),
      "type": "alert-danger"
    }
    return jsonify({"flash": flash, "error": True})


  else:
    flash = {
      "msg": "Successfully removed functionary '{name}'.".
        format(name=functionary_name),
      "type": "alert-success"
    }
    return jsonify({"flash": flash, "error": False})


@app.route("/authorizing", methods=["GET", "POST"])
@with_session_id
def authorizing():
  """Step 7.
  Associate functionaries with steps. """

  if request.method == "POST":
    step_names = request.form.getlist("step_name[]")
    thresholds = request.form.getlist("threshold[]")
    comment = request.form.get("comment", "")

    # Steps names, commands and thresholds are related by the same index
    # These lists should be equally long
    # FIXME: Don't assert, try!
    assert(len(step_names) == len(thresholds))

    # The authorized functionaries multi select form element has the
    # respective step name in its name
    auth_items = []
    for idx, step_name in enumerate(step_names):
      functionaries_for_step = request.form.getlist(
          "functionary_name_" + step_name + "[]")

      auth_data = {
        "step_name": step_name,
        "threshold": int(thresholds[idx]),
        "authorized_functionaries": functionaries_for_step
      }
      auth_items.append(auth_data)

    # Validate, we validate after we have processed everything so we can
    # return all data to the form
    valid = True
    for auth_item in auth_items:
      if not auth_item["authorized_functionaries"]:
        valid = False
        flash("Step '{name}': Authorize at least one functionary!"
            .format(name=auth_item["step_name"]), "alert-danger")

      elif auth_item["threshold"] > len(auth_item["authorized_functionaries"]):
        valid = False
        flash(("Step '{name}': Threshold can't be higher than the "
            " number of authorized functionaries!")
            .format(name=auth_item["step_name"]), "alert-danger")

    if valid:
      flash("Success! It's time to do a test run of your software supply "
          "chain.", "alert-success")

      query_result = mongo.db.session_collection.update_one(
          { "_id": session["id"]},
          {"$set": {"authorizing.items": auth_items,
            "authorizing.comment": comment}})
      return redirect(url_for("chaining"))

    # if not valid we'll return below and the user can amend invalid data


  else: # request not POST
    authorizing = _get_session_subdocument("authorizing")
    auth_items = authorizing.get("items", [])
    comment = authorizing.get("comment", "")

  # We store auth data items to db as list
  # but in the templates we map the items to their respective step names
  auth_dict = _auth_items_to_dict(auth_items)

  session_functionaries = _get_session_subdocument("functionaries")
  session_steps = _get_session_subdocument("ssc").get("steps", [])
  return render_template("authorizing.html",
      functionaries=session_functionaries, steps=session_steps,
      auth_dict=auth_dict, comment=comment)


@app.route("/chaining", methods=["GET", "POST"])
@with_session_id
def chaining():
  """Step 8.
  On GET:
    Serve dry run snippet and link metadata upload.
    Link files are uploaded using ajax (c.f. ajax_upload_link)
  On POST:
    Store comment and redirect to next page."""

  chaining = _get_session_subdocument("chaining")
  steps = _get_session_subdocument("ssc").get("steps", [])

  if request.method == "POST":
    chaining["comment"] = request.form.get("comment", "")
    _persist_session_subdocument({"chaining": chaining})

    flash("Yeah! That's basically it... :)", "alert-success")
    return redirect(url_for("wrap_up"))

  return render_template("chaining.html", steps=steps, chaining=chaining)


@app.route("/chaining/upload", methods=["POST"])
@with_session_id
def ajax_upload_link():
  """Ajax upload link metadata. """
  uploaded_file = request.files.get("step_link", None)

  if not uploaded_file:
    flash = {
      "msg": "Could not store uploaded file - No file uploaded",
      "type":  "alert-danger"
    }
    return jsonify({"flash": flash, "error": True})

  if uploaded_file.filename == "":
    flash = {
      "msg": "Could not store uploaded file - No file selected",
      "type":  "alert-danger"
    }
    return jsonify({"flash": flash, "error": True})


  link_file_tuples = []
  # The uploaded file might be a tar archive so let's try to unpack it
  try:
    link_archive = tarfile.open(fileobj=uploaded_file)
    for tar_info in link_archive.getmembers():
      link_file = link_archive.extractfile(tar_info)
      link_file_tuples.append((tar_info.name, link_file))

  except tarfile.TarError as e:
    # If that does not work we assume the uploaded file was link
    link_file_tuples.append((uploaded_file.filename, uploaded_file))


  added_files = []
  messages = []
  msg_type = "alert-success"
  error = False
  # Now iterate over all files we have, try to load them as link and
  # store them to database
  for link_filename, link_file in link_file_tuples:
    try:
      link_dict = json.loads(link_file.read())
      # FIXME: in-toto links have no format validator (yet!)
      link = in_toto.models.mock_link.MockLink.read(link_dict)

      link_db_item = {
        "step_name": link.name,
        "file_name": link_filename,
        # NOTE: We can't store the dict representation of the link, because
        # MongoDB does not allow dotted keys, e.g.: "materials": {"foo.py": {...
        # hence we store it as canonical json string dump (c.f. link's __repr__)
        # NOTE: I wonder if we are prone to exceed the max document size (16 MB)
        # if we store all the session info in one document. Probably not.
        "link_str": repr(link)
      }

      # Push link item to the chaining.items array in the session document
      query_result = mongo.db.session_collection.update_one(
          {"_id": session["id"]},
          {"$push": {"chaining.items": link_db_item}},
          upsert=True)

      # TODO: Throw more rocks at query_result

    except Exception as e:
      error = True
      msg_type = "alert-danger"
      messages.append("Could not store '{}'. {}".format(link_filename, e))

    else:
      added_files.append(link_filename)
      messages.append("Successfully stored link '{file_name}' "
          "for step '{name}'!".format(file_name=link_filename, name=link.name))

  # FIXME: Joining all the messages and giving them one message type does not
  # look so good. We should change the JS show_message function to handle
  # a list of messages instead.

  flash = {
    "msg": " ".join(messages),
    "type": msg_type
  }
  return jsonify({"flash": flash, "error": error, "files": added_files})



@app.route("/chaining/remove", methods=["POST"])
@with_session_id
def ajax_remove_link():
  """ Remove the posted link by step name from the chaining session
  document.
  """
  link_filename = request.form.get("link_filename")
  try:
    # Remove the link entry with posted file name in the session
    # document's chaining.items list
    res = mongo.db.session_collection.update_one(
        {"_id": session["id"]},
        {"$pull": {"chaining.items": {"file_name": link_filename}}})
    # TODO: Throw rocks at query_result

  except Exception as e:
    flash = {
      "msg": "Could not remove link file '{link}', Error: '{e}'".format(
          link=link_filename, e=e),
      "type": "alert-danger"
    }
    return jsonify({"flash": flash, "error": True})

  else:
    flash = {
      "msg": "Successfully removed link file '{link}'!".format(
          link=link_filename),
      "type": "alert-success"
    }

  return jsonify({"flash": flash, "error": False})


@app.route("/wrap-up")
@with_session_id
def wrap_up():
  """Step 9.
  Explain what to do with generated layout.
   - Download layout
   - Create project owner key (keygen snippet)
   - Sign layout (signing snippet)
   - Per functionary commands (in-toto-run snippet)
   - Release instructions ??
  """
  functionaries = _get_session_subdocument("functionaries")
  auth_items = _get_session_subdocument("authorizing").get("items", [])
  auth_dict = _auth_items_to_dict(auth_items)

  steps = _get_session_subdocument("ssc").get("steps", [])
  return render_template("wrap_up.html", steps=steps, auth_dict=auth_dict,
      functionaries=functionaries)


@app.route("/download-layout")
@with_session_id
def download_layout():
  """Create layout based on session data and uploaded links and
  serve.

  TODO: Move out layout creation functionality to reverse_layout.py
  """
  # Iterate over items in ssc session document and create an ordered list
  # of according link objects retrieved from the chaining session document
  session_ssc = _get_session_subdocument("ssc")
  session_chaining = _get_session_subdocument("chaining")
  links = []
  for step in session_ssc.get("steps", []):
    for link_data in session_chaining.get("items", []):
      if link_data["step_name"] == step["name"]:
        link = in_toto.models.mock_link.MockLink.read(json.loads(
            link_data["link_str"] ))
        links.append(link)

  # Create basic layout with steps based on links
  layout = reverse_layout.create_layout_from_ordered_links(links)

  # Add pubkeys and authorization to layout
  functionary_keyids = {}

  # Add uploaded functionary pubkeys to layout
  for functionary in _get_session_subdocument("functionaries").get("items", []):
    key = functionary.get("key_dict")
    functionary_name = functionary.get("functionary_name")

    # Check the format of the uploaded public key
    # TODO: Handle invalid key
    securesystemslib.formats.PUBLIC_KEY_SCHEMA.check_match(key)

    # Add keys to layout's key store
    layout.keys[key["keyid"]] = key

    # Add keys to functionary name-keyid map needed below
    functionary_keyids[functionary_name] = key["keyid"]

  auth_items = _get_session_subdocument("authorizing").get("items", [])
  auth_dict = _auth_items_to_dict(auth_items)

  # Add authorized functionaries to steps and set signing threshold
  for idx in range(len(layout.steps)):
    step_name = layout.steps[idx].name
    auth_data = auth_dict.get(step_name)

    for functionary_name in auth_data.get("authorized_functionaries", []):
      keyid = functionary_keyids.get(functionary_name)
      if keyid:
        layout.steps[idx].pubkeys.append(keyid)

    layout.steps[idx].threshold = auth_data.get("threshold")

  # Add inspections to layout
  inspections = session_ssc.get("inspections", [])
  for inspection_data in inspections:
    inspection = in_toto.models.layout.Inspection(
        name=inspection_data["name"],
        run=inspection_data["cmd"],
        material_matchrules=[
          ["MATCH", "*", "WITH", "PRODUCTS", "FROM", inspection_data["based_on"]]
        ])

    layout.inspect.append(inspection)

  layout.validate()
  layout_name = "untitled-" + str(time.time()).replace(".", "") + ".layout"

  # Dump layout to memory file and server to user
  layout_fp = StringIO.StringIO()
  layout_fp.write("{}".format(layout))
  layout_fp.seek(0)
  return send_file(layout_fp,
      mimetype="application/json", as_attachment=True,
      attachment_filename=layout_name)


@app.route("/guarantees")
@with_session_id
def guarantees():
  """ Show what the software supply chain protects against and give advice for
  more guarantees. """
  return render_template("guarantees.html")

if __name__ == "__main__":
  app.run()
