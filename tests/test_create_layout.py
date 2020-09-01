import unittest
import before_after_filesystem_snapshot

class Test_before_after_filesystem_snapshot(unittest.TestCase):

  '''Check whether the output of before_after_filesystem_snapshot is as defined
    by each test case.'''

  before = {
    'one.tgz': '1234567890abcdef',
    'foo/two.tgz': '0000001111112222',
    'three.txt': '1111222233334444',
    'bar/bat/four.tgz': '6677889900112233'
  }

  def test_same_filesystem_snapshot(self):

    after = {
      'one.tgz': '1234567890abcdef',
      'foo/two.tgz': '0000001111112222',
      'three.txt': '1111222233334444',
      'bar/bat/four.tgz': '6677889900112233'
    }

    snapshot = before_after_filesystem_snapshot.snapshot(self.before, after)
    self.assertEqual(snapshot, (['bar/bat/four.tgz', 'foo/two.tgz', 'one.tgz',
      'three.txt'], [], [], []))


  def test_removed_files_filesystem_snapshot(self):

    after = {}

    snapshot = before_after_filesystem_snapshot.snapshot(self.before, after)
    self.assertEqual(snapshot, ([], [], [], ['bar/bat/four.tgz', 'foo/two.tgz',
      'one.tgz', 'three.txt']))


  def test_new_filesystem_snapshot(self):
    after = {
      'five.tgz': '1234567890defghi',
      'foo/bar/six.tgz': '0000001111112234',
      'foofoo/seven.txt': '1111222233334555'
    }

    snapshot = before_after_filesystem_snapshot.snapshot(self.before, after)
    self.assertEqual(snapshot, ([], [], ['five.tgz', 'foo/bar/six.tgz',
      'foofoo/seven.txt'], ['bar/bat/four.tgz', 'foo/two.tgz', 'one.tgz',
      'three.txt']))


  def test_fully_modified_filesystem_snapshot(self):

    after = {
      'one.tgz': '1234567890aabbcc',
      'foo/two.tgz': '0000001111112233',
      'three.txt': '1111222233334455',
      'bar/bat/four.tgz': '6677889900123456'
    }

    snapshot = before_after_filesystem_snapshot.snapshot(self.before, after)
    self.assertEqual(snapshot, ([], ['bar/bat/four.tgz', 'foo/two.tgz',
      'one.tgz', 'three.txt'], [], []))


  def test_partially_modified_filesystem_snapshot(self):

    after = {
      'five.txt': '5555555555555555',
      'one.tgz': '1234567890abcdef',
      'foo/two.tgz': 'ffffffffffffffff',
      'bar/bat/four.tgz': '6677889900123456',
      'baz/six.tgz': '6666666666666666'
    }

    snapshot = before_after_filesystem_snapshot.snapshot(self.before, after)
    self.assertEqual(snapshot, (['one.tgz'], ['bar/bat/four.tgz',
      'foo/two.tgz'], ['baz/six.tgz', 'five.txt'], ['three.txt']))

  def test_generate_artifact_rules(self):

    after = {
      'five.txt': '5555555555555555',
      'one.tgz': '1234567890abcdef',
      'foo/two.tgz': 'ffffffffffffffff',
      'bar/bat/four.tgz': '6677889900112233',
      'baz/six.tgz': '6666666666666666'
    }

    artifact_rules = {
      'expected_materials': [
        ['ALLOW', 'bar/bat/four.tgz'],
        ['ALLOW', 'one.tgz'],
        ['ALLOW', 'foo/two.tgz'],
        ['DELETE', 'three.txt'],
        ['DISALLOW', '*']
      ],
      'expected_products': [
        ['ALLOW', 'bar/bat/four.tgz'],
        ['ALLOW', 'one.tgz'],
        ['MODIFY', 'foo/two.tgz'],
        ['CREATE', 'baz/six.tgz'],
        ['CREATE', 'five.txt'],
        ['DISALLOW', '*']
      ]
    }

    snapshot = before_after_filesystem_snapshot.snapshot(self.before, after)
    rules = before_after_filesystem_snapshot.generate_artifact_rules(snapshot)
    self.assertDictEqual(artifact_rules, rules)

  if __name__ == '__main__':
    unittest.main()
