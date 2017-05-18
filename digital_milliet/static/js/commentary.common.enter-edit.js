
var remove_input = function(target) {
  target.remove();
};
var add_input = function(model, target) {
      var formgroup = $(model[0]).clone();
      formgroup.attr("id", "");
      formgroup.find(".add-input").on("click", function (e) {
          e.preventDefault();
          add_input(model, target);
      });
      formgroup.find(".rem-input").on("click", function (e) {
          e.preventDefault();
          remove_input(formgroup);
      });

      target.append(formgroup);

  };