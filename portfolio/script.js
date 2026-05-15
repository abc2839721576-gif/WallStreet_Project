document.addEventListener('DOMContentLoaded', () => {

    // 1. Navbar Scroll Effect
    const navbar = document.getElementById('navbar');
    window.addEventListener('scroll', () => {
        if (window.scrollY > 50) {
            navbar.classList.add('scrolled');
        } else {
            navbar.classList.remove('scrolled');
        }
    });

    // 2. Smooth Scroll for Anchors
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const targetId = this.getAttribute('href');
            if(targetId === '#') return;
            const targetElement = document.querySelector(targetId);
            if(targetElement) {
                targetElement.scrollIntoView({
                    behavior: 'smooth'
                });
            }
        });
    });

    // 3. Intersection Observer for Fade-Up and Progress Bars
    const observerOptions = {
        root: null,
        rootMargin: '0px',
        threshold: 0.1
    };

    const animateNumbers = (element) => {
        const target = parseInt(element.getAttribute('data-target'));
        const duration = 1500; // ms
        const frameDuration = 1000 / 60;
        const totalFrames = Math.round(duration / frameDuration);
        let frame = 0;

        // Easing function (ease-out-expo)
        const easeOutExpo = (t) => {
            return t === 1 ? 1 : 1 - Math.pow(2, -10 * t);
        };

        const counter = setInterval(() => {
            frame++;
            const progress = easeOutExpo(frame / totalFrames);
            const currentVal = Math.round(target * progress);
            
            element.textContent = currentVal;

            if (frame === totalFrames) {
                element.textContent = target;
                clearInterval(counter);
            }
        }, frameDuration);
    };

    const observer = new IntersectionObserver((entries, obs) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                // Fade Up
                if (entry.target.classList.contains('fade-up')) {
                    entry.target.classList.add('visible');
                }
                
                // Numbers Animation
                const numbers = entry.target.querySelectorAll('.num');
                numbers.forEach(num => {
                    if (!num.classList.contains('animated')) {
                        animateNumbers(num);
                        num.classList.add('animated');
                    }
                });

                // Progress Bars
                const progressBars = entry.target.querySelectorAll('.progress');
                progressBars.forEach(bar => {
                    const targetWidth = bar.getAttribute('data-width');
                    bar.style.width = targetWidth;
                });

                obs.unobserve(entry.target);
            }
        });
    }, observerOptions);

    document.querySelectorAll('.fade-up, .dash-card, .skill-item').forEach(el => {
        observer.observe(el);
    });

    // 4. Hero Mouse Follow Glow
    const hero = document.getElementById('hero');
    const glow = document.querySelector('.hero-glow');
    
    if(hero && glow) {
        hero.addEventListener('mousemove', (e) => {
            const rect = hero.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            
            // Adjust glow position so it centers on mouse
            glow.style.left = `${x - glow.offsetWidth / 2}px`;
            glow.style.top = `${y - glow.offsetHeight / 2}px`;
        });
    }
});
