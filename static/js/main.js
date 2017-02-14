// Register buttons
// We do not directly listen on the elements but on the document instead
// to allow dynamic creation of content (delegation).
// TODO: We could DRY-up step/inspection/material add and remove
// They do similar things.

$(document).on("click", "button.add-step", function(evt){
  $(".step.template")
    .clone()
    .removeClass("template")
    .appendTo("#step-container");
});
$(document).on("click", "button.remove-step", function(evt){
  $(this).closest(".step").remove();
});

$(document).on("click", "button.add-inspection", function(evt){
  $(".inspection.template")
    .clone()
    .removeClass("template")
    .appendTo("#inspection-container");
});
$(document).on("click", "button.remove-inspection", function(evt){
  $(this).closest(".inspection").remove();
});
