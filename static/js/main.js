$(function() {

  // Initialize option form container collapsibles
  // https://v4-alpha.getbootstrap.com/components/collapse/
  $(".opt-form-cont").collapse({
     toggle: false,
  });

  // Show/Hide/Toggle forms and toggle "active"class
  $(".opt-content").on("click", function(evt) {
    var opt_form_cont = "#" + $(this).data("target");

    // Hide all others
    $(".opt-form-cont").not(opt_form_cont).collapse("hide")
    $(".opt-content").not(this).removeClass("active")

    // If the checkbox is checked we always show (leave shown)
    // and hide (leave hidden) if unchecked.
    if (evt.target.type == "checkbox") {
      if (evt.target.checked) {
        $(opt_form_cont).collapse("show");
        $(this).addClass("active");

      } else {
        $(opt_form_cont).collapse("hide");
        $(this).removeClass("active");
      }
    // If something other than a checkbox is clicked we just toggle
    } else {
      $(opt_form_cont).collapse("toggle");
      $(this).toggleClass("active");
    }
  });


  $("#add-cmd").on("click", function(evt){
    $(".opt-form.template")
        .clone()
        .appendTo("#custom-cmd-container")
        .slideDown(function(){
          $(this).removeClass("template");
        })
  });

  $(document).on("click", "button.rm-cmd", function(evt) {
    $(this).closest(".opt-form").slideUp(function(){
      $(this).remove();
    });
  });
});