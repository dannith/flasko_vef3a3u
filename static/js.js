$( document ).ready(function(){
    $(".button-collapse").sideNav();
    $('.slider').slider({full_width: true});
    $('select').material_select();
    $('.collapsible').collapsible({
      accordion : false // A setting that changes the collapsible behavior to expandable instead of the default accordion style
    });
})