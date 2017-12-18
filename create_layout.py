# -*- coding: utf-8 -*-
#!/usr/bin/env python

"""
<Program Name>
  create_layout.py

<Author>
  Lukas Puehringer <lukas.puehringer@nyu.edu>

<Started>
  March 23, 2017

<Copyright>
  See LICENSE for licensing information.

<Purpose>
  Creates a basic in-toto layout by reading an ordered list of step link files.

  ** Infer layout fields: **
    expires:
            default value
    keys:
            FIXME: Keys are currently ignored in this module
    steps:
            add steps in the order of passed link files
            name:
                    link.name
            expected_command:
                    link.command
            threshold:
                    default value
            material_matchrules/product_matchrules:
                    currently uses simple approach (see below)
                    FIXME: Should use more complex approach (see ideas below)
            inspections:
                    FIXME Inspections are currently ignored in this module
            signatures:
                    empty (use `in-toto-sign` command line utility)


  ** Infer step artifact rules (simple approach) **
    ** material_matchrules **

      IF no materials were recorded
        material_matchrules: [["DISALLOW", "*"]]

      ELSE IF materials were recorded and it is the first step
        material_matchrules: [["ALLOW", "*"]]

      ELSE
        material_matchrules: [["MATCH", "*", "WITH", "PRODUCTS", "FROM", <PREVIOUS STEP>]


    ** product_matchrules **

      IF no products were recorded
        product_matchrules: [["DISALLOW", "*"]]

      ELSE products were recorded:
        product_matchrules: [["ALLOW", "*"]]


  ** Ideas for more complexity: **
    - explicitly, ALLOW or MATCH files by name instead of "*", e.g.:
      material_matchrules = \
          [["ALLOW", material] for material in links[index].materials.keys()]

    - for MATCH rules
      match only those that already were in the previous step
      allow the rest by name


  <Usage>

    ```
    # Create a layout given an ordered list of link file paths

    links = []
    for LINK_PATH in LINK_PATHS:
      link = in_toto.models.link.Link.read_from_file(LINK_PATH)
      links.append(link)

    layout = create_layout_from_ordered_links(links)
    layout.dump()

    ```

"""
import os
import in_toto.models.link
import in_toto.models.layout
import in_toto.models.metdata

def create_material_matchrules(links, index):
  """Create generic material rules (3 variants)

  * No materials recorded -> disallow any artifact
  * Materials recorded (first step) -> allow artifacts that existed beforehand
  * Materials recorded (latter step) -> match from previous products

  Returns a list of material rules
  NOTE: Read header docstring for ideas for more complexity.  """

  material_matchrules = []

  if not links[index].materials:
    material_matchrules = [["DISALLOW", "*"]]

  elif index == 0 and links[index].materials:
    material_matchrules = [["ALLOW", "*"]]

  else:
    material_matchrules = [
        ["MATCH", "*", "WITH", "PRODUCTS", "FROM", links[index - 1].name]]

  return material_matchrules


def create_product_matchrules(links, index):
  """Create generic material rules (2 variants)

  * No products recorded -> disallow any artifact
  * Products recorded  -> allow all artifacts

  Returns a list of product rules
  NOTE: Read header docstring for ideas for more complexity.  """

  if not links[index].products:
    product_matchrules = [["DISALLOW", "*"]]

  else:
    product_matchrules = [["ALLOW", "*"]]

  return product_matchrules


def create_layout_from_ordered_links(links):
  """Creates basic in-toto layout from an ordered list of in-toto link objects,
  inferring material and product rules from the materials and products of the
  passed links. """
  # Create an empty layout
  layout = in_toto.models.layout.Layout()
  layout.keys = {}

  for index, link in enumerate(links):
    step_name = link.name
    step = in_toto.models.layout.Step(name=step_name,
      material_matchrules=create_material_matchrules(links, index),
      product_matchrules=create_product_matchrules(links, index),
      expected_command=link.command)

    layout.steps.append(step)

  layout_metadata = in_toto.models.metadata.Metablock(signed=layout)

  return layout_metadata
