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

from functools import wraps
from flask import (Flask, render_template, session, redirect, url_for, request,
    flash, send_from_directory, abort, json, jsonify)
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
    # FIXME: Isolate files per session like in old version of tool
    USER_FILES=os.path.join(os.path.dirname(os.path.abspath(__file__)), "files"),
))

# Supply a config file at "instance/config.py" that carries
# e.g. your deployment secret key
app.config.from_pyfile("config.py")

# -----------------------------------------------------------------------------
# Utils
# -----------------------------------------------------------------------------
# def layout_to_graph(layout):
#   """
#   <Purpose>
#     Takes an in-toto layout and transforms it to a data structure that's more
#     convenient to create a graph from it, e.g. using `dagre-d3` [1]:

#     Note:
#       We do this on server-side to make use of in-toto functions like
#       `artifact_rules.unpack_rule`.
#   <Returns>
#     {
#       "nodes": [{
#         "name": <unique step or inspection name">,
#         "type": "step" | "inspection"
#       }, ...]
#       "edges": [{
#         "source": <unique step or inspection name">,
#         "source_type": "M" | "P",
#         "dest": <unique step or inspection name">,
#         "dest_type": "M" | "P",
#       }, ...]
#     }
#   """
#   graph_data = {
#     "nodes": [],
#     "edges": []
#   }

#   def _get_edges(src_type, src_name, rules):
#     """ Returns edges (list) based on passed list of material_matchrules ("M")
#     or product_matchrules ("P"). """

#     edges = []
#     for rule in rules:
#       # Parse rule list into dictionary
#       rule_data = in_toto.artifact_rules.unpack_rule(rule)

#       # Only "MATCH" rules are used as edges
#       if rule_data["type"].upper() == "MATCH":

#         # We can pass additional information here if we want
#         edges.append({
#             "source": src_name,
#             "source_type": src_type,
#             "dest": rule_data["dest_name"],
#             "dest_type": rule_data["dest_type"][0].upper() # "M" | "P"
#           })

#     return edges

#   # Create nodes from steps and inspections
#   for item in layout.steps + layout.inspect:
#     graph_data["nodes"].append({
#         "name": item.name,
#         "type": item._type
#       })

#     # Create edges from material- and product- matchrules
#     graph_data["edges"] += _get_edges("M", item.name, item.material_matchrules)
#     graph_data["edges"] += _get_edges("P", item.name, item.product_matchrules)

#   return graph_data


def session_to_ssc(session_data):
  """
  <Purpose>
    Takes a session document, which can contain form posted data from previous
    pages (vcs, building, qa, ...) to generate a dict of lists of step data and
    inspection data dicts.

  <Returns>
    Software Supply Chain Data, i.e. a dictionary of step and inspection data
    (these are not not actual in-toto Step and Insepction objects), e.g.:
    {
      steps: [
        {
          "name": <unique step name>,
          "cmd": <expected command>
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
  inspections = []

  for step_type in ["vcs", "building", "qa", "package"]:
    for idx, step in enumerate(session_data.get(step_type, {}).get(
        "items", [])):
      # FIXME: Come up with better naming (low priority)
      step_name = "{}-{}".format(step_type, idx + 1)
      steps.append({
        "name": step_name,
        "cmd" : step["cmd"],
        # "step_type": "vcs" | "buiding" | "qa" | "package"
      })

      # We suggest an inspection for each set retval, stdout and stderr for
      # each specified QA step
      if step_type == "qa":
        for inspect_type in ["retval", "stdout", "stderr"]:
          val = step.get(inspect_type + "_value")
          operator = step.get(inspect_type + "_operator")

          if (val != None and operator != None):
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

            inspect_name = "inspection-" + str(len(inspections) + 1)
            inspections.append({
              "name": inspect_name,
              "cmd": run,
              "based_on": step_name
            })

  ssc_data = {
    "steps": steps,
    "inspections": inspections
  }
  return ssc_data

def form_data_to_ssc(step_names, step_commands, inspection_names,
    inspection_commands, inspection_step_names):
  """
  <Purpose>
    Takes form posted data (lists) to generate a dict of lists of step data and
    inspection data dicts.
    Each item aggregates the step or inspection data by list index

  <Returns>
    Software Supply Chain Data, i.e. a dictionary of step and inspection data
    (these are not not actual in-toto Step and Insepction objects), e.g.:
    {
      steps: [
        {
          "name": <unique step name>,
          "cmd": <expected command>
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
        # We need a step type to know how to link the steps
        # e.g. qa steps don't have products
        # "step_type": "vcs" | "buiding" | "qa" | "package"
        # or
        # "step_type": "reporting" | "modifying"
        # What if the user adds new steps here (i.e. we don't know the type)?
        # Should we ask the user?
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
# NoSQL Helpers
# -----------------------------------------------------------------------------

# NOTE:
# Below functions rely on the current session having an id. If there is no id
# in the session, all fucntions redirect to `404`.
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
    retval_operator_list = request.form.getlist("retval_operator[]")
    retval_value_list = request.form.getlist("retval_value[]")
    stdout_operator_list = request.form.getlist("stdout_operator[]")
    stdout_value_list = request.form.getlist("stdout_value[]")
    stderr_operator_list = request.form.getlist("stderr_operator[]")
    stderr_value_list = request.form.getlist("stderr_value[]")

    # Values of a step are related by the same index
    # All lists should be equally long
    # FIXME: Don't assert, try!
    assert(len(cmd_list) ==
        len(retval_operator_list) == len(retval_value_list) ==
        len(stdout_operator_list) == len(stdout_value_list) ==
        len(stderr_operator_list) == len(stderr_value_list))

    qa_steps_cnt = len(cmd_list)

    # There can only be one comment
    posted_coment = request.form.get("comment", "")

    posted_items = []
    for i in range(qa_steps_cnt):
      posted_items.append({
          "cmd": cmd_list[i],
          "retval_operator": retval_operator_list[i],
          "retval_value": retval_value_list[i],
          "stdout_operator": stdout_operator_list[i],
          "stdout_value": stdout_value_list[i],
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
# @app.route("/software-supply-chain/refresh", methods=["GET"])
@with_session_id
def software_supply_chain(refresh=False):
  """Step 5.
  Serve software supply chain graph based on form data posted on previous
  pages and stored to session (`session_to_graph`).
  Alternatively accepts a post request to override the generated software
  supply chain as edited in the here served form (`form_data_to_graph`).

  Latter will be used on subsequent pages.

  FIXMEs/TODOs:

  - Data sanatizing: e.g. restrict step names (unique) and inspection
    step names (must reference an existing step)
  - On front-end JS: refresh D3 graph on form change
  - DRY up graph generation functions: session_to_graph, form_data_to_graph,
    layout_to_graph (commented out)
  """

  if request.method == "POST":
    step_names = request.form.getlist("step_name[]")
    step_commands = request.form.getlist("step_cmd[]")
    inspection_names = request.form.getlist("inspection_name[]")
    inspection_commands = request.form.getlist("inspection_cmd[]")
    inspection_step_names = request.form.getlist("inspection_step_name[]")

    # Names and Commands of a step or inspection are related by the same index
    # All lists should be equally long
    # FIXME: Don't assert, try!
    assert(len(step_names) == len(step_commands))
    assert(len(inspection_names) == len(inspection_commands) ==
        len(inspection_step_names))

    # Create and persist software supply chain data from posted form
    ssc_data = form_data_to_ssc(step_names, step_commands,
        inspection_names, inspection_commands, inspection_step_names)
    _persist_session_subdocument_ts({"ssc": ssc_data})

    return redirect(url_for("functionaries"))


  session_data = _get_session_document()
  ssc_data = session_data.get("ssc", {})
  ssc_last_modified = ssc_data.get("last_modified", 0)

  # If stored ssc data is older than any of stored
  # vcs/building/qa/package data, we (re-)generate the software supply chain,
  # otherwise we serve the stored software supply chain
  # If an entry does not exist the last_modified property is 0
  for step_type in ["vcs", "building", "qa", "package"]:
    data_last_modified = session_data.get(step_type, {}).get("last_modified", 0)
    if ssc_last_modified < data_last_modified:
      ssc_data = session_to_ssc(session_data)
      break

  # TODO: Maybe we shouldn't auto RE-generate but ask user for confirmation

  return render_template("software_supply_chain.html",
      ssc_data=ssc_data)


@app.route("/functionaries")
@with_session_id
def functionaries():
  """Step 6.
  Functionary keys upload and keys dropzone. """
  functionaries = _get_session_subdocument("functionaries")
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
    securesystemslib.keys.import_rsakey_from_public_pem(
        functionary_key.read())

    # Reset the filepointer
    functionary_key.seek(0)

  except Exception as e:
    flash = {
      "msg": "Could not store uploaded file - Not a valid public key",
      "type":  "alert-danger"
    }
    return jsonify({"flash": flash, "error": True})

  else:
    fn = functionary_key.filename
    functionary_key_path = os.path.join(app.config["USER_FILES"], fn)
    functionary_key.save(functionary_key_path)

  # FIXME: Fix race condition!
  functionary_data = _get_session_subdocument("functionaries")
  functionary_data[functionary_name] = fn
  _persist_session_subdocument({"functionaries": functionary_data})

  flash = {
    "msg": "Successfully uploaded key '{fn}' for functionary '{functionary}'!".
      format(fn=fn, functionary=functionary_name),
    "type": "alert-success"
  }
  return jsonify({"flash": flash, "error": False})


@app.route("/functionaries/remove", methods=["POST"])
@with_session_id
def ajax_remove_key():
  """ Remove the posted functionary (by name) from the functionary session
  store.

  FIXME: We probably should also remove the key file
  """
  functionary_name = request.form.get("functionary_name", None)

  # FIXME: Fix race condition
  functionary_data = _get_session_subdocument("functionaries")
  if functionary_name in functionary_data:
    del functionary_data[functionary_name]
    _persist_session_subdocument({"functionaries": functionary_data})

    flash = {
      "msg": "Successfully removed functionary '{functionary}'!".
        format(functionary=functionary_name),
      "type": "alert-success"
    }
    error = False

  else:
    flash = {
      "msg": "Could not remove non-existing functionary '{functionary}'!".
        format(functionary=functionary_name),
      "type": "alert-danger"
    }
    error = True

  return jsonify({"flash": flash, "error": error})



@app.route("/authorizing", methods=["GET", "POST"])
@with_session_id
def authorizing():
  """Step 7.
  Associate functionaries with steps. """

  # This is needed for POST and GET requests
  session_functionaries = _get_session_subdocument("functionaries")
  session_authorizing = _get_session_subdocument("authorizing")
  session_steps = _get_session_subdocument("ssc").get("steps", [])

  if request.method == "POST":
    step_names = request.form.getlist("step_name[]")
    thresholds = request.form.getlist("threshold[]")

    # Steps names, commands and thresholds are related by the same index
    # These lists should be equally long
    # FIXME: Don't assert, try!
    assert(len(step_names) == len(thresholds))

    # The authorized functionaries multi select form element has the
    # respective step name in its name
    for idx, step_name in enumerate(step_names):
      functionaries_for_step = request.form.getlist(
          "functionary_name_" + step_name + "[]")

      auth_data = {
        "threshold": int(thresholds[idx]),
        "authorized_functionaries": functionaries_for_step
      }

      session_authorizing[step_name] = auth_data

    # Validate, we validate after we have processed everything so we can
    # return all data to the form
    valid = True
    for step_name, step_data in session_authorizing.iteritems():
      if not step_data.get("authorized_functionaries", []):
        valid = False
        flash("Step '{name}': Authorize at least one functionary!"
            .format(name=step_name), "alert-danger")

      elif step_data["threshold"] > len(step_data.get("authorized_functionaries",
          [])):
        valid = False
        flash(("Step '{name}': Threshold can't be higher than the "
            " number of authorized functionaries!").format(name=step_name),
                "alert-danger")

    if valid:
      flash("Success! It's time to do a test run of your software supply "
          "chain.", "alert-success")
      _persist_session_subdocument({"authorizing": session_authorizing})
      return redirect(url_for("chaining"))

    #If not valid return to form so that the user can fix the errors

  return render_template("authorizing.html",
      functionaries=session_functionaries, steps=session_steps,
      authorizing=session_authorizing)


@app.route("/chaining")
@with_session_id
def chaining():
  """Step 8.
  Dry run snippet and link metadata upload. """
  steps = _get_session_subdocument("ssc").get("steps", [])
  links = _get_session_subdocument("chaining")
  return render_template("chaining.html", steps=steps, link_dict=links)


@app.route("/chaining/upload", methods=["POST"])
@with_session_id
def ajax_upload_link():
  """Ajax upload link metadata. """
  link_file = request.files.get("step_link", None)

  if not link_file:
    flash = {
      "msg": "Could not store uploaded file - No file uploaded",
      "type":  "alert-danger"
    }
    return jsonify({"flash": flash, "error": True})

  if link_file.filename == "":
    flash = {
      "msg": "Could not store uploaded file - No file selected",
      "type":  "alert-danger"
    }
    return jsonify({"flash": flash, "error": True})

  try:
    # We try to load the public key to check the format
    link_dict = json.loads(link_file.read())
    link = in_toto.models.mock_link.MockLink.read(link_dict)

    # Reset the filepointer
    link_file.seek(0)

  except Exception as e:
    flash = {
      "msg": "Could not store '{}': Not a valid Link file. {}".format(
          link_file.filename, e),
      "type":  "alert-danger"
    }
    return jsonify({"flash": flash, "error": True})

  else:
    fn = link_file.filename
    path = os.path.join(app.config["USER_FILES"], fn)
    link_file.save(path)

  # FIXME: Fix race condition
  session_chaining = _get_session_subdocument("chaining")
  session_chaining[link.name] = fn
  _persist_session_subdocument({"chaining": session_chaining})

  flash = {
    "msg": "Successfully uploaded link '{fn}' for step '{name}'!".
      format(fn=fn, name=link.name),
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
  functionaries = _get_session_subdocument("functionaries").keys()
  auths = _get_session_subdocument("authorizing")
  steps = _get_session_subdocument("ssc").get("steps", [])
  return render_template("wrap_up.html", steps=steps, auths=auths,
      functionaries=functionaries)


@app.route("/download-layout")
@with_session_id
def download_layout():
  """Create layout based on session data and uploaded links and
  serve with layout name from session directory as attachment
  (Content-Disposition: attachment).

  TODO: Move out layout creation functionality to reverse_layout.py
  """
  # Iterate over items in ssc dictionary and create an ordered list
  # of according link objects
  session_ssc = _get_session_subdocument("ssc")
  session_chaining = _get_session_subdocument("chaining")

  links = []
  inspections = session_ssc.get("inspections", [])

  for item in session_ssc.get("steps", []):
    link_filename = session_chaining.get(item["name"])

    if not link_filename:
      continue

    link_path = os.path.join(app.config["USER_FILES"], link_filename)

    if not os.path.exists(link_path):
      continue

    link = in_toto.models.mock_link.MockLink.read_from_file(link_path)
    links.append(link)


  # Create basic layout with steps based on links
  layout = reverse_layout.create_layout_from_ordered_links(links)

  # Add pubkeys and authorization to layout
  functionary_keyids = {}

  # Add uploaded functionary pubkeys to layout
  for functionary_name, pubkey_fn in _get_session_subdocument(
      "functionaries").iteritems():

    # Load and check the format of the uploaded public keys
    pubkey_path = os.path.join(app.config["USER_FILES"], pubkey_fn)
    key = in_toto.util.import_rsa_key_from_file(pubkey_path)
    securesystemslib.formats.PUBLIC_KEY_SCHEMA.check_match(key)

    # Add keys to layout's key store
    layout.keys[key["keyid"]] = key

    # Add keys to functionary name-keyid map needed below
    functionary_keyids[functionary_name] = key["keyid"]

  # Add authorized functionaries to steps and set signing threshold
  for idx in range(len(layout.steps)):
    step_name = layout.steps[idx].name
    auth_data = _get_session_subdocument("authorizing").get(step_name, {})

    for functionary_name in auth_data.get("authorized_functionaries", []):
      keyid = functionary_keyids.get(functionary_name)
      if keyid:
        layout.steps[idx].pubkeys.append(keyid)

    layout.steps[idx].threshold = auth_data.get("threshold")

  # Add inpsections to layout
  for inspection_data in inspections:
    inspection = in_toto.models.layout.Inspection(
        name=inspection_data["name"],
        run=inspection_data["cmd"],
        material_matchrules=[
          ["MATCH", "*", "WITH", "PRODUCTS", "FROM", inspection_data["based_on"]]
        ])

    layout.inspect.append(inspection)

  layout.validate()
  # TODO: Use a dyniamic name?
  layout_name = "root.layout"
  layout_path = os.path.join(app.config["USER_FILES"], layout_name)
  layout.dump(layout_path)

  # Serve file
  return send_from_directory(app.config["USER_FILES"], layout_name,
      as_attachment=True)

@app.route("/guarantees")
@with_session_id
def guarantees():
  """ Show what the software supply chain protects against and give advice for
  more guarantees. """
  return render_template("guarantees.html")

if __name__ == "__main__":
  app.run()
