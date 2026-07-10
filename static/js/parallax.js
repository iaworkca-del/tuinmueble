(function () {
  var nav = document.querySelector('.pub-nav');
  var heroBg = document.querySelector('.pub-hero-bg');

  function onScroll() {
    var y = window.scrollY || window.pageYOffset;
    if (nav) {
      if (y > 40) nav.classList.add('scrolled');
      else nav.classList.remove('scrolled');
    }
    if (heroBg) {
      heroBg.style.transform = 'translateY(' + (y * 0.35) + 'px)';
    }
  }

  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  var revelables = document.querySelectorAll('.pub-reveal');
  if ('IntersectionObserver' in window && revelables.length) {
    var obs = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible');
          obs.unobserve(entry.target);
        }
      });
    }, { threshold: 0.15 });
    revelables.forEach(function (el) { obs.observe(el); });
  } else {
    revelables.forEach(function (el) { el.classList.add('visible'); });
  }
})();
