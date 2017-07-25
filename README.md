# in-toto Layout Creation Wizard

A Flask based web app to guide project owners through creating an
[in-toto layout](github.com/in-toto/in-toto).

Mockups can be found at [`editor-and-wizard-wip/mockups`](https://github.com/in-toto/layout-web-tool/blob/editor-and-wizard-wip/mockups/layout-wizard.pdf).


### Installation

**Requirements**
- [Python 2.7](https://www.python.org/download/releases/2.7/) --  backend
- [npm](https://www.npmjs.com/) -- frontend dependencies
- [Ruby](https://www.ruby-lang.org/en/documentation/installation/) and [SASS](http://sass-lang.com/install) -- CSS preprocessor
- [MongoDB](https://docs.mongodb.com/manual/installation/) -- to persist
user session data (for usage analysis)


```shell
# Start `mongod` (if not already running)
# This command should work on many Linux systems
sudo service mongod start

# Install backend (c.f. requirements.txt)
pip install -r requirements.txt

# Install frontend dependencies (c.f. package.json)
npm install

# Compile scss to css + source maps
sass static/scss/main.scss:static/css/main.scss.css

# Copy needed node_modules *.js to `static/vendor/` dir (c.f. gulpfile)
gulp
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