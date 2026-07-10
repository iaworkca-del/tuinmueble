// Movimiento natural de la interfaz: aparición al hacer scroll + transición de imagen.
(function () {
  const prefiereMenos =
    window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  // ── Aparición de tarjetas al entrar en pantalla ──
  if (!prefiereMenos && "IntersectionObserver" in window) {
    const items = document.querySelectorAll(".card, .historial-card");
    const observador = new IntersectionObserver(
      function (entradas) {
        entradas.forEach(function (e) {
          if (e.isIntersecting) {
            e.target.classList.add("en-vista");
            observador.unobserve(e.target);
          }
        });
      },
      { threshold: 0.08, rootMargin: "0px 0px -40px 0px" }
    );
    items.forEach(function (el, i) {
      el.classList.add("reveal-init");
      el.style.transitionDelay = Math.min(i * 55, 280) + "ms";
      observador.observe(el);
    });
  }

  // ── Fondo parallax: se mueve más lento que el scroll ──
  const fondo = document.querySelector(".parallax-fondo");
  if (fondo && !prefiereMenos) {
    let ticking = false;
    window.addEventListener(
      "scroll",
      function () {
        if (!ticking) {
          window.requestAnimationFrame(function () {
            fondo.style.transform = "translateY(" + window.scrollY * 0.35 + "px)";
            ticking = false;
          });
          ticking = true;
        }
      },
      { passive: true }
    );
  }

  // ── Transición suave al cambiar la imagen de la vista previa ──
  const main = document.getElementById("mainPreview");
  if (main && !prefiereMenos) {
    document.querySelectorAll(".thumb").forEach(function (t) {
      t.addEventListener("click", function () {
        main.classList.add("cambiando");
        setTimeout(function () {
          main.classList.remove("cambiando");
        }, 220);
      });
    });
  }
})();
