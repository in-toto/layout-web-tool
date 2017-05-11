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

  // Transform data
  var nodes = [], links = [];
  ["steps", "inspect"].forEach(function(item_type) {
    if (item_type in layout_data) {
      layout_data[item_type].forEach(function(item){

        var item_name = item.name;

        nodes.push({
          id: item_name,
          type: item._type
        });

        ["material_matchrules", "product_matchrules"].forEach(function(artifact_rules) {
          if (artifact_rules in item) {
            item[artifact_rules].forEach(function(rule) {
              if (rule[0].toLowerCase() == "match") {
                links.push({
                  source: item_name,
                  target: rule[rule.length - 1]
                });
              }
            });
          }
        });
      });
    }
  });

  var svg = d3.select("svg-content");
  var simulation = d3.forceSimulation()
      .force("charge", d3.forceManyBody())
      .force("link", d3.forceLink().id(function(d) { return d.id; }))
      .force("center", d3.forceCenter());

  var link = svg.append("g")
      .attr("class", "links")
      .selectAll("line")
      .data(links)
      .enter()
      .append("line");

  var node = svg.append("g")
      .attr("class", "nodes")
      .selectAll("circle")
      .data(nodes)
      .enter()
      .append("circle")
      .attr("r", 5);

  node.append("title")
    .text(function(d) {
      return d.id;
    });

  simulation.nodes(nodes)
    .on("tick", function() {
    link.attr("x1", function(d) { return d.source.x; })
      .attr("y1", function(d) { return d.source.y; })
      .attr("x2", function(d) { return d.target.x; })
      .attr("y2", function(d) { return d.target.y; })

    node.attr("cx", function(d) { return d.x; })
        .attr("cy", function(d) { return d.y; });
  });

  simulation.force("link").links(links);
  
}


