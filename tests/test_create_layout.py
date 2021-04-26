import unittest
import create_layout
import in_toto.models.link

class Test_CreateLayout(unittest.TestCase):

  '''Check whether the output of create_layout is as defined
    by each test case.'''

  before = {
    'one.tgz': '1234567890abcdef',
    'foo/two.tgz': '0000001111112222',
    'three.txt': '1111222233334444',
    'bar/bat/four.tgz': '6677889900112233'
  }

  first_step_link_str = {
    '_type': 'link',
    'name': 'first_step',
    'byproducts': {},
    'environment': {},
    'materials': {},
    'command': [],
    'products': {
      'one.tgz': {'sha256': '1234567890abcdef'},
      'foo/two.tgz': {'sha256': '0000001111112222'},
      'three.txt': {'sha256': '1111222233334444'},
      'bar/bat/four.tgz': {'sha256': '6677889900112233'}
    }
  }

  second_step_link_str = {
    '_type': 'link',
    'name': 'second_step',
    'byproducts': {},
    'environment': {},
    'materials': {
      'one.tgz': {'sha256': '1234567890abcdef'},
      'foo/two.tgz': {'sha256': '0000001111112222'},
      'three.txt': {'sha256': '1111222233334444'},
      'bar/bat/four.tgz': {'sha256': '6677889900112233'}
    },
    'command': [],
    'products': {
      'five.txt': {'sha256': '5555555555555555'},
      'one.tgz': {'sha256': '1234567890abcdef'},
      'foo/two.tgz': {'sha256': 'ffffffffffffffff'},
      'bar/bat/four.tgz': {'sha256': '6677889900112233'},
      'baz/six.tgz': {'sha256': '6666666666666666'}
    }
  }

  empty_set = set()

  def test_same_filesystem_snapshot(self):

    after = {
      'one.tgz': '1234567890abcdef',
      'foo/two.tgz': '0000001111112222',
      'three.txt': '1111222233334444',
      'bar/bat/four.tgz': '6677889900112233'
    }

    unchanged, modified, added, deleted = \
        create_layout.changes_between_snapshots(self.before, after)

    self.assertEqual(unchanged,
        {'one.tgz', 'foo/two.tgz', 'three.txt', 'bar/bat/four.tgz'})
    self.assertSetEqual(modified, self.empty_set)
    self.assertSetEqual(added, self.empty_set)
    self.assertSetEqual(deleted, self.empty_set)


  def test_removed_files_filesystem_snapshot(self):

    after = {}

    unchanged, modified, added, deleted = \
        create_layout.changes_between_snapshots(self.before, after)

    self.assertSetEqual(unchanged, self.empty_set)
    self.assertSetEqual(modified, self.empty_set)
    self.assertSetEqual(added, self.empty_set)
    self.assertSetEqual(deleted,
        {'bar/bat/four.tgz', 'foo/two.tgz', 'one.tgz', 'three.txt'})


  def test_new_filesystem_snapshot(self):
    after = {
      'five.tgz': '1234567890defghi',
      'foo/bar/six.tgz': '0000001111112234',
      'foofoo/seven.txt': '1111222233334555'
    }

    unchanged, modified, added, deleted = \
        create_layout.changes_between_snapshots(self.before, after)

    self.assertSetEqual(unchanged, self.empty_set)
    self.assertSetEqual(modified, self.empty_set)
    self.assertSetEqual(added,
        {'five.tgz', 'foo/bar/six.tgz', 'foofoo/seven.txt'})
    self.assertSetEqual(deleted,
        {'bar/bat/four.tgz', 'foo/two.tgz', 'one.tgz', 'three.txt'})


  def test_fully_modified_filesystem_snapshot(self):

    after = {
      'one.tgz': '1234567890aabbcc',
      'foo/two.tgz': '0000001111112233',
      'three.txt': '1111222233334455',
      'bar/bat/four.tgz': '6677889900123456'
    }

    unchanged, modified, added, deleted = \
        create_layout.changes_between_snapshots(self.before, after)

    self.assertSetEqual(unchanged, self.empty_set)
    self.assertSetEqual(modified,
        {'bar/bat/four.tgz', 'foo/two.tgz', 'one.tgz', 'three.txt'})
    self.assertSetEqual(added, self.empty_set)
    self.assertSetEqual(deleted, self.empty_set)


  def test_partially_modified_filesystem_snapshot(self):

    after = {
      'five.txt': '5555555555555555',
      'one.tgz': '1234567890abcdef',
      'foo/two.tgz': 'ffffffffffffffff',
      'bar/bat/four.tgz': '6677889900123456',
      'baz/six.tgz': '6666666666666666'
    }

    unchanged, modified, added, deleted = \
        create_layout.changes_between_snapshots(self.before, after)

    self.assertSetEqual(unchanged, {'one.tgz'})
    self.assertSetEqual(modified, {'bar/bat/four.tgz', 'foo/two.tgz'})
    self.assertSetEqual(added, {'baz/six.tgz', 'five.txt'})
    self.assertSetEqual(deleted, {'three.txt'})


  def test_create_material_rules_of_initial_step(self):
    # Zero index means that the current step is the initial step,
    # so we need to ALLOW all the existing files instead of matching.
    second_link = in_toto.models.link.Link.read(self.second_step_link_str)
    links = [second_link]

    expected_materials = [
      ['DELETE', 'three.txt'],
      ['ALLOW', 'bar/bat/four.tgz'],
      ['ALLOW', 'foo/two.tgz'],
      ['ALLOW', 'one.tgz'],
      ['DISALLOW', '*']
    ]

    self.assertEqual(expected_materials,
        create_layout.create_material_rules(None, second_link))

  def test_create_material_rules_of_not_initial_step(self):
    # Nonzero index means that the current step is not the initial step,
    # so we need to MATCH materials with products of the previous step.
    first_link = in_toto.models.link.Link.read(self.first_step_link_str)
    second_link = in_toto.models.link.Link.read(self.second_step_link_str)
    links = [first_link, second_link]

    # WARNING: if we have a MATCH rule and a DELETE rule on the same artifact,
    # the first MATCH rule will moot the subsequent DELETE rule.
    expected_materials = [
      ['MATCH', 'bar/bat/four.tgz', 'WITH', 'PRODUCTS', 'FROM', 'first_step'],
      ['MATCH', 'foo/two.tgz', 'WITH', 'PRODUCTS', 'FROM', 'first_step'],
      ['MATCH', 'one.tgz', 'WITH', 'PRODUCTS', 'FROM', 'first_step'],
      ['MATCH', 'three.txt', 'WITH', 'PRODUCTS', 'FROM', 'first_step'],
      ['DELETE', 'three.txt'],
      ['DISALLOW', '*']
    ]

    self.assertEqual(expected_materials,
        create_layout.create_material_rules(first_link, second_link))

  def test_create_product_rules(self):
    # Given the changes of second step's materials and product,
    # generate the product rules.
    second_link = in_toto.models.link.Link.read(self.second_step_link_str)
    expected_products = [
      ['ALLOW', 'bar/bat/four.tgz'],
      ['ALLOW', 'one.tgz'],
      ['MODIFY', 'foo/two.tgz'],
      ['CREATE', 'baz/six.tgz'],
      ['CREATE', 'five.txt'],
      ['DISALLOW', '*']
    ]

    self.assertTrue(expected_products,
        create_layout.create_product_rules(second_link))

  # TODO: missing test for create_layout_from_ordered_links

  if __name__ == '__main__':
    unittest.main()
