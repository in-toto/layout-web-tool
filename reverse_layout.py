# -*- coding: utf-8 -*-
#!/usr/bin/env python

"""
<Program Name>
  reverse_layout.py

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
        default value (e.g. two months)
    keys:
        empty (add manually)
    steps:
        add each step from list of ordered step link files
            name:
                `link.name`
            expected_command:
                `link.command`
            threshold:
                default (e.g. 1)
            material_matchrules and product_matchrules:
                see below
    inspections:
        ??
    signatures:
        []

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
    - explicitly, ALLOW or MATCH files by name instead of "*"
      e.g.:material_matchrules = [["ALLOW", material] for material in links[index].materials.keys()]
    - for MATCH rules
      match only those that already were in the previous step
      allow the rest, by name


"""
import os
import in_toto.models.link
import in_toto.models.layout

def load_ordered_links():
  # TODO: Get an ordered list of links
  # Possible ways
  #  - store the link files with a sortable filename prefix (1,2,3), ..
  #  - store a list in a separate file
  #  - store the steps immedeatly to a layout

  test_link_file_paths = [
      "demo_metadata/clone.0c6c50a1.link",
      "demo_metadata/update-version.0c6c50a1.link",
      "demo_metadata/package.c1ae1e51.link"
  ]

  links = []
  for path in test_link_file_paths:
    links.append(in_toto.models.link.Link.read_from_file(path))

  return links

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



def main():
  links = load_ordered_links()

  layout = in_toto.models.layout.Layout.read({
    "_type": "layout",
    "keys": {},
    "signatures": [],
    "steps" : [
      {
        "name": link.name,
        "threshold": 1,
        "expected_command": (" ".join(link.command)
            if isinstance(link.command, list) else ""),
        "material_matchrules": create_material_matchrules(links, index),
        "product_matchrules": create_product_matchrules(links, index),
        "pubkeys": []
      } for index, link in enumerate(links)
    ],
    "inspect": []
  })

  layout.dump("demo_metadata/demo.layout")


if __name__ == "__main__":
  main()