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
import warnings
import in_toto.models.link
import in_toto.models.layout

def changes_between_snapshots(before_dict, after_dict):
  """Given two 'snapshots' of an artifacts structure -- 'before' and 'after' --
  return a tuple specifying which artifacts have been added, which have been
  removed, which have been modified, and which have remained unchanged. Both
  these dictionaries have artifact names as the keys and their hashes as the
  values."""

  before_set = set(before_dict.keys())
  after_set = set(after_dict.keys())

  removed_artifacts = before_set.difference(after_set)
  added_artifacts = after_set.difference(before_set)

  unchanged_artifacts = set()
  modified_artifacts = set()
  for key in before_set.intersection(after_set):
    if before_dict[key] == after_dict[key]:
      unchanged_artifacts.add(key)
    else:
      modified_artifacts.add(key)

  return (unchanged_artifacts, modified_artifacts, added_artifacts,
      removed_artifacts)

def create_material_rules(previous_link, current_link):
  """Create generic material rules

  - MATCH available materials with products from previous step (links must be
      an ordered list) and
  - ALLOW available materials if it is the first step in the list
  - DELETE removed materials

  Args:
    previous_link: a link of previous step, including previous step's materials
        and products
    current link: a link of current step, including current step's materials
        and products

  Returns:
    a list of material rules
  """

  expected_materials_rules = []
  unchanged_artifacts, modified_artifacts, _, deleted_artifacts = \
      changes_between_snapshots(current_link.materials, current_link.products)
  previous_link_products = previous_link.products if previous_link else []

  # If there was a previous step, add MATCH rules for all materials that were
  # products in the previous step
  for artifact in sorted(set(current_link.materials).intersection(
      previous_link_products)):
    expected_materials_rules.append(
        ["MATCH", artifact, "WITH", "PRODUCTS", "FROM", previous_link.name])

  # Add DELETE rules for all deleted artifacts
  for artifact in sorted(deleted_artifacts):
    expected_materials_rules.append(["DELETE", artifact])
  # Warn for any delete rule that has no effect because of a previous match
  # rule
  if deleted_artifacts.intersection(previous_link_products):
    warnings.warn("DELETE rule is moot because of the previous MATCH rule."
        " Only the first rule for a given artifact has an effect")

  # Add ALLOW rules for all remaining materials
  for artifact in sorted(set(current_link.materials).difference(
      previous_link_products).difference(deleted_artifacts)):
    expected_materials_rules.append(["ALLOW", artifact])

  # Add DISALLOW rules for all other artifacts
  expected_materials_rules.append(["DISALLOW", "*"])

  return expected_materials_rules


def create_product_rules(current_link):
  """Create generic product rules

  - ALLOW available products
  - MODIFY changed products
  - CREATE added products
  - DISALLOW everything else

  Args:
    current_link: a link of current step, including current step's materials
        and products

  Returns:
    a list of product rules
  """

  expected_products_rules = []
  # Deleted artifacts won't show up in the product queue
  unchanged_artifacts, modified_artifacts, added_artifacts, _ = \
      changes_between_snapshots(current_link.materials, current_link.products)

  for artifact in sorted(unchanged_artifacts):
    # ALLOW unchanged artifacts
    expected_products_rules.append(["ALLOW", artifact])
  for artifact in sorted(modified_artifacts):
    # MODIFY modified artifacts
    expected_products_rules.append(["MODIFY", artifact])
  for artifact in sorted(added_artifacts):
    # CREATE added artifacts
    expected_products_rules.append(["CREATE", artifact])
  # DISALLOW everything else
  expected_products_rules.append(["DISALLOW", "*"])

  return expected_products_rules


def create_layout_from_ordered_links(links):
  """Creates basic in-toto layout from an ordered list of in-toto link objects,
  inferring material and product rules from the materials and products of the
  passed links. """
  # Create an empty layout
  layout = in_toto.models.layout.Layout()
  layout.keys = {}

  for index, link in enumerate(links):
    step_name = link.name
    previous_link = None if index == 0 else links[index-1]
    current_link = link
    step = in_toto.models.layout.Step(name=step_name,
      expected_materials=create_material_rules(previous_link, current_link),
      expected_products=create_product_rules(current_link),
      expected_command=link.command)

    layout.steps.append(step)

  return layout
