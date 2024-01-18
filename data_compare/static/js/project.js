
// Enable tooltip
// TODO: Tooltip does not work on edit/delete icons
const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));


(function(){
  console.log("Hello World!")
})();
