# in-toto Layout Creation Wizard

A Flask based web app to guide project owners to through the generation of an in-toto layout.

Mockups can be found at [`editor-and-wizard-wip/mockups`](https://github.com/in-toto/layout-web-tool/blob/editor-and-wizard-wip/mockups/layout-wizard.pdf).


### Installation

**Requirements**
- [Python 2.7](https://www.python.org/download/releases/2.7/) --  backend
- [npm](https://www.npmjs.com/) -- frontend dependencies
- [Ruby](https://www.ruby-lang.org/en/documentation/installation/) and [SASS](http://sass-lang.com/install) -- CSS preprocessor


```shell
# Install backend (c.f. requirements.txt)
pip install -r requirements.txt

# Install frontend dependencies (c.f. package.json)
npm install

# Compile scss to css + source maps
sass static/scss/main.scss:static/css/main.scss.css

# Copy needed node_modules *.js to `static/vendor/` dir (c.f. gulpfile)
gulp
```

### Development tips
- Run a `sass` watcher during development to automatically compile css on file change:
```shell
sass --watch static/scss/main.scss:static/css/main.scss.css
```
- Make extensive use of (e.g. chrome's) browser developer tools. E.g. [map DevTool files to your local workspace](https://developers.google.com/web/tools/setup/setup-workflow) to live edit `*.scss` and `*.js` files.