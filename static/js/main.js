
/* ----------------------------------------------------------------------------
 * DOM to JSON functions for main layout form
 * ----------------------------------------------------------------------------
 */


/*
 * Create array of values from input and select form elements and create
 * a rule array.
 * NOTE: This function is sensitive to DOM changes
 *
 */
var jsonify_rule = function($rule) {
  // NOTE: We have to wrap the returned array of rule elements into another
  // array because this function gets called inside other map functions and
  // jQuery's map would just concatenate the returned arrays, e.g.:
  //
  // $.map([["CREATE", "foo"], ["ALLOW", "*"]], function(array){
  //    return array;
  // })
  // Would produce ["CREATE", "foo", "ALLOW", "*"] but we want
  // [["CREATE", "foo"], ["ALLOW", "*"]]
  //
  return [
    $rule.find("input,select").map(function() {
      return $(this).val();
    }).toArray()
  ];
}


/*
 * Traverse form group for one step and assign the input fields values to
 * a JSON object.
 * NOTE: This function is sensitive to DOM changes
 *
 */
var jsonify_step = function($step) {
  var data = {};

  // Find and assign simple text input values
  data.name = $step.find("input[name='step_name']").val();
  data.expected_command = $step.find("input[name='step_cmd']").val();

  // Returns the selected keyids or an empty array.
  data.pubkeys = $step.find("select[name='step_keyid[]']").val()

  // Iterate over material rule form groups and assign created array of
  // material rule arrays
  data.material_matchrules = $step
      .find(".material-rules .rule")
      .map(function() {
        return jsonify_rule($(this));
  }).toArray();

  // Iterate over product rule form groups and assign created array of
  // product rule arrays
  data.product_matchrules = $step
      .find(".product-rules .rule")
      .map(function() {
        return jsonify_rule($(this));
  }).toArray();

  return data;
}


/*
 * Traverse form group for one inspection and assign the input fields values to
 * a JSON object.
 * NOTE: This function is sensitive to DOM changes
 *
 */
var jsonify_inspection = function($inspection) {
  var data = {};

  // Find and assign simple text input values
  data.name = $inspection.find("input[name='inspection_name']").val();
  data.run = $inspection.find("input[name='inspection_run']").val();

  // Iterate over material rule form groups and assign created array of
  // material rule arrays
  data.material_matchrules = $inspection
      .find(".material-rules .rule")
      .map(function() {
        return jsonify_rule($(this));
  }).toArray();

  // Iterate over product rule form groups and assign created array of
  // product rule arrays
  data.product_matchrules = $inspection
      .find(".product-rules .rule")
      .map(function() {
        return jsonify_rule($(this));
  }).toArray();

  return data;
}


/*
 * Traverse layout form and assign the input fields values to a JSON object.
 * NOTE: This function is sensitive to DOM changes
 *
 * The returned json_data contains some additional fields that are not
 * in-toto layout conformant and will be removed/replaced on server side:
 *   - layout_name_old:
 *          the current file name of the layout
 *   - layout_name_new:
 *          the new file name of the layout (if changed)
 *   - layout_pubkey_ids:
 *          a list of public key ids
 *          the server has to load the keys from the <session>/pubkeys dir as
 *          key dictionary and assign it to the layout.keys attribute instead
 *    - layout.expires:
 *          must be converted into a zulu timestamp
 *
 */
var jsonify_layout = function($form) {
  var data = {};

  // Find and assign simple text input values
  data.layout_name_old = $form.find("input[name='layout_name_old']").val();
  data.layout_name_new = $form.find("input[name='layout_name_new']").val();
  data.expires = $form.find("input[name='layout_expires']").val();

  // Iterate over selected layout keyids and assign created array
  data.layout_pubkey_ids = $form
      .find("select[name='layout_keyid[]'] option:selected")
      .map(function() {
        return $(this).val();
  }).toArray();

  // Iterate over step form groups and assign created array of step JSON
  // objects
  data.steps = $form.find(".step-container .step")
      .map(function() {
        return jsonify_step($(this));
  }).toArray();

  // Iterate over inspection form groups and assign created array of
  // inspection JSON objects
  data.inspect = $form.find(".inspection-container .inspection")
      .map(function() {
        return jsonify_inspection($(this));
  }).toArray();

  return data;
}

/*
 * Takes a jQuery form object and a JSON data object as arguments,
 * creates a new form, copying the method and action attributes from the
 * passed form and adding a single text input named "json_data" with the
 * passed stringified json_data as value and submit it.
 *
 */
var submit_layout_as_json = function($form, json_data) {
  // Copy relevant attributes from the original form
  var method = $form.attr("method");
  var action = $form.attr("action");

  // Create a new (hidden) form object, assign action and method from the
  // original form to it and append one text input field that contains the
  // stringified JSON data.
  var $ghost_form = $("<form />", {
    action: action,
    method: method,
    type: "application/json",
    style: "display: none;"
  }).append($("<input />", {
      type: "hidden",
      name: "json_data",
      value: JSON.stringify(json_data)
  }));

  // Some browsers require a form to be part of the document body before submit
  // But it will be gone when the server returns.
  $ghost_form.appendTo("body").submit();
}





/* ----------------------------------------------------------------------------
 * Register Event Listener
 * ----------------------------------------------------------------------------
 *
 * Register click listeners to add and remove dynamic form elements
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
$(document).on("click", "button.add-rule", function(evt) {
  // Rule type must be one of
  // "match", "allow", "disallow", "create", "delete", "modify"
  var rule_type = $(this).closest(".add-rule-container")
      .find("option:selected").val();

  // We identify the target by searching up the DOM for the
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


// Register change listener to update step pubkey options
// on pubkey select/de-select in layout
$(document).on("change", "select[name='layout_keyid[]']", function(evt){

  // Get the currently selected layout pubkey option elements
  // Only those should be available in the step pubkeys selection
  var $layout_pubkey_options = $(evt.target).find("option:selected");

  // Iterate over all steps' pubkeys selections and replace the options
  // (without losing existing selections)
  $("select[name='step_keyid[]']").each(function(){

    // Cache the selected pubkeys
    var selected_pubkeys = $(this).val();

    // Replace the selects options with a reset clone of the
    // layout_pubkey_options
    $(this).html(
      $layout_pubkey_options
        .clone()
        .prop("selected", false)
    );

    // And finally re-apply the selections
    // Vals that are no longer there are ignored
    $(this).val(selected_pubkeys);

  });

});


/*
 * Register layout form submit listener to intercept vanilla form post
 * and parse the form input values into a JSON object and submit that instead
 *
 * Since the layout form is nested and dynamic this approach is preferred over
 * keeping track of nested form data names. Which would require to increment
 * or decrement indices in the name attributes of input elements each time
 * we add or remove dynamic form elements.
 *
 */
$("#layout-form").on("submit", function(evt) {
  // Preventing default and stopping propagation here instead of returning
  // false, cancels the default submit even if below JavaScript has an error
  evt.preventDefault();
  evt.stopPropagation();

  // Create an in-toto layout from the user inputs ...
  var layout_json = jsonify_layout($(this));
  console.log(layout_json)

  // ... and submit the stringified JSON data.
  submit_layout_as_json($(this), layout_json);
})
