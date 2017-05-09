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

  console.log(layout_data);
  // var svg = d3.select("body")

});