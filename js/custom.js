(function ($) {

    "use strict";

        // PRE LOADER
        $(window).load(function(){
          $('.preloader').delay(500).slideUp('slow'); // set duration in brackets    
        });


        // MENU
        $('.navbar-collapse a').on('click',function(){
          $(".navbar-collapse").collapse('hide');
        });

        $(window).scroll(function() {
          if ($(".navbar").offset().top > 50) {
            $(".navbar-fixed-top").addClass("top-nav-collapse");
              } else {
                $(".navbar-fixed-top").removeClass("top-nav-collapse");
              }
        });


        // PARALLAX JS
        function initParallax() {
          $('#home').parallax("60%", 100);
          $('#about').parallax("100%", 80);
          $('#project').parallax("80%", 60);
          $('#team').parallax("40%", 40);
          $('#contact').parallax("20%", 20);
          }
        initParallax();


        // Owl Carousel
        var owl = $("#owl-team");
          owl.owlCarousel({
            autoPlay: 6000,
            items : 4,
            itemsDesktop : [1199,3],
            itemsDesktopSmall : [979,3],
            itemsTablet: [768,2],
            itemsTabletSmall: false,
            itemsMobile : [479,1],
            Speedfast: 200,
        });

})(jQuery);

// Add this to your scripts (e.g., custom.js)
document.addEventListener('DOMContentLoaded', function() {
  const filmCards = document.querySelectorAll('.film-card');
  
  filmCards.forEach(card => {
    card.addEventListener('click', function(e) {
      // Close other open cards first
      filmCards.forEach(otherCard => {
        if (otherCard !== card && otherCard.classList.contains('active')) {
          otherCard.classList.remove('active');
        }
      });
      // Toggle current card
      card.classList.toggle('active');
      e.stopPropagation(); // Prevent document-wide clicks
    });
  });

  // Close overlays when clicking outside
  document.addEventListener('click', function() {
    filmCards.forEach(card => card.classList.remove('active'));
  });
});