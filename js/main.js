(function() {
  // ===== NAV SCROLL =====
  const nav = document.getElementById('navbar');
  window.addEventListener('scroll', () => {
    nav.classList.toggle('scrolled', window.scrollY > 80);
  });

  // ===== MOBILE MENU =====
  const menuToggle = document.getElementById('menuToggle');
  const mobileMenu = document.getElementById('mobileMenu');

  menuToggle.addEventListener('click', () => {
    menuToggle.classList.toggle('open');
    mobileMenu.classList.toggle('open');
    document.body.style.overflow = mobileMenu.classList.contains('open') ? 'hidden' : '';
  });

  mobileMenu.querySelectorAll('a').forEach(link => {
    link.addEventListener('click', () => {
      menuToggle.classList.remove('open');
      mobileMenu.classList.remove('open');
      document.body.style.overflow = '';
    });
  });

  // ===== LIGHTBOX =====
  const lightbox = document.getElementById('lightbox');
  const lightboxImg = document.getElementById('lightboxImg');
  let currentIndex = 0;
  let visibleItems = [];

  function getVisibleItems() {
    return [...document.querySelectorAll('.gallery-item:not(.hidden)')];
  }

  function openLightbox(index) {
    visibleItems = getVisibleItems();
    currentIndex = index;
    const item = visibleItems[currentIndex];
    const img = item.querySelector('img');
    lightboxImg.src = img.src.replace('w=600', 'w=1400').replace('w=800', 'w=1400');
    lightboxImg.alt = img.alt;
    lightbox.classList.add('active');
    document.body.style.overflow = 'hidden';
  }

  function closeLightbox() {
    lightbox.classList.remove('active');
    document.body.style.overflow = '';
  }

  function navigate(dir) {
    visibleItems = getVisibleItems();
    currentIndex = (currentIndex + dir + visibleItems.length) % visibleItems.length;
    const item = visibleItems[currentIndex];
    const img = item.querySelector('img');
    lightboxImg.src = img.src.replace('w=600', 'w=1400').replace('w=800', 'w=1400');
    lightboxImg.alt = img.alt;
  }

  const galleryItems = document.querySelectorAll('.gallery-item');
  galleryItems.forEach((item, i) => {
    item.addEventListener('click', () => {
      const vis = getVisibleItems();
      const idx = vis.indexOf(item);
      openLightbox(idx >= 0 ? idx : 0);
    });
  });

  lightbox.querySelector('.lightbox-close').addEventListener('click', closeLightbox);
  lightbox.querySelector('.lightbox-prev').addEventListener('click', (e) => { e.stopPropagation(); navigate(-1); });
  lightbox.querySelector('.lightbox-next').addEventListener('click', (e) => { e.stopPropagation(); navigate(1); });
  lightbox.addEventListener('click', (e) => { if (e.target === lightbox) closeLightbox(); });

  document.addEventListener('keydown', (e) => {
    if (!lightbox.classList.contains('active')) return;
    if (e.key === 'Escape') closeLightbox();
    if (e.key === 'ArrowLeft') navigate(-1);
    if (e.key === 'ArrowRight') navigate(1);
  });

  // ===== SCROLL REVEAL =====
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add(entry.target.classList.contains('gallery-item') ? 'visible' : 'revealed');
      }
    });
  }, { threshold: 0.1, rootMargin: '0px 0px -40px 0px' });

  document.querySelectorAll('.reveal, .gallery-item').forEach((el, i) => {
    if (el.classList.contains('gallery-item')) {
      el.style.transitionDelay = (i * 0.08) + 's';
    }
    observer.observe(el);
  });

  // ===== ACTIVE NAV LINK =====
  const sections = document.querySelectorAll('section[id]');
  const navLinks = document.querySelectorAll('.nav-links a');

  window.addEventListener('scroll', () => {
    let current = '';
    sections.forEach(section => {
      const top = section.offsetTop - 200;
      if (window.scrollY >= top) current = section.getAttribute('id');
    });
    navLinks.forEach(link => {
      link.classList.toggle('active', link.getAttribute('href') === '#' + current);
    });
  });

  // ===== LANGUAGE TOGGLE =====
  const langToggle = document.getElementById('langToggle');
  let currentLang = localStorage.getItem('lang') || 'en';
  const enTextStore = new Map();
  const enHtmlStore = new Map();

  document.querySelectorAll('[data-zh]').forEach(el => {
    enTextStore.set(el, el.textContent);
  });
  document.querySelectorAll('[data-zh-html]').forEach(el => {
    enHtmlStore.set(el, el.innerHTML);
  });

  function setLanguage(lang) {
    currentLang = lang;
    localStorage.setItem('lang', lang);
    document.documentElement.lang = lang === 'zh' ? 'zh-CN' : 'en';
    document.title = lang === 'zh' ? '作品集 — 摄影' : 'Portfolio \u2014 Photography';
    langToggle.textContent = lang === 'zh' ? 'EN' : '\u4E2D\u6587';

    document.querySelectorAll('[data-zh]').forEach(el => {
      el.textContent = lang === 'zh' ? el.dataset.zh : enTextStore.get(el);
    });

    document.querySelectorAll('[data-zh-html]').forEach(el => {
      el.innerHTML = lang === 'zh' ? el.dataset.zhHtml : enHtmlStore.get(el);
    });

  }

  langToggle.addEventListener('click', () => {
    setLanguage(currentLang === 'en' ? 'zh' : 'en');
  });

  if (currentLang === 'zh') setLanguage('zh');
})();
