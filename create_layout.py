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
            expected_materials/expected_products:
                    currently uses simple approach (see below)
                    FIXME: Should use more complex approach (see ideas below)
            inspections:
                    FIXME Inspections are currently ignored in this module
            signatures:
                    empty (use `in-toto-sign` command line utility)


  ** Infer step artifact rules (simple approach) **
    ** expected_materials **

      IF no materials were recorded
        expected_materials: [["DISALLOW", "*"]]

      ELSE IF materials were recorded and it is the first step
        expected_materials: [["ALLOW", "*"]]

      ELSE
        expected_materials: [["MATCH", "*", "WITH", "PRODUCTS", "FROM", <PREVIOUS STEP>]


    ** expected_products **

      IF no products were recorded
        expected_products: [["DISALLOW", "*"]]

      ELSE products were recorded:
        expected_products: [["ALLOW", "*"]]


  ** Ideas for more complexity: **
    - explicitly, ALLOW or MATCH files by name instead of "*", e.g.:
      expected_materials = \
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

def create_material_rules(links, index):
  """Create generic material rules (3 variants)

  * MATCH available materials with products from previous step (links must be an
  ordered list) and
  * ALLOW available materials if it is the first step in the
  list
  Returns a list of material rules
  NOTE: Read header docstring for ideas for more complexity.  """

  expected_materials = []

  if index == 0:
    for material_name in links[index].materials.keys():
      expected_materials.append(["ALLOW", material_name])
    expected_materials.append(["DISALLOW", "*"])

  else:
    expected_materials = [
        ["MATCH", "*", "WITH", "PRODUCTS", "FROM", links[index - 1].name]]

  return expected_materials


def create_product_rules(links, index):
  """Create generic product rules (2 variants)

  * ALLOW available products
  * DISALLOW everything else

  Returns a list of product rules
  NOTE: Read header docstring for ideas for more complexity.  """


  expected_products = []

  for product_name in links[index].materials.keys():
    expected_products.append(["ALLOW", product_name])

  expected_products.append(["DISALLOW", "*"])

  return expected_products


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
      expected_materials=create_material_rules(links, index),
      expected_products=create_product_rules(links, index),
      expected_command=link.command)

    layout.steps.append(step)


  return layout
