$(function() {
  /*
   * Click listener to toggle option form in the option grid and toggle active
   * class.
   * Cases:
   * Form is shown (stays shown) if checkbox is checked
   * Form is hidden (stays hidden) if checkbox is unchecked
   * Form is toggled if click occurs outside of checkbox in the option cell
   */
  $(".opt-content").on("click", function(evt) {
    var $opt_form_cont = $(this).parent(".opt-cell").find(".opt-form-cont");

    // Hide all others
    $(".opt-form-cont").not($opt_form_cont).slideUp();
    $(".opt-content").not(this).removeClass("active");

    // If the checkbox is checked we always show (leave shown)
    // and hide (leave hidden) if unchecked.
    if (evt.target.type == "checkbox") {
      if (evt.target.checked) {
        $opt_form_cont.slideDown();
        $(this).addClass("active");

      } else {
        $opt_form_cont.slideUp();
        $(this).removeClass("active");
      }
    // If something other than a checkbox is clicked we just toggle
    } else {
      $opt_form_cont.slideToggle();
      $(this).toggleClass("active");
    }
  });

  /*
   * Click listener to add and show "custom command" form
   */
  $("#add-cmd").on("click", function(evt){
    $(".opt-form.template")
        .clone()
        .appendTo("#custom-cmd-container")
        .slideDown(function(){
          $(this).removeClass("template");
        })
  });

  /*
   * Click listener to hide and remove "custom command" form
   */
  $(document).on("click", "button.rm-cmd", function(evt) {
    $(this).closest(".opt-form").slideUp(function(){
      $(this).remove();
    });
  });


  /*
   * Initialize drag and drop sorting
   */
   sortable(".sort-container", {
      forcePlaceholderSize: true,
      placeholderClass: "sort-placeholder",
   });



  /*
   * Draw in-toto layout graph using D3.js
   * FIXME: modularize don't use data from global variable `layout_data`
   * (c.f. software_supply_chain.html)
   */
  draw_graph(layout_data);
});




var draw_graph = function(layout_data) {
  var nodes = [],
      links = [];

  // Create nodes of steps and insepctions arrays and link array based on
  // material and product matchrules of type "MATCH" from in-toto layout
  ["steps", "inspect"].forEach(function(item_type) {
    if (item_type in layout_data) {
      layout_data[item_type].forEach(function(item){
        nodes.push({
          name: item.name,
          type: item._type
        });

        ["material_matchrules", "product_matchrules"]
            .forEach(function(artifact_rules) {

          if (artifact_rules in item) {
            item[artifact_rules].forEach(function(rule) {
              if (rule[0].toLowerCase() == "match") {
                links.push({
                  source: item.name,
                  // FIXME: in_toto.artifact_rule.unpack_rule would come in
                  // handy here.
                  // We'll probably move the whole data transformation to
                  // the server
                  target: rule[rule.length - 1],
                  rule: rule
                });
              }
            });
          }
        });
      });
    }
  });

  // Create a new directed graph
  var g = new dagreD3.graphlib.Graph()

  // Create a left to right layout
  g.setGraph({
    nodesep: 70,
    ranksep: 50,
    rankdir: "RL",
    marginx: 20,
    marginy: 20
  });

  // Automatically label each of the nodes
  nodes.forEach(function(node) {
    g.setNode(node.name,
      {
        label: node.name
      });
  });

  links.forEach(function(link){
    g.setEdge(link.source, link.target,
      {
        //label: link.rule[1]
      });
  });

  var svg = d3.select("svg.svg-content"),
      inner = svg.append("g");

  // Set up drag/drop/zoom support
  var zoom = d3.behavior.zoom().on("zoom", function() {
        inner.attr("transform", "translate(" + d3.event.translate + ")" +
                                    "scale(" + d3.event.scale + ")");
      });
  svg.call(zoom);

  // Create the renderer
  var render = new dagreD3.render();

  // Run the renderer. This is what draws the final graph.
  render(inner, g);
}


