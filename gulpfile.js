var gulp = require("gulp");

gulp.task("default", function() {
  var js = [
    "node_modules/jquery/dist/jquery.js",
    "node_modules/bootstrap/dist/js/bootstrap.js",
    "node_modules/tether/dist/js/tether.js",
    "node_modules/html5sortable/dist/html.sortable.js"
  ];

  js.forEach(function() {
    gulp.src(js).pipe(gulp.dest("./static/vendor/"));
  });

});