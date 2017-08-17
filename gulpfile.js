/*****************************************************************
<File Name>
  gulpfile.js

<Author>
  Lukas Puehringer <lukas.puehringer@nyu.edu>

<Started>
  May 05, 2017

<Copyright>
  See LICENSE for licensing information.

<Purpose>
  Front-end build tool used to copy third-party JS scripts to
  static/vendor from where the app serves them.

  TODO:
  Add gulp task for scss (styles) compilation (on change)
  Currently this is done with a separate command, i.e.
  ```
  sass --watch static/scss/main.scss:static/css/main.scss.css
  ```
  but it would be nice to have all in one place.

<Usage>
  ```
  # Install front-end dependencies (in same directory)
  npm install
  # Run default gulp task
  gulp
  ```

*****************************************************************/
var gulp = require("gulp");

gulp.task("default", function() {
  var js = [
    "node_modules/jquery/dist/jquery.js",
    "node_modules/bootstrap/dist/js/bootstrap.js",
    "node_modules/tether/dist/js/tether.js",
    "node_modules/html5sortable/dist/html.sortable.js",
    "node_modules/d3/d3.js",
    "node_modules/dagre-d3/dist/dagre-d3.js",
    "node_modules/dropzone/dist/dropzone.js",
    "node_modules/select2/dist/js/select2.js"
  ];
  js.forEach(function() {
    gulp.src(js).pipe(gulp.dest("./static/vendor/"));
  });
});