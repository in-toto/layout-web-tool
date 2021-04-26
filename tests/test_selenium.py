"""
  Setting up functional testing for layout web tool.
"""

import unittest
import urllib

from flask import Flask
from flask_testing import LiveServerTestCase
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

class TestBase(LiveServerTestCase):

  def create_app(self):
      app = Flask(__name__)
      app.config['TESTING'] = True
      # Default port is 5000
      app.config['LIVESERVER_PORT'] = 8943
      # Default timeout is 5 seconds
      app.config['LIVESERVER_TIMEOUT'] = 10
      return app

  def setUp(self):
    opt = Options()
    opt.add_argument("headless")
    # FIXME: we may want to keep a policy so as to fix seccomp blocking
    # the browser without disabling sandboxing altogether.
    opt.add_argument("no-sandbox")
    self.driver = webdriver.Chrome(options=opt)

  def test_start(self):
    driver = self.driver
    driver.get('https://in-toto.engineering.nyu.edu/')

    start = driver.find_element_by_xpath('/html/body/div[3]/div/div/a')
    start.click()

    self.driver.quit()

if __name__ == '__main__':
    unittest.main()