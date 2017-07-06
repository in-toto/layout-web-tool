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
from flask import (Flask, render_template, session, redirect, url_for, request,
    flash, send_from_directory, abort, json, jsonify)

import in_toto.util
import in_toto.models.link
import in_toto.models.mock_link
import in_toto.artifact_rules
import securesystemslib.keys

import tooldb
import reverse_layout

app = Flask(__name__, static_url_path="", instance_relative_config=True)

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


def session_to_graph(session):
  """
  <Purpose>
    Takes an the session and transforms it to a data structure that's more
    convenient to create a graph from it, e.g. using `dagre-d3` [1]:

  <Returns>
    {
      "nodes": [{
        "type": "step" | "inspection",
        "name": <unique step or inspection name">,
        "based_on" <step name> # Only for inspections!!!!
      }, ...],
      "edges": [{
        "source": <unique step or inspection name">,
        "dest": <unique step or inspection name">,
      }, ...]
    }
  """
  step_nodes = []
  step_edges = []
  inspect_nodes = []
  inspect_edges = []

  # Create edges based on data posted from previous pages
  # FIXME: Come up with better naming (low priority)
  for step_type in ["vcs", "building", "qa", "package"]:
    for idx, step in enumerate(session.get(step_type, {}).get("items", [])):
      step_name = "{}-{}".format(step_type, idx + 1)
      step_nodes.append({
        "type": "step",
        "name": step_name,
        "cmd" : step["cmd"],
      })

      # We suggest an inspection for each set retval, stdout and stderr for each
      # specified QA step
      if step_type == "qa":
        for inspect_type in ["retval", "stdout", "stderr"]:
          val = step.get(inspect_type + "_value")
          if val:
            # The (QA) link file we want to inspect uses the link step name
            # created above
            link = in_toto.models.link.FILENAME_FORMAT_SHORT.format(
                step_name=step_name)
            operator = step.get(inspect_type + "_operator")
            value = step.get(inspect_type + "_value")

            if inspect_type == "retval":
              run = ("inspect-return-value --link={link} --{operator} {value}"
                  .format(link=link, operator=operator, value=value))

            elif inspect_type in ["stdout", "stderr"]:
              run = ("inspect-by-product"
                  " --link={link} --{inspect_type} --{operator} {value}"
                  .format(link=link, inspect_type=inspect_type,
                  operator=operator, value=value))

            inspect_name = "inspection-" + str(len(inspect_nodes) + 1)
            inspect_nodes.append({
              "type": "inspection",
              "name": inspect_name,
              "cmd": run,
              "based_on": step_name
            })

            inspect_edges.append({
              "source": step_name,
              "dest": inspect_name
            })

  # For now we assume that steps are executed sequentially
  # And that's how we connect the steps
  for idx in range(len(step_nodes)):
    if idx > 0:
      step_edges.append({
          "source": step_nodes[idx-1]["name"],
          "dest": step_nodes[idx]["name"]
        })

  return {
    "nodes": step_nodes + inspect_nodes,
    "edges": step_edges + inspect_edges
  }


def form_data_to_graph(step_names, step_commands, inspection_names,
    inspection_commands, inspection_step_names):
  """
  <Purpose>
    Takes form posted data (lists) to generate a data structure that's more
    convenient to create a graph from it, e.g. using `dagre-d3` [1]:

    Each node aggregates the the step or inspection data by list index

  <Returns>
    {
      "nodes": [{
        "type": "step" | "inspection",
        "name": <unique step or inspection name">,
        "based_on" <step name> # Only for inspections!!!!
      }, ...],
      "edges": [{
        "source": <unique step or inspection name">,
        "dest": <unique step or inspection name">,
      }, ...]
    }
  """
  # Generate ssc_graph based on data posted on the ssc page
  # FIXME: Some of this is similar to code in `session_to_graph`. DRY?
  step_nodes = []
  step_edges = []
  for i in range(len(step_names)):
    step_nodes.append({
        "type": "step",
        "name": step_names[i],
        "cmd": step_commands[i]
      })

  for idx in range(len(step_nodes)):
    if idx > 0:
      step_edges.append({
          "source": step_nodes[idx-1]["name"],
          "dest": step_nodes[idx]["name"]
        })

  inspect_nodes = []
  inspect_edges = []
  for i in range(len(inspection_names)):
    inspect_nodes.append({
        "type": "inspection",
        "name": inspection_names[i],
        "cmd": inspection_commands[i],
        "based_on": inspection_step_names[i]
      })

    inspect_edges.append({
      "source": inspection_step_names[i],
      "dest": inspection_names[i]
    })

  return {
    "nodes": step_nodes + inspect_nodes,
    "edges": step_edges + inspect_edges
  }

# -----------------------------------------------------------------------------
# Views
# -----------------------------------------------------------------------------
@app.route("/")
def start():
  """Step 0.
  Wizard entry point, static landing page. """
  return render_template("start.html")


@app.route("/versioning", methods=["GET", "POST"])
def versioning():
  """Step 1.
  Enter information about version control system. """
  options = tooldb.collection["vcs"]

  if request.method == "POST":
    # Grab the form posted vcs commands and write it to the session
    # FIXME: Needs sanitizing and session persistence!!!
    session["vcs"] = {
      "items": [{"cmd": cmd} for cmd in request.form.getlist("vcs_cmd[]")],
      "comment": request.form.get("comment", "")
    }

    flash("Success! Now let's see how you build your software...", "alert-success")
    return redirect(url_for("building"))

  # The template can deal with an empty dict, but a dict it must be
  user_data = session.get("vcs", {})

  return render_template("versioning.html", options=options, user_data=user_data)


@app.route("/building", methods=["GET", "POST"])
def building():
  """Step 2.
  Enter information about building. """
  options = tooldb.collection["building"]

  if request.method == "POST":
    # Grab the form posted building commands and write it to the session
    # FIXME: Needs sanitizing and session persistence!!!
    session["building"] = {
      "items": [{"cmd": cmd} for cmd in request.form.getlist("build_cmd[]")],
      "comment": request.form.get("comment", "")
    }

    flash("Success! Let's talk about quality management next...", "alert-success")
    return redirect(url_for("quality_management"))

  # The template can deal with an empty dict, but a dict it must be
  user_data = session.get("building", {})

  return render_template("building.html", options=options, user_data=user_data)


@app.route("/quality", methods=["GET", "POST"])
def quality_management():
  """Step 3.
  Enter information about quality management. """
  options = tooldb.collection["qa"]

  if request.method == "POST":
    # Grab the form posted quality management data  and write it to the session
    # FIXME: Needs sanitizing and session persistence!!!
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

    session["qa"] = {
      "items": posted_items,
      "comment": posted_coment
    }

    flash("Success! Nice quality management, but how to you package up your software?", "alert-success")
    return redirect(url_for("packaging"))

  # The template can deal with an empty dict, but a dict it must be
  user_data = session.get("qa", {})

  return render_template("quality.html", options=options, user_data=user_data)

@app.route("/packaging", methods=["GET", "POST"])
def packaging():
  """Step 4.
  Enter information about packaging. """
  options = tooldb.collection["package"]

  if request.method == "POST":
    # Grab the form posted building commands and write it to the session
    # FIXME: Needs sanitizing and session persistence!!!
    session["package"] = {
      "items": [{"cmd": cmd} for cmd in request.form.getlist("cmd[]")],
      "comment": request.form.get("comment", "")
    }

    flash("Success! Now let's see if we got your software supply chain right...", "alert-success")
    return redirect(url_for("software_supply_chain"))

  # The template can deal with an empty dict, but a dict it must be
  user_data = session.get("package", {})

  return render_template("packaging.html", options=options, user_data=user_data)


@app.route("/software-supply-chain", methods=["GET", "POST"])
def software_supply_chain():
  """Step 5.
  Serve software supply chain graph based on form data posted on previous
  pages and stored to session (`session_to_graph`).
  Alternatively accepts a post request to override the generated software
  supply chain as edited in the here served form (`form_data_to_graph`).

  Latter will be used on subsequent pages.

  FIXMEs/TODOs:

  - Data sanatizing: e.g. restrict step names (unique) and inspection
    step names (must reference an existing step)
  - Decide how to prioritize graph data
    What if a user GET requests this page and the graph generated by using
    form data from previous pages (vcs, build, ...) is different from the
    graph as edited in the ssc form (`session["ssc"]`)?
    Show we ask the user which one he wants to use?
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

    supply_chain = form_data_to_graph(step_names, step_commands,
        inspection_names, inspection_commands, inspection_step_names)

    session["ssc"] = supply_chain

    return redirect(url_for("functionaries"))

  # If not POST request
  # Generate a supply chain based on previously posted data (stored in session)
  # TODO: This overrides anything that was from the ssc form
  # Should we ask for confirmation?
  supply_chain = session_to_graph(session)

  return render_template("software_supply_chain.html",
      ssc_graph_data=supply_chain)


@app.route("/functionaries")
def functionaries():
  """Step 6.
  Functionary keys upload and keys dropzone. """
  functionaries = session.get("functionaries", {})

  return render_template("functionaries.html", functionaries=functionaries)


@app.route("/functionaries/upload", methods=["POST"])
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

  session_functionaries = session.get("functionaries", {})
  session_functionaries[functionary_name] = fn
  session["functionaries"] = session_functionaries

  flash = {
    "msg": "Successfully uploaded key '{fn}' for functionary '{functionary}'!".
      format(fn=fn, functionary=functionary_name),
    "type": "alert-success"
  }
  return jsonify({"flash": flash, "error": False})


@app.route("/functionaries/remove", methods=["POST"])
def ajax_remove_key():
  """ Remove the posted functionary (by name) from the functionary session
  store.
  FIXME: We probably should also remove the key file
  """
  functionary_name = request.form.get("functionary_name", None)
  session_functionaries = session.get("functionaries", {})
  if functionary_name in session_functionaries:
    del session_functionaries[functionary_name]
    session["functionaries"] = session_functionaries
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
def authorizing():
  """Step 7.
  Associate functionaries with steps. """

  if request.method == "POST":
    step_names = request.form.getlist("step_name[]")
    step_cmds = request.form.getlist("step_cmd[]")
    thresholds = request.form.getlist("threshold[]")

    # Steps names, commands and thresholds are related by the same index
    # These lists should be equally long
    # FIXME: Don't assert, try!
    assert(len(step_names) == len(step_cmds) == len(thresholds))

    # The authorized functionaries multi select form element has the
    # respective step name in its name
    session_authorizing = session.get("authorizing", {})
    for idx, step_name in enumerate(step_names):
      functionaries_for_step = request.form.getlist(
          "functionary_name_" + step_name + "[]")

      session_authorizing[step_name] = {
        "cmd": step_cmds[idx],
        "threshold": int(thresholds[idx]),
        "authorized_functionaries": functionaries_for_step
      }

    # Validate
    # We validate after we have processed everything so we can return all data
    # to the form

    valid = True
    for step_name, step_data in session_authorizing.iteritems():
      if not step_data.get("authorized_functionaries", []):
        valid = False
        flash("Step '{name}': Authorize at least one functionary!"
            .format(name=step_name), "alert-danger")

      if step_data["threshold"] > len(step_data.get("authorized_functionaries", [])):
        valid = False
        flash(("Step '{name}': Threshold can't be higher than the "
            " number of authorized functionaries!").format(name=step_name),
                "alert-danger")

    if valid:
      flash("Success! It's time to do a test run of your software supply chain.", "alert-success")
      session["authorizing"] = session_authorizing
      return redirect(url_for("chaining"))

    else:
      # Return to form so that the user can fix the errors
      return render_template("authorizing.html", steps=session_authorizing,
        functionaries=session.get("functionaries", {}))


  nodes = session.get("ssc", {}).get("nodes", [])
  # FIXME: Probably we should have two different steps lists for steps and
  # inspections in the first place
  steps = {}
  for item in nodes:
    if item.get("type") == "step":
      steps[item["name"]] = {
        "cmd": item["cmd"],
        "threshold": 1,
        "authorized_functionaries": []
      }
  functionaries = session.get("functionaries", {})

  return render_template("authorizing.html", functionaries=functionaries,
      steps=steps)

@app.route("/chaining")
def chaining():
  """Step 8.
  Dry run snippet and link metadata upload. """
  items = session.get("ssc", {}).get("nodes", [])
  links = session.get("chaining", {})
  return render_template("chaining.html", items=items, link_dict=links)


@app.route("/chaining/upload", methods=["POST"])
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

  session_chaining = session.get("chaining", {})
  session_chaining[link.name] = fn
  session["chaining"] = session_chaining

  flash = {
    "msg": "Successfully uploaded link '{fn}' for step '{name}'!".
      format(fn=fn, name=link.name),
    "type": "alert-success"
  }
  return jsonify({"flash": flash, "error": False})

@app.route("/wrap-up")
def wrap_up():
  """Step 9.
  Explain what to do with generated layout.
   - Download layout
   - Create project owner key (keygen snippet)
   - Sign layout (signing snippet)
   - Per functionary commands (in-toto-run snippet)
   - Release instructions ??
  """
  functionaries = session.get("functionaries", {}).keys()
  auths = session.get("authorizing", {})
  items = session.get("ssc", {}).get("nodes", [])
  return render_template("wrap_up.html", items=items, auths=auths, functionaries=functionaries)

@app.route("/download-layout")
def download_layout():
  """Create layout based on session data and uploaded links and
  serve with layout name from session directory as attachment
  (Content-Disposition: attachment).  """

  # Iterate over items in ssc dictionary and create an ordered list
  # of according link objects
  links = []
  for item in session.get("ssc", {}).get("nodes", []):

    # FIXME: split ssc["nodes"] into steps and inspections
    if item["type"] != "step":
      continue

    link_filename = session.get("chaining", {}).get(item["name"])
    if not link_filename:
      continue

    link_path = os.path.join(app.config["USER_FILES"], link_filename)
    link = in_toto.models.mock_link.MockLink.read_from_file(link_path)
    if link:
      links.append(link)

  layout = reverse_layout.create_layout_from_ordered_links(links)

  functionary_keyids = {}
  # Add uploaded functionary pubkeys to layout
  for functionary_name, pubkey_path in session.get("functionaries",
      {}).iteritems():

    # Load and check the format of the uploaded public keys
    key = in_toto.util.import_rsa_key_from_file(pubkey_path)
    securesystemslib.formats.PUBLIC_KEY_SCHEMA.check_match(key)

    # Add keys to layout's key store
    layout.keys[key["keyid"]] = key

    # Add keys to functionary name-keyid map needed below
    functionary_keyids[functionary_name] = key["keyid"]


  # Add authorized functionaries to steps and set signing threshold
  for idx in range(len(layout.steps)):
    step_name = layout.steps[idx].name
    auth_data = session.get("authorizing", {}).get(step_name, {})

    for functionary_name in auth_data.get("authorized_functionaries", []):
      keyid = functionary_keyids.get(functionary_name)
      if keyid:
        layout.steps[idx].pubkeys.append(keyid)

    layout.steps[idx].threshold = auth_data.get("threshold")

  # TODO: Create inspections
  layout.validate()

  layout_name = "root.layout"
  layout_path = os.path.join(app.config["USER_FILES"], layout_name)
  layout.dump(layout_path)

  # Serve file
  return send_from_directory(app.config["USER_FILES"], layout_name,
      as_attachment=True)

@app.route("/guarantees")
def guarantees():
  """ Show what the software supply chain protects against and give advice for
  more guarantees. """
  return render_template("guarantees.html")

if __name__ == "__main__":
  app.run()
