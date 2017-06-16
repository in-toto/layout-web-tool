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
def transform_for_graph(layout):
  """
  <Purpose>
    Takes an in-toto layout and transforms it to a data structure that's more
    convenient to create a graph from it, e.g. using `dagre-d3` [1]:

    Note:
      We do this on server-side to make use of in-toto functions like
      `artifact_rules.unpack_rule`.
  <Returns>
    Example:
    {
      nodes: {
        "name": <unique step or inspection name">,
        "type": "step" | "inspection"
      }
      links: {
        "source": <unique step or inspection name">,
        "source_type": "M" | "P",
        "dest": <unique step or inspection name">,
        "dest_type": "M" | "P",

      }
    }
  """
  graph_data = {
    "nodes": [],
    "links": []
  }

  def _get_links(src_type, src_name, rules):
    """ Returns links (list) based on passed list of material_matchrules ("M")
    or product_matchrules ("P"). """

    links = []
    for rule in rules:
      # Parse rule list into dictionary
      rule_data = in_toto.artifact_rules.unpack_rule(rule)

      # Only "MATCH" rules are used as links
      if rule_data["type"].upper() == "MATCH":

        # We can pass additional information here if we want
        links.append({
            "source": src_name,
            "source_type": src_type,
            "dest": rule_data["dest_name"],
            "dest_type": rule_data["dest_type"][0].upper() # "M" | "P"
          })

    return links

  # Create nodes from steps and inspections
  for item in layout.steps + layout.inspect:
    graph_data["nodes"].append({
        "name": item.name,
        "type": item._type
      })

    # Create links from material- and product- matchrules
    graph_data["links"] += _get_links("M", item.name, item.material_matchrules)
    graph_data["links"] += _get_links("P", item.name, item.product_matchrules)

  return graph_data


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
    # FIXME: Needs sanatizing and session persistence!!!
    session["vcs"] = {
      "items": [{"cmd": cmd} for cmd in request.form.getlist("vcs_cmd[]")],
      "comment": request.form.get("comment", "")
    }

    flash("Success! Now let's see how you build your software...", "alert-success")
    return redirect(url_for("building"))

  # The template can deal with an empty dict, but a dict it must be
  user_data = session.get("vcs", {})

  return render_template("versioning.html", options=options, user_data=user_data)


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
  graph_data = transform_for_graph(layout)

  return render_template("software_supply_chain.html",
      graph_json=json.dumps(graph_data), layout=layout)


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
