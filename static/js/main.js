$(function() {
  /*
   * Click listener to toggle option form in the option grid and toggle active
   * class.
   */
  $(".opt-content").on("click", function(evt) {
    var $opt_form_cont = $(this).parent(".opt-cell").find(".opt-form-cont");

    // Hide all others
    $(".opt-form-cont").not($opt_form_cont).slideUp();
    $(".opt-content").not(this).removeClass("active");

    $opt_form_cont.slideToggle();
    $(this).toggleClass("active");
  });

  /*
   * Click listener to clone an html template found by the selector stored in
   * the clicked element's `data-templatesource` attribute and append it to
   * an `data-templatedest`
   * Important: the selectors should each match only one element
   */
  $(".add-btn").on("click", function(evt){
    var template_src_selector = $(this).data("templatesource");
    var template_dest_selector = $(this).data("templatedest");

    $(".template" + template_src_selector)
        .clone()
        .appendTo(template_dest_selector)
        .slideDown(function(){
          $(this).removeClass("template");
        })

    // If the added item was sortable, re-initialize the sort container
    if ($(template_src_selector).parents(".sort-container").length) {
      sortable(".sort-container")
    }
  });

  /*
   * Click listener to hide and remove closest (up the DOM) element matched by
   * the clicked element's `data-toremove` attribute.
   */
  $(document).on("click", "button.rm-btn", function(evt) {
    var element_to_remove_selector = $(this).data("toremove");

    $(this).closest(element_to_remove_selector).slideUp(function(){
      $(this).remove();
    });
  });

  /*
   * Click listener to copy the enclosing opt-form and add it to an element
   * with id #opt-from-container.
   * If the clicked copy button has a value on the "data-submit" attribute
   * that value will be used to query the actual postable form and submit it
   * to the server.
   * If not the user stays the opt-form will be added and if the target
   * opt-form-container is also a sort container the sortable plugin will be
   * re-initialized.
   */
  $(document).on("click", "button.copy-btn", function(evt) {

    // Hide opts
    $(".opt-form-cont").slideUp();
    $(".opt-content").removeClass("active");

    var $opt_form = $(this).parents(".opt-form").clone().hide();

    // TODO: Replace hack that hides "add" buttons and shows "remove" button
    // instead
    $opt_form.find(".rm-btn").removeClass("d-none");
    $opt_form.find(".copy-btn").addClass("d-none");

    // Every opt_form in the opt-grid has two copy buttons
    var form_id = $(this).data("submit");
    if (form_id) {
      $opt_form.appendTo("#opt-form-container");
      $("#" + form_id).submit();

    } else {
      $opt_form.appendTo("#opt-form-container").slideDown();
      show_message("The command has been added to your workflow!" +
          " You can still review and change it below before it gets stored.",
          "alert-info");

      $(".opt-form-container-info").removeClass("d-none");

      // If the added item was sortable, re-initialize the sort container
      if ($opt_form.parents(".sort-container").length) {
        sortable(".sort-container")
      }
    }
  });


  /*
   * Click listener to add a new functionary name with a file upload dropzone
   * to upload a public key
   */
  $(document).on("click", "button.add-func-btn", function(evt){
    var $input = $(".add-func-input");
    var val = $input.val();

    // Two cheap frontend name validations (must be unique and not "")
    if (val == "") {
      show_message("Your functionary needs a name!", "alert-warning");

    } else if ($("#functionary-container input[value='"+ val + "']").length > 0) {
      show_message("You already have a functionary '"+ val + "'!",
          "alert-warning");

    } else {
      // Clone functionary template
      var $func = $(".template.functionary").clone();

      // Copy input functionary name
      // one displayed and one hidden input sent to server on file upload
      $func.find("span.functionary-name").text(val);
      $func.find("input[name='functionary_name']").val(val);

      // Append the functionary dropzone to the appropriate place
      $func.appendTo("#functionary-container")
        .slideDown(function(){
          $(this).removeClass("template");

          // Inits the file upload dropzone
          $func.find(".dropzone").dropzone({
            paramName: "functionary_key",
            maxFiles: 1,
            success: function(file, response) {
              // Remove the file place holder from dropzone if upload failed
              if (response.error) {
                this.removeFile(file);
              }
              show_message(response.flash.msg, response.flash.type);
            }
          });
      });
    }
  })

  /*
   * Click listener to remove a functionary
   * Removes the functionary dropzone and the according key on the server
   * # TODO: Maybe we should allow to just use remove a key (on the server)
   * without removing the functionary?
   */
  $(document).on("click", "button.rm-func-btn", function(evt) {
    $functionary = $(this).closest(".functionary");
    name = $functionary.find("input[name='functionary_name']").val();

    //FIXME: This is a hackish way to find out if there's already a file in
    // that dropzone.
    // We should use
    // $(".dropzone").get(0).dropzone.files
    // but we can't because currently we don't initialize the dropzone
    // if the functionary page is served with already uploaded pubkeys
    var preview = $functionary.find(".dz-file-preview");

    // We only try to delete the key on the server if there is one
    if (preview.length > 0) {
      // Post the name of the functionary to remove
      $.post("/functionaries/remove", {"functionary_name": name},
        function(response) {
          show_message(response.flash.msg, response.flash.type);

          //Only remove on client side if server side removal was successful
          if (!response.error) {
            $functionary.slideUp(function(){
              $(this).remove();
            });
          }
        });
    } else {
      $functionary.slideUp(function(){
        $(this).remove();
      });
    }
  });

  /*
   * Initialize drag and drop sorting
   * Note: Needs to be re-initialized when elements are added
   */
   sortable(".sort-container", {
      forcePlaceholderSize: true,
      placeholderClass: "sort-placeholder",
   });


  /* Turn pre element (code) into textarea on click and select code.
   * Nice for copy paste snippets
   */
  $("pre.code").click(function(){
    // Cache old elements attributes (e.g. class)
    var attrs = {};
    $.each(this.attributes, function(idx, attr) {
        attrs[attr.nodeName] = attr.nodeValue;
    });

    // Add disable spellcheck attribute
    attrs["spellcheck"] = "false";

    // Create new element
    $textarea = $("<textarea />", attrs)
      .height($(this).outerHeight())
      .prop("readonly", true)
      .append($(this).html());

    // Remove old element from DOM and insert new
    $(this).replaceWith($textarea);

    // Select the contents
    $textarea.select();

  });
});


/*
 * Append and show message with a certain type
 * The message gets removed after a fixed amount of time
 */
var show_message = function(msg, msg_type) {

  if ($.inArray(msg_type,
      ["alert-success", "alert-info", "alert-warning", "alert-danger"]) == -1)
    msg_type = "alert-info";

  var $container = $("#alert-container");
  var $alert = $container.find(".alert.template").clone();
  $alert.find("span.alert-msg").text(msg);

  $alert.addClass(msg_type)
      .appendTo($container)
      .removeClass("template");

  // Remove message after a fixed amount of time
  setTimeout(function(){
    $alert.alert("close");
  }, 5000);
}

  /*
   * Draw in-toto layout graph using D3.js
   * FIXME: modularize don't use data from global variable `layout_data`
   * (c.f. software_supply_chain.html)
   */
var draw_graph = function(graph_data) {
  // Create a new directed acyclic graph (dag)
  var dag = new dagreD3.graphlib.Graph({multigraph: true})

  // Create a left to right layout
  dag.setGraph({
    nodesep: 5,
    ranksep: 40,
    edgesep: 10,
    rankdir: "LR",
  });

  // Create nodes (steps and inspections) based on passed nodes data.
  graph_data.nodes.forEach(function(node) {
    // Create regular node (step or inspection)
    dag.setNode(node.name, {label: node.name});
  });

  // Create edges between steps and/or inspections
  graph_data.edges.forEach(function(edge){
    dag.setEdge(edge.source, edge.dest, {
        lineInterpolate: "basis"
        // TODO: we could display the path pattern as label
        // label: "..."
      });
  });


  // The SVG element
  var svg = d3.select("svg.svg-content");

  // An SVG group element that wraps the graph
  var inner = svg.append("g");

  // Set up drag/drop/zoom support
  var zoom = d3.behavior.zoom().on("zoom", function() {
        inner.attr("transform", "translate(" + d3.event.translate + ")" +
                                    "scale(" + d3.event.scale + ")");
      });
  svg.call(zoom);

  // Create the renderer ...
  var render = new dagreD3.render();

  // ... and run it to draw the graph.
  render(inner, dag);

  /* Scale and Center  graph */

  // Cache the SVG's container to access its width and height
  // this is where the svg is visible
  var $outer = $(".svg-container");

  // Get width and height of the graph
  // Note: D3 elements are lists of objects having the DOM element at idx 1
  var inner_rect = inner[0][0].getBoundingClientRect();

  // Padding in pixels
  var padding = 50;

  // Calculate how much we have to scale the graph up or down to fit the
  // container
  var scale = Math.min(($outer.width() - padding) / inner_rect.width,
      ($outer.height() - padding) / inner_rect.height);

  // Calculate distance from top and left to center the graph
  // Note: We have to translate between viewport and user coordinate system
  var top = ($outer.height() - inner_rect.height * scale) / 2;
  var left = ($outer.width() - inner_rect.width * scale) / 2;

  // Do the actual translate and scale
  zoom.translate([left, top]).scale(scale).event(svg);

  d3.selection.prototype.toFront = function() {
     /*
      * D3 selection extension to re-locate an element
      * to be the last child.
      */
    return this.each(function(){
      this.parentNode.appendChild(this);
    });
  };

  // Re-order SVG items - no z-index in SVG :(
  d3.select(".edgePaths").toFront();
}
