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
    // TODO: We should trigger a custom "add" event on the container
     // and listen on it. if is also sort-container and then re-initialize
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
      $(document).trigger("custom.removed", element_to_remove_selector);
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
      // TODO: We should trigger a custom "add" event on the container
      // and listen on it. if is also sort-container and then re-initialize
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

          // Initialize new pubkey fileupload dropzone
          init_functionary_dropzone($func.find(".dropzone"));
      });
    }
  })

  /*
   * Click listener to remove a functionary
   * Removes the functionary dropzone and the according key on the server
   * Functionaries only make sense together with a key, hence we don't
   * allow to remove a public key alone (keys can be replaced though).
   */
  $(document).on("click", "button.rm-func-btn", function(evt) {
    $functionary = $(this).closest(".functionary");
    $dropzone = $functionary.find(".dropzone");
    var name = $functionary.find("input[name='functionary_name']").val();

    // We only post if the dropzone has a file
    if ($dropzone.get(0).dropzone.files.length > 0) {
      // Post the name of the functionary to remove
      $.post("/functionaries/remove", {"functionary_name": name},
        function(response) {
          show_messages(response.messages);

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
   * Re-generate/re-draw the the graph when step name inputs loose focus
   * Re-generate/re-draw the graph when and ssc step is removed
   * Re-generate/re-draw the graph when ssc steps get sorted
   */
  $(document).on("blur", ".ssc-steps .ssc-step input[name='step_name[]']",
    function(evt){
      draw_graph(generate_graph_from_ssc_steps());
  });
  $(document).on("custom.removed",
    function(evt, removed_elem_class){
      if (removed_elem_class == ".ssc-step")
        draw_graph(generate_graph_from_ssc_steps());
  });
  $(".sort-container.ssc-steps").on("sortupdate",
    function(evt) {
      draw_graph(generate_graph_from_ssc_steps());
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
function show_message(msg, msg_type) {
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
 * Call show_message for a list of message tuples, i.e.:
 * [["<type>", <msg>"}]
 */
function show_messages(messages) {
  messages.forEach(function(message) {
    show_message(message[1], message[0]);
  });
}


/*
 * Initializes a functionary public key file upload dropzone on a
 * passed Jquery element and returns the Dropzone object.
 */
function init_functionary_dropzone($elem) {

  var opts = {
    paramName: "functionary_key",
    parallelUploads: 1,
    init: function(file) {
      var prevFile;

      // Event triggered when a file was uploaded and the server
      // resplies with 200
      this.on("success", function(file, response) {
        show_messages(response.messages);

        // If the new file could not be stored on the server we remove it
        // from the client dropzone
        if (response.error) {
          this.removeFile(file);


        } else {
          // If the new file was successfully stored on the server we
          // remove any previously existing file...
          if (typeof prevFile !== "undefined") {
            this.removeFile(prevFile);
          }
          // ... and store the new file as previously existing file
          // for future replacements
          prevFile = file;
        }
      });

      // We trigger this event (with a second parameter) when adding files
      // that are already stored on the server to the dropzone
      // c.f. JS in functionaries.html
      this.on("complete", function(file, existing) {
        // This makes existing files also replaceable by new files
        if (existing) {
          prevFile = file;
        }
      });
    }
  };
  return new Dropzone($elem.get(0), opts);
}


/*
 * Initializes a link file upload dropzone on a passed Jquery element and
 * returns the Dropzone object.
 */
function init_link_dropzone($elem) {
  var opts = {
    paramName: "step_link",
    addRemoveLinks: true,
    parallelUploads: 1,
    dictRemoveFile: "Remove Link",
    init: function(file) {
      this.on("success", function(file, response) {

        // Remove automatically added file preview...
        // NOTE: We mention this fact by setting a
        // custom property in the file object to not go and remove that file
        // on the server when below call triggers the "removedfile" event.
        // This feels a little hackish
        file.removed_on_error = true;
        this.removeFile(file);

        // ... and add previews only for the file(s) that were actually stored
        // on the server, e.g.: members of an uploaded tar
        for (var i = 0; i < response.files.length; i++) {
          // TODO: DRY add mock file
          uploaded_file = {name: response.files[i], size: 12345};
          this.emit("addedfile", uploaded_file);
          this.emit("complete", uploaded_file, true);
          this.files.push(uploaded_file);
        }
        show_messages(response.messages);
      });

      this.on("removedfile", function(file) {
        if (file.removed_on_error)
          return;

        var thiz = this;
        // Post the name of the functionary to remove
        $.post("/chaining/remove", {"link_filename": file.name},
          function(response) {
            show_messages(response.messages);

            // Re-add file (on clientside) if server-side remove
            // was not successfull
            if (response.error) {
              thiz.emit("addedfile", file);
              thiz.emit("complete", file, true);
              thiz.files.push(file);
            }
          });
      });
    }
  };
  return new Dropzone($elem.get(0), opts);
}

/*
 * Traverse `.ssc_steps` (c.f. softare_supply_chain.html)
 * and generate graph data suitable for `draw_graph`.
 *
 * Directed edges are created sequentially: E {node_i, node_i+1}
 * Only modifying nodes have outdegree
 * A modifying node remains edge source for all subsequent nodes,
 * until the next modifying node in the list.
 *
 * TODO:
 *  - Display inspections
 *
 *
 * Returns
{
  nodes: [
    {
      name: <step name>
    }
  ]
  edges: [
    {
      source: <step name> ,
      dest: <step name>
    }, ...
  ]
}
 */
function generate_graph_from_ssc_steps() {
  // Make a list of node objects (i.e.: [{name: <step_name>}] from
  // step name input fields Ignore steps without name
  var nodes = $.map($(".ssc-steps .ssc-step"),
    function(elem) {
      var step_name = $(elem).find("input[name='step_name[]']").val();
      var step_modifies = ($(elem).find("input[name='step_modifies[]']").val()
          === "true");
      if (step_name) {
        return {
          name: step_name,
          modifies: step_modifies
        };
      }
      return;
    });

  var edges = [];
  var src_i = null;
  for (var i = 0; i < nodes.length - 1; i++) {
    // Only modifying steps, i.e. steps have products, have an outdegree
    // Skip non-modifying steps for edge sources
    if (nodes[i].modifies) {
       src_i = i;
    }
    if (src_i !== null) {
      edges.push({
        source: nodes[src_i].name,
        dest: nodes[i+1].name
      })
    }
  }

  return {
    nodes: nodes,
    edges: edges
  };

}

/*
 * Draw in-toto layout graph using D3.js
 */
function draw_graph(graph_data) {
  // The SVG element
  var svg = d3.select("svg.svg-content");

  // Remove existing content (could be re-draw)
  svg.selectAll("*").remove();

  // Abort drawing if no nodes were passed
  if (graph_data.nodes.length < 1)
    return;

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
