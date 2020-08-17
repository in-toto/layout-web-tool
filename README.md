# in-toto Layout Creation Wizard

A Flask-based web app to guide project owners through creating an
*in-toto layout*.

More information about *in-toto* and *in-toto layouts* can be found at the
project website
[in-toto.io](https://in-toto.io). A beta version of this web app is
deployed at [in-toto.engineering.nyu.edu](https://in-toto.engineering.nyu.edu/) and mockups can be found at
[`editor-and-wizard-wip/mockups`](https://github.com/in-toto/layout-web-tool/blob/editor-and-wizard-wip/mockups/layout-wizard.pdf).


### Installation

**Requirements**
- [Python](https://www.python.org) --
backend
- [npm](https://www.npmjs.com/) -- frontend dependencies
- [Ruby](https://www.ruby-lang.org/en/documentation/installation/) and [SASS](http://sass-lang.com/install) -- CSS preprocessor
- [MongoDB](https://docs.mongodb.com/manual/installation/) -- to persist
user session data (for usage analysis)


```shell
# Start `mongod` (if not already running)
sudo systemctl start mongod

# Install backend (c.f. requirements.txt)
pip install -r requirements.txt

# Install and vendorize frontend dependencies and compile scss
# c.f. dependencies and scripts in package.json
npm install
```

### Deployment
- Add an [instance folder](http://flask.pocoo.org/docs/0.12/config/#instance-folders) with your
deployment configuration, e.g.:
```python
# Example configuration in FLASK_APP_ROOT/instance/config.py
DEBUG = False
SECRET_KEY = '?\xbf,\xb4\x8d\xa3"<\x9c\xb0@\x0f5\xab,w\xee\x8d$0\x13\x8b83' #CHANGE THIS!!!!!

```

- Take a look at `wizard.wsgi` and [these`mod_wsgi` instructions](http://flask.pocoo.org/docs/0.12/deploying/mod_wsgi/)
for further guidance.

### Development Tips
- Run the development server like this:
```shell
python wizard.py
```
- Run a `sass` watcher during development to automatically compile css on file change:
```shell
sass --watch static/scss/main.scss:static/css/main.scss.css
```
- Make extensive use of (e.g. chrome's) browser developer tools, e.g. [map
DevTool files to your local workspace](https://developers.google.com/web/tools/setup/setup-workflow) to live edit `*.scss` and `*.js` files.

## Acknowledgements
This project is managed by Prof. Justin Cappos and other members of the
[Secure Systems Lab](https://ssl.engineering.nyu.edu/) at NYU and the
[NJIT Cybersecurity Research Center](https://centers.njit.edu/cybersecurity).
