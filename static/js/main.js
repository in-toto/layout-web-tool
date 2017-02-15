/*
 * Register click/change listeners to add and remove dynamic form elements
 *
 * We do not directly listen on the elements but on the document instead
 * to allow dynamic creation of content (delegation).
 *
 * NOTE 1: There are a lot of different ways to achieve below result.
 * The Event-based is a personal preference.
 * In any case this could be more DRY, maybe at the cost of readability?
 */
$(document).on("click", "button.add-step", function(evt) {
  // Query the template, clone it, remove the property that hid it
  // and append it to the correct target inside the form.
  $(".step.template").clone().removeClass("template")
      .appendTo("#step-container-inner");
});

$(document).on("click", "button.add-inspection", function(evt) {
  // Query the template, clone it, remove the property that hid it
  // and append it to the correct target inside the form.
  $(".inspection.template").clone().removeClass("template")
      .appendTo("#inspection-container-inner");
});
$(document).on("change", "select.add-rule", function(evt) {
  // Rule type must be one of
  // "match", "allow", "disallow", "create", "delete", "modify"
  var rule_type = $(this).find("option:selected").val();

  // We identifiy the target by searching up the DOM for the
  // element that contains the rules and the rule picker (i.e. rule-container),
  // then we search down for the rule-container-inner that contains only
  // the rules.
  var $target = $(this).closest(".rule-container")
      .find(".rule-container-inner");

  // Finally query the template, clone it, remove the property that hid it
  // and  append it to the correct target inside the form.
  $(".rule.template." + rule_type).clone().removeClass("template")
      .appendTo($target);
});

// Register click listener to remove dynamic nested form elements
// Find container element and remove it.
$(document).on("click", "button.remove-step", function(evt){
  $(this).closest(".step").remove();
});
$(document).on("click", "button.remove-inspection", function(evt){
  $(this).closest(".inspection").remove();
});
$(document).on("click", "button.remove-rule", function(evt){
  $(this).closest(".rule").remove();
});
