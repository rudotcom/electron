$(document).ready(function(){

	// Mobile menu
	$('.mobile-menu-icon').click(function(){
		$('.tm-nav').slideToggle();
	});

	$( window ).resize(function() {
		if($( window ).width() > 767) {
			$('.tm-nav').show();
			$('.group-farm').css('margin-left', 400);
		
		} else if ($( window ).width() > 500) {
			$('.tm-nav').show();
			$('.group-farm').css('margin-left', 200);
		
		} else {
			$('.tm-nav').hide();
			$('.group-farm').css('margin-left', 0);
		}
	});

  // http://stackoverflow.com/questions/2851663/how-do-i-simulate-a-hover-with-a-touch-in-touch-enabled-browsers
  $('body').bind('touchstart', function() {});

  // Smooth scroll
  // https://css-tricks.com/snippets/jquery/smooth-scrolling/
  $('a[href*=#]:not([href=#])').click(function() {
    if (location.pathname.replace(/^\//,'') == this.pathname.replace(/^\//,'') && location.hostname == this.hostname) {
      var target = $(this.hash);
      target = target.length ? target : $('[name=' + this.hash.slice(1) +']');
      if (target.length) {
        $('html,body').animate({
          scrollTop: target.offset().top
        }, 1000);
        return false;
      }
    }
  });

    $(".hide-toast").click(function(){
        $(".toast").toast('hide');
    });
});
$('#myTab a').on('click', function (e) {
  e.preventDefault()
  $(this).tab('show')
})