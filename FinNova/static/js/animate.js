
document.addEventListener('DOMContentLoaded', () => {
gsap.from("#hero-title", {
    y: -50,
    opacity: 0,
    duration: 1.2,
    ease: "power3.out",
    color: "  linear-gradient(90deg, rgba(2,0,36,1) 0%, rgba(9,9,121,1) 35%, rgba(0,212,255,1) 100%)"
});

gsap.from("#hero-tagline", {
    y: 20,
    opacity: 0,
    delay: 0.5,
    duration: 1.2,
    ease: "power2.out"
});

gsap.to("#hero-tagline", {
    repeat: -1,
    yoyo: true,
    duration: 1.8,
    ease: "sine.inOut",
    color: "#4f46e5", 
    delay: 2
});



gsap.from("#hero-logo", {
    scale: 0.5,
    opacity: 0,
    duration: 1,
    delay: 0.2,
    ease: "back.out(1.7)"
  });
  



});
