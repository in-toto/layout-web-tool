from unittest import defaultTestLoader, TextTestRunner
import sys

suite = defaultTestLoader.discover(start_dir=".")
result = TextTestRunner(verbosity=2, buffer=True).run(suite)
sys.exit(0 if result.wasSuccessful() else 1)
