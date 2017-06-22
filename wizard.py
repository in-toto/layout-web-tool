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
    flash, send_from_directory, abort, json, jsonify)

from in_toto.models.layout import Layout
from in_toto.models.link import FILENAME_FORMAT_SHORT
import in_toto.artifact_rules
import tooldb

app = Flask(__name__, static_url_path="", instance_relative_config=True)

app.config.update(dict(
    DEBUG=True,
    SECRET_KEY="do not use the development key in production!!!"
))

# Supply a config file at "instance/config.py" that carries
# e.g. your deployment secret key
app.config.from_pyfile("config.py")


# FIXME: For prototyping, we statically serve an example  layout on some pages
layout = Layout.read_from_file(
    "demo_metadata/root.layout") # WARNING: layout file not in VCS

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
#     Example:
#     {
#       "nodes": [{
#         "name": <unique step or inspection name">,
#         "type": "step" | "inspection"
#       }, ...]
#       "links": [{
#         "source": <unique step or inspection name">,
#         "source_type": "M" | "P",
#         "dest": <unique step or inspection name">,
#         "dest_type": "M" | "P",
#       }, ...]
#     }
#   """
#   graph_data = {
#     "nodes": [],
#     "links": []
#   }

#   def _get_links(src_type, src_name, rules):
#     """ Returns links (list) based on passed list of material_matchrules ("M")
#     or product_matchrules ("P"). """

#     links = []
#     for rule in rules:
#       # Parse rule list into dictionary
#       rule_data = in_toto.artifact_rules.unpack_rule(rule)

#       # Only "MATCH" rules are used as links
#       if rule_data["type"].upper() == "MATCH":

#         # We can pass additional information here if we want
#         links.append({
#             "source": src_name,
#             "source_type": src_type,
#             "dest": rule_data["dest_name"],
#             "dest_type": rule_data["dest_type"][0].upper() # "M" | "P"
#           })

#     return links

#   # Create nodes from steps and inspections
#   for item in layout.steps + layout.inspect:
#     graph_data["nodes"].append({
#         "name": item.name,
#         "type": item._type
#       })

#     # Create links from material- and product- matchrules
#     graph_data["links"] += _get_links("M", item.name, item.material_matchrules)
#     graph_data["links"] += _get_links("P", item.name, item.product_matchrules)

#   return graph_data


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
    when_list = request.form.getlist("when[]")
    build_cmd_list = request.form.getlist("build_cmd[]")
    retval_operator_list = request.form.getlist("retval_operator[]")
    retval_value_list = request.form.getlist("retval_value[]")
    stdout_operator_list = request.form.getlist("stdout_operator[]")
    stdout_value_list = request.form.getlist("stdout_value[]")
    stderr_operator_list = request.form.getlist("stderr_operator[]")
    stderr_value_list = request.form.getlist("stderr_value[]")

    # Values of a step are related by the same index
    # All lists should be equally long
    # FIXME: Don't assert, try!
    assert(len(cmd_list) == len(when_list) == len(build_cmd_list) ==
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
          "when": when_list[i],
          "build_cmd": build_cmd_list[i],
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

  # Building commands as set by user in prior template
  # Note how we deal with non existing and empty building data.
  build_steps = session.get("building", {}).get("items", [])

  return render_template("quality.html", options=options, user_data=user_data,
      build_steps=build_steps)

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


@app.route("/software-supply-chain")
def software_supply_chain():
  """Step 5.
  Create preliminary software supply chain based on form posted steps.

  """
  # `transform_for_graph` is used in conjunctions with a layout
  # But actually we take form posted data to create the supply_chain graph.
  # FIXME: comment out for now (decide later what to do with it
  # graph_data = layout_to_graph(layout)

  step_nodes = []
  step_links = []
  inspect_nodes = []
  inspect_links = []

  # Create links based on data posted from previous pages
  # FIXME: Come up with better naming (low priority)
  # TODO: Do we want to re-order QA steps based on the form posted info from
  # QA page (`I run this inspection (before | after) <build step>`)??
  # IMHO a user can re-order the steps here anyway, right?
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
          link = FILENAME_FORMAT_SHORT.format(step_name=step_name)
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

          #FIXME: We kinda ignore the information
          # `I run this inspection (before | after) <build step>`
          inspect_links.append({
            "source": step_name,
            "dest": inspect_name
          })

  # For now we assume that steps are executed sequentially
  # And that's how we link the steps
  for idx in range(len(step_nodes)):
    if idx > 0:
      step_links.append({
          "source": step_nodes[idx-1]["name"],
          "dest": step_nodes[idx]["name"]
        })

  supply_chain = {
    "nodes": step_nodes + inspect_nodes,
    "links": step_links + inspect_links
  }

  return render_template("software_supply_chain.html",
      ssc_graph_data=supply_chain)


@app.route("/authorizing")
def authorizing():
  """Step 6.
  Functionary keys upload and keys dropzone. """
  return render_template("authorizing.html", layout=layout)


@app.route("/authorizing/upload", methods=["POST"])
def ajax_upload_key():
  """Ajax upload functionary keys. """
  return jsonify({})


@app.route("/chaining")
def chaining():
  """Step 7.
  Dry run snippet and link metadata upload. """
  return render_template("chaining.html")


@app.route("/chaining/upload", methods=["POST"])
def ajax_upload_link():
  """Ajax upload link metadata. """
  return jsonify({})


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
  return render_template("wrap_up.html", layout=layout)


@app.route("/guarantees")
def guarantees():
  """ Show what the software supply chain protects against and give advice for
  more guarantees. """
  return render_template("guarantees.html")

if __name__ == "__main__":
  app.run()
