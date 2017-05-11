var gulp = require("gulp");

gulp.task("default", function() {
  var js = [
    "node_modules/jquery/dist/jquery.js",
    "node_modules/bootstrap/dist/js/bootstrap.js",
    "node_modules/tether/dist/js/tether.js",
    "node_modules/html5sortable/dist/html.sortable.js",
    "node_modules/d3/d3.js",
    "node_modules/dagre-d3/dist/dagre-d3.js"

  ];

  js.forEach(function() {
    gulp.src(js).pipe(gulp.dest("./static/vendor/"));
  });

});