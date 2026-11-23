document.addEventListener("DOMContentLoaded", function () {

    const navbar = document.getElementById("paNavbar");
    const menuToggle = document.getElementById("paMenuToggle");
    const navMenu = document.getElementById("paNavMenu");

    // NAVBAR SCROLL EFFECT
    function handleNavbarScroll() {
        if (!navbar) return;

        navbar.classList.toggle(
            "scrolled",
            window.scrollY > 40
        );
    }

    handleNavbarScroll();

    window.addEventListener(
        "scroll",
        handleNavbarScroll,
        { passive: true }
    );


    // MOBILE NAVIGATION
    if (menuToggle && navMenu) {

        menuToggle.addEventListener("click", function () {

            const isOpen = navMenu.classList.toggle("open");

            menuToggle.classList.toggle("active", isOpen);

            menuToggle.setAttribute(
                "aria-expanded",
                String(isOpen)
            );
        });

        // Close mobile menu after selecting a link
        navMenu.querySelectorAll("a").forEach(function (link) {

            link.addEventListener("click", function () {

                navMenu.classList.remove("open");
                menuToggle.classList.remove("active");

                menuToggle.setAttribute(
                    "aria-expanded",
                    "false"
                );
            });
        });
    }


    // DROPDOWN MENUS
    const dropdowns = document.querySelectorAll(
        ".pa-nav-dropdown"
    );

    dropdowns.forEach(function (dropdown) {

        const button = dropdown.querySelector(
            ".pa-dropdown-toggle"
        );

        if (!button) return;

        button.addEventListener("click", function (event) {

            event.stopPropagation();

            const willOpen = !dropdown.classList.contains("open");

            dropdowns.forEach(function (otherDropdown) {

                otherDropdown.classList.remove("open");

                const otherButton = otherDropdown.querySelector(
                    ".pa-dropdown-toggle"
                );

                if (otherButton) {
                    otherButton.setAttribute(
                        "aria-expanded",
                        "false"
                    );
                }
            });

            if (willOpen) {
                dropdown.classList.add("open");

                button.setAttribute(
                    "aria-expanded",
                    "true"
                );
            }
        });
    });


    // CLOSE DROPDOWNS WHEN CLICKING OUTSIDE
    document.addEventListener("click", function (event) {

        if (!event.target.closest(".pa-nav-dropdown")) {

            dropdowns.forEach(function (dropdown) {

                dropdown.classList.remove("open");

                const button = dropdown.querySelector(
                    ".pa-dropdown-toggle"
                );

                if (button) {
                    button.setAttribute(
                        "aria-expanded",
                        "false"
                    );
                }
            });
        }
    });


    // SCROLL REVEAL ANIMATIONS
    const revealElements = document.querySelectorAll(
        ".pa-reveal"
    );

    if ("IntersectionObserver" in window) {

        const revealObserver = new IntersectionObserver(
            function (entries, observer) {

                entries.forEach(function (entry) {

                    if (entry.isIntersecting) {

                        entry.target.classList.add("visible");

                        observer.unobserve(entry.target);
                    }
                });

            },
            {
                threshold: 0.12,
                rootMargin: "0px 0px -35px 0px"
            }
        );

        revealElements.forEach(function (element) {
            revealObserver.observe(element);
        });

    } else {

        revealElements.forEach(function (element) {
            element.classList.add("visible");
        });
    }


    // SMOOTH SCROLL FOR INTERNAL LINKS
    document.querySelectorAll(
        '.pa-home a[href^="#"]'
    ).forEach(function (link) {

        link.addEventListener("click", function (event) {

            const targetId = link.getAttribute("href");

            if (!targetId || targetId === "#") return;

            const target = document.querySelector(targetId);

            if (!target) return;

            event.preventDefault();

            target.scrollIntoView({
                behavior: window.matchMedia(
                    "(prefers-reduced-motion: reduce)"
                ).matches ? "auto" : "smooth",
                block: "start"
            });
        });
    });


    // HERO VIDEO FALLBACK
    const heroVideo = document.querySelector(
        ".pa-hero-video"
    );

    if (heroVideo) {

        heroVideo.addEventListener("error", function () {
            heroVideo.style.display = "none";
        });

        const reducedMotion = window.matchMedia(
            "(prefers-reduced-motion: reduce)"
        );

        if (reducedMotion.matches) {
            heroVideo.pause();
            heroVideo.style.display = "none";
        }
    }

});