/* VilleSignal — scripts communs à toutes les pages */
document.addEventListener("DOMContentLoaded", () => {
    /* 1. Barre de navigation : ombre au scroll */
    const topbar = document.querySelector(".topbar");
    const onScroll = () => topbar && topbar.classList.toggle("scrolled", window.scrollY > 10);
    window.addEventListener("scroll", onScroll, { passive: true });
    onScroll();

    /* 2. Menu mobile */
    const toggle = document.getElementById("menuToggle");
    const nav = document.getElementById("mainNav");
    if (toggle && nav) {
        toggle.addEventListener("click", () => {
            const open = nav.classList.toggle("open");
            toggle.classList.toggle("open", open);
            toggle.setAttribute("aria-expanded", open);
        });
    }

    /* 3. Apparition progressive des éléments au scroll */
    const reveals = document.querySelectorAll(".reveal");
    if ("IntersectionObserver" in window) {
        const io = new IntersectionObserver((entries) => {
            entries.forEach((e) => {
                if (e.isIntersecting) {
                    e.target.classList.add("visible");
                    io.unobserve(e.target);
                }
            });
        }, { threshold: 0.12 });
        reveals.forEach((el, i) => {
            el.style.transitionDelay = (i % 3) * 90 + "ms";
            io.observe(el);
        });
    } else {
        reveals.forEach((el) => el.classList.add("visible"));
    }

    /* 4. Compteurs animés (page d'accueil) */
    const counters = document.querySelectorAll("[data-count]");
    const animate = (el) => {
        const target = parseInt(el.dataset.count, 10) || 0;
        if (target === 0) { el.textContent = "0"; return; }
        const duration = 1400;
        const start = performance.now();
        const step = (now) => {
            const p = Math.min((now - start) / duration, 1);
            el.textContent = Math.round(target * (1 - Math.pow(1 - p, 3)));
            if (p < 1) requestAnimationFrame(step);
        };
        requestAnimationFrame(step);
    };
    if ("IntersectionObserver" in window) {
        const co = new IntersectionObserver((entries) => {
            entries.forEach((e) => {
                if (e.isIntersecting) { animate(e.target); co.unobserve(e.target); }
            });
        }, { threshold: 0.6 });
        counters.forEach((c) => co.observe(c));
    } else {
        counters.forEach(animate);
    }

    /* 5. Messages flash : fermeture manuelle + disparition automatique */
    document.querySelectorAll(".alert").forEach((alert) => {
        const close = () => {
            alert.classList.add("hide");
            setTimeout(() => alert.remove(), 400);
        };
        const btn = alert.querySelector("button");
        if (btn) btn.addEventListener("click", close);
        setTimeout(close, 7000);
    });

    /* 6. Anti double-envoi sur tous les formulaires POST */
    document.querySelectorAll("form[method='post'], form[method='POST']").forEach((form) => {
        form.addEventListener("submit", () => {
            if (!form.checkValidity()) return;
            const btn = form.querySelector("button[type='submit']");
            if (btn && !btn.dataset.noLock) {
                setTimeout(() => { btn.disabled = true; btn.style.opacity = ".7"; }, 0);
            }
        });
    });
});
