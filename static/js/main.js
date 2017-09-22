/*****************************************************************
<File Name>
  main.js

<Author>
  Lukas Puehringer <lukas.puehringer@nyu.edu>

<Started>
  May 05, 2017

<Copyright>
  See LICENSE for licensing information.

<Purpose>
  Contains all non-third-party JavaScript for this app, except for some
  small specific scripts that are directly embedded in the html.

  Registers UI event listeners for onload, i.e. inside the curly braces of
  `$(function(){})`

  Also defines functions to:
   - create CSRF token header
   - show user feedback
   - handle file uploads and removals (dropzone)
   - create graph data from DOM
   - draw graph using D3

  FIXME:
    Move out functionality to different scripts and only load on pages where
    needed, e.g. not every listener needs to be registered on every page.

*****************************************************************/



/*****************************************************************
 * Below function gets executed when the DOM is fully loaded
 ****************************************************************/
$(function() {

  /*
   * Register click listener to toggle an option cell's checkbox input element
   * and a "checked" class used for styling.
   */
  $(".opt-cell").on("click", function(evt) {
    $(this).toggleClass("checked");
    $checkbox = $(this).find("input[type='checkbox']")
    $checkbox.prop("checked", !$checkbox.prop("checked"));

  });

  /*
   * Register click listener to clone an html element (template source) and
   * append it to another html element (template dest).
   *
   * Clicked element must store unique selectors in `data-templatesource`
   * and `data-templatedest`, e.g.:
   *
   * <button type="button"
   *         data-templatesource=".ssc-step"
   *         data-templatedest=".ssc-steps">Add Step</button>
   */
  $(".add-btn").on("click", function(evt){
    // Get the source and dest selectors
    var template_src_selector = $(this).data("templatesource");
    var template_dest_selector = $(this).data("templatedest");

    // Clone template (hidden on the page),
    // append, show (animate) element and remove template class
    $(".template" + template_src_selector)
        .clone()
        .appendTo(template_dest_selector)
        .slideDown(function(){
          $(this).removeClass("template");
        })

    // If the added item was sortable, re-init the enclosing sort container
    // TODO: Maybe we should trigger a custom "add" event on the container
    // and register a separate listener to re-init the sort-container in case
    if ($(template_src_selector).parents(".sort-container").length) {
      sortable(".sort-container")
    }
  });

  /*
   * Register click listener to hide (animate) and remove first element
   * matched by given selector when going up the DOM.
   *
   * Clicked element must store selector in `data-toremove`, e.g.:
   *
   * <button type="button"
   *         data-toremove=".opt-form">Remove</button>
   */
  $(document).on("click", "button.rm-btn", function(evt) {
    // Get the selector
    var element_to_remove_selector = $(this).data("toremove");

    // Hide (animate) and remove first element matched by selector when
    // going up the DOM from clicked element
    // Also trigger custom event ("custom.removed") listened for by other event
    // listener below
    $(this).closest(element_to_remove_selector).slideUp(function(){
      $(this).remove();
      $(document).trigger("custom.removed", element_to_remove_selector);
    });
  });

  /*
   * Register click listener to copy enclosing `.opt-form` and add it to
   * `#opt-form-container`
   *
   * Only `.opt-form`s inside `#opt-form-container` will be posted to the
   * server. Like this the user can review and modify all the options selected
   * and extracted (copied) from the option grid before posting them.
   *
   * Alternatively, a user can immediately post a selected option `.opt-form`.
   * This happens if the clicked button `.copy-btn` has a value on the
   * `data-submit` attribute.
   * That value will be used to query the actual `form` element and submit it
   * to the server right away.
   *
   * If `#opt-form-container` is a sort container, the sortable plugin is
   * re-inited.
   */
  $(document).on("click", "button.copy-btn", function(evt) {
    // Slide up all option forms
    $(".opt-form-cont").slideUp();
    $(".opt-content").removeClass("active");

    // Clone opt form to be copied and hide the clone so that it can be displayed
    // with animation below
    var $opt_form_orig = $(this).parents(".opt-form");
    var $opt_form = $opt_form_orig.clone().hide();

    // JQuery's clone does not clone user selections made to `select` elements
    // https://bugs.jquery.com/ticket/1294
    // https://api.jquery.com/clone/
    // Iterate over select element in the clone base (if any)...
    $opt_form_orig.find("select").each(function(idx){
      // ...and assign each selected value to the respective
      // cloned select element (matched by index)
      $opt_form.find("select").eq(idx).val($(this).val());
    });

    // `.opt-form`s in the option grid can be copied but not removed
    // `.opt-form`s in the `#opt-form-container` can be removed but not copied
    // Here we toggle the display of the respective remove and copy buttons
    // in the `.opt-form` that gets copied from the option grid to the option
    // form container
    // TODO: This is a very hackish DRY effort, we can do better
    $opt_form.find(".rm-btn").removeClass("d-none");
    $opt_form.find(".copy-btn").addClass("d-none");

    // If the user clicked the shortcut button the form gets posted right away
    var form_id = $(this).data("submit");
    if (form_id) {
      $opt_form.appendTo("#opt-form-container");
      $("#" + form_id).submit();

    // ...otherwise we add the form and tell the user that the form can still
    // be modified before it is posted
    } else {
      $opt_form.appendTo("#opt-form-container").slideDown();
      show_message("The command has been added to your workflow!" +
          " You can still review and change it below before it gets stored.",
          "alert-info");

      $(".opt-form-container-info").removeClass("d-none");

      // If the added item was sortable, re-init the enclosing sort container
      // TODO: Maybe we should trigger a custom "add" event on the container
      // and register a separate listener to re-init the sort-container in case
      if ($opt_form.parents(".sort-container").length) {
        sortable(".sort-container")
      }
    }
  });

  /*
   * Register click listener to add a new functionary. That is, copy the
   * functionary name from the input field, clone the functionary
   * html template, give it the copied name and append it to the functionary
   * container.
   *
   * The functionary template shows the given name and a dropzone to upload
   * a functionary public key. The dropzone is initialized when the template is
   * added.
   */
  $(document).on("click", "button.add-func-btn", function(evt){
    // Get the functionary name from the input field
    var functionary_name = $(".add-func-input").val();

    // Do some cheap front-end validation (name must be unique and not empty)
    if (functionary_name == "") {
      show_message("Your functionary needs a name!", "alert-warning");

    } else if ($("#functionary-container input[value='" +
        functionary_name + "']").length > 0) {
      show_message("You already have a functionary '"+ functionary_name + "'!",
          "alert-warning");

    } else {
      // If the name seems to be valid...
      // ... clone functionary template (hidden on the page) ...
      var $func = $(".template.functionary").clone();

      // ... add the name to a span that gets displayed and to a hidden input
      // element that gets posted to the server to associate functionary keys
      // with functionary names ...
      $func.find("span.functionary-name").text(functionary_name);
      $func.find("input[name='functionary_name']").val(functionary_name);

      // ... and append and show the template to the functionary container
      // and remove the template class
      $func.appendTo("#functionary-container")
        .slideDown(function(){
          $(this).removeClass("template");

          // Finally, initialize the contained file dropzone so that the user
          // can upload a public key for the added functionary
          init_functionary_dropzone($func.find(".dropzone"));
      });
    }
  })

  /*
   * Register click listener to remove a functionary. That is,
   * remove the functionary dropzone from the DOM and send a request to the
   * server to also remove the stored functionary and key.
   *
   * Functionaries only make sense together with a key, hence we don't
   * provide a way to just remove the key. Keys can be replaced though.
   */
  $(document).on("click", "button.rm-func-btn", function(evt) {
    // Find the relevant DOM elements relative to the clicked remove button
    $functionary = $(this).closest(".functionary");
    $dropzone = $functionary.find(".dropzone");
    var name = $functionary.find("input[name='functionary_name']").val();

    // We only bother to ask the server to remove the functionary if that
    // functionary already has a pubkey associated, because functionaries
    // without pubkeys are not stored on the server
    if ($dropzone.get(0).dropzone.files.length > 0) {
      // Post the name of the functionary to remove
      $.ajax({
        method: "POST",
        url: "/functionaries/remove",
        data: {"functionary_name": name},
        headers: _get_csrf_token_header(),
        success: function(response) {
          // Show any messages returned by the server
          show_messages(response.messages);

          // Only remove the functionary on client side if server side removal
          // was successful
          if (!response.error) {
            $functionary.slideUp(function(){
              $(this).remove();
            });
          }
        }
      });

    } else {
      // If there was no key to begin with we remove the functionary on
      // client side right away
      $functionary.slideUp(function(){
        $(this).remove();
      });
    }
  });

  /*
   * Register blur listener to re-generate/re-draw D3 graph when a
   * step name input field looses focus
   */
  $(document).on("blur", ".ssc-steps .ssc-step input[name='step_name[]']",
    function(evt){
      draw_graph(generate_graph_from_ssc_steps());
  });

  /*
   * Register custom removed event listener to re-generate/re-draw D3 graph
   * when a step form element got removed
   */
  $(document).on("custom.removed",
    function(evt, removed_elem_class){
      if (removed_elem_class == ".ssc-step")
        draw_graph(generate_graph_from_ssc_steps());
  });

  /*
   * Register sortable sortupdate event listener to re-generate/re-draw D3
   * graph when the step form elements got re-ordered
   */
  $(".sort-container.ssc-steps").on("sortupdate",
    function(evt) {
      draw_graph(generate_graph_from_ssc_steps());
  });

  /*
   * Initialize sortable plugin on `.sort-container`s to enable
   * drag and drop sorting.
   * Note:
   * Needs to be re-initialized when elements are added to the DOM
   */
   sortable(".sort-container", {
      forcePlaceholderSize: true,
      placeholderClass: "sort-placeholder",
   });

  /*
   * Register click listener that turns a pre html element into a textarea
   * and immediately selects the contents
   * This is a neat little feature for copy-paste snippets
   */
  $("pre.code").click(function(){
    // Extract (copy) all attributes of the clicked pre element
    var attrs = {};
    $.each(this.attributes, function(idx, attr) {
        attrs[attr.nodeName] = attr.nodeValue;
    });

    // We don't need red squiggly underlines for code snippets
    attrs["spellcheck"] = "false";

    // Create new empty element with above copied attributes, set it to
    // readonly and insert the text content from the clicked pre element
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

/*****************************************************************
 * Miscellaneous functions globally available
 ****************************************************************/

/*
 * Retrieve the CSRF token written by the server to a meta element in the page
 * header and format it so that it can be used as additional header for form
 * posting ajax calls
 */
function _get_csrf_token_header() {
  return {
    'X-CSRFToken': $('meta[name="csrftoken"]').attr('content')
  };
}

/*
 * Append passed message to DOM (using message template), and show for
 * a fixed amount of time (5 seconds) the second parameter is used as style
 * class.
 *
 * See https://v4-alpha.getbootstrap.com/components/alerts/ for available
 * types and styles.
 *
 * TODO: Some messages are too long to read them in 5 seconds and for
 * shorter messages 5 seconds seems too much.
 * We could calculate the time based on the length of the message
 *
 */
function show_message(msg, msg_type) {
  // If the type is none of below, use "alert-info" as default
  if ($.inArray(msg_type,
      ["alert-success", "alert-info", "alert-warning", "alert-danger"]) == -1)
    msg_type = "alert-info";

  // Find and clone the message template (hidden in the page)
  var $container = $("#alert-container");
  var $alert = $container.find(".alert.template").clone();
  $alert.find("span.alert-msg").text(msg);

  // Set the message style class, add it to the appropriate place and remove
  // the template class
  $alert.addClass(msg_type)
      .appendTo($container)
      .removeClass("template");

  // Remove message after 5 seconds
  setTimeout(function(){
    $alert.alert("close");
  }, 5000);
}

/*
 * Loop over a list of message tuples and call show_messages for each
 * Expected format is: [["<message type>", <message>"], ...]
 */
function show_messages(messages) {
  messages.forEach(function(message) {
    show_message(message[1], message[0]);
  });
}


/*
 * Initialize a functionary public key file upload dropzone on a
 * passed JQuery element and return the Dropzone object
 */
function init_functionary_dropzone($elem) {

  var opts = {
    paramName: "functionary_key",
    parallelUploads: 1,
    headers: _get_csrf_token_header(),
    init: function(file) {
      var prevFile;

      // Event triggered when a file was uploaded and the server
      // replied with 200
      this.on("success", function(file, response) {
        show_messages(response.messages);

        // If the new file could not be stored on the server we remove it
        // from the client dropzone
        if (response.error) {
          this.removeFile(file);

        } else {
          // If the new file was successfully stored on the server we
          // remove any previously existing file (replace)...
          if (typeof prevFile !== "undefined") {
            this.removeFile(prevFile);
          }
          // ...and keep a reference to the new file for future replacements
          prevFile = file;
        }
      });

      // This event gets triggered when the user drops or clicks to add a new
      // file, but also when we render files in a dropzone that were already
      // stored on the server.
      // In the latter case we want to safe a reference to the file (like
      // above after a successful upload) so that we can replace it.
      // To differentiate between those two cases we trigger the event with
      // an extra parameter `existing` and only if the event has that parameter
      // store the reference (see JS in functionaries.html).
      // Remember, for user added files we don't want to do this right away,
      // but only if the file was actually successfully stored on the server.
      // TODO: This feels a little hackish, maybe we can do better
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
 * Initialize a link file upload dropzone on a passed JQuery element and
 * return the Dropzone object.
 */
function init_link_dropzone($elem) {
  var opts = {
    paramName: "step_link",
    addRemoveLinks: true,
    parallelUploads: 1,
    dictRemoveFile: "Remove Link",
    headers: _get_csrf_token_header(),
    init: function(file) {
      // Event triggered when a file was uploaded and the server
      // replied with 200
      this.on("success", function(file, response) {
        // We set this made-up property on the file object to communicate to
        // the "removedfile" event listener, which listens for the event
        // triggered by the call below , that it should not go and actually
        // remove the file from the server.
        // TODO: This feels a little hackish, maybe we can do better
        file.removed_on_fontend_only = true;

        // When the server returns from a file upload, we remove all
        // automatically added file previews...
        this.removeFile(file);

        // ... and re-add previews only for the files that were actually
        // stored on the server (according to the server's response).
        // E.g. if we uploaded `links.tar.gz`, we only store and therefore only
        // want to display the contained `foo.link` and `bar.link`
        for (var i = 0; i < response.files.length; i++) {
          // Add (mock) previews for all the files that were actually stored
          // TODO: DRY add mock file
          uploaded_file = {name: response.files[i], size: 12345};
          this.emit("addedfile", uploaded_file);
          this.emit("complete", uploaded_file, true);
          this.files.push(uploaded_file);
        }
        show_messages(response.messages);
      });

      this.on("removedfile", function(file) {
        // If this property is set we don't actually want to remove the file
        // on the server, but just on the frontend
        if (file.removed_on_fontend_only)
          return;

        // Cache this (dropzone) to access it in inner scope which has its
        // own this
        var thiz = this;
        // Post the name of the functionary to remove
        $.post({
          method: "POST",
          url: "/chaining/remove",
          data: {"link_filename": file.name},
          headers: _get_csrf_token_header(),
          success: function(response) {
            show_messages(response.messages);

            // Re-add file (on client side) if server-side remove
            // was not successful
            if (response.error) {
              thiz.emit("addedfile", file);
              thiz.emit("complete", file, true);
              thiz.files.push(file);
            }
          }
        });
      });
    }
  };
  return new Dropzone($elem.get(0), opts);
}

/*
 * Traverse `.ssc_steps` (c.f. software_supply_chain.html)
 * and generate graph data suitable for `draw_graph`.
 *
 * Directed edges are created sequentially: E {node_i, node_i+1}
 * Only "modifying" nodes have outdegree. A modifying node remains the edge
 * source for all subsequent nodes until the next modifying node in the list.
 *
 * TODO: Find a way to display inspections
 *
 * Returns
 * {
 *   nodes: [
 *     {
 *       name: <step name>
 *     }
 *   ]
 *   edges: [
 *     {
 *       source: <step name> ,
 *       dest: <step name>
 *     }, ...
 *   ]
 * }
 */
function generate_graph_from_ssc_steps() {
  // Make a list of node objects (i.e.: [{name: <step_name>}] from
  // step name input fields, ignore steps without name
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
    // Skip non-modifying steps for edge sources
    // Only modifying steps, i.e. steps where materials and products are not
    // equal, have an outdegree
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
 * Draw in-toto layout graph using dagre-d3 and D3.js
 * https://github.com/cpettitt/dagre-d3/wiki
 */
function draw_graph(graph_data) {
  // Query the SVG element
  var svg = d3.select("svg.svg-content");

  // Remove existing content so that we can re-draw the graph
  svg.selectAll("*").remove();

  // Abort drawing if no nodes were passed
  if (graph_data.nodes.length < 1)
    return;

  // Create a new directed acyclic graph (dag)
  var dag = new dagreD3.graphlib.Graph({multigraph: true})

  // Create a left to right layout,
  // this controls the way the graph is displayed
  dag.setGraph({
    nodesep: 5,
    ranksep: 40,
    edgesep: 10,
    rankdir: "LR",
  });

  // Create nodes (steps and inspections) based on passed nodes data
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

  // Query the inner SVG group element that wraps the graph
  var inner = svg.append("g");

  // Set up drag/drop/zoom support
  var zoom = d3.behavior.zoom().on("zoom", function() {
        inner.attr("transform", "translate(" + d3.event.translate + ")" +
                                    "scale(" + d3.event.scale + ")");
      });
  svg.call(zoom);

  // Create the renderer ...
  var render = new dagreD3.render();

  // ... and run it to draw the graph
  render(inner, dag);

  // Scale and Center graph...

  // Get the SVG's container to access its width and height, i.e.
  // where the svg is visible
  var $outer = $(".svg-container");

  // Get width and height of the graph
  // Note: D3 elements are lists of objects having the DOM element at idx 0
  var inner_rect = inner[0][0].getBoundingClientRect();

  // Define a fixed padding between graph and viewport (px)
  var padding = 50;

  // Calculate how much we must scale the graph up or down to fit the container
  var scale = Math.min(($outer.width() - padding) / inner_rect.width,
      ($outer.height() - padding) / inner_rect.height);

  // Calculate distance from top and left to center the graph
  // Note: We have to translate between viewport and user coordinate system
  var top = ($outer.height() - inner_rect.height * scale) / 2;
  var left = ($outer.width() - inner_rect.width * scale) / 2;

  // Do the actual translate and scale
  zoom.translate([left, top]).scale(scale).event(svg);

  // Extend D3 selection's prototype to make an element first child
  d3.selection.prototype.toFront = function() {
    return this.each(function(){
      this.parentNode.appendChild(this);
    });
  };
  // Bring the edges to the front so that the nodes don't overlap the arrows
  // Note: There is no z-index for SVG, instead we have to mess with the order
  // of elements
  d3.select(".edgePaths").toFront();
}
