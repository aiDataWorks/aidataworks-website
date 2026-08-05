(function () {
  // ---- Nav shrinks back to its compact size once the page scrolls ----
  var nav = document.querySelector('.nav');
  function updateNavScrollState() {
    nav.classList.toggle('is-scrolled', window.scrollY > 20);
  }
  window.addEventListener('scroll', updateNavScrollState, { passive: true });
  updateNavScrollState();

  var hamburgerBtn = document.getElementById('hamburgerBtn');
  var mobilePanel = document.getElementById('mobilePanel');
  hamburgerBtn.addEventListener('click', function () {
    var isOpen = mobilePanel.classList.toggle('is-open');
    hamburgerBtn.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
    if (!isOpen) { closeAllMobileSubmenus(); }
  });

  // ---- Desktop nav dropdowns ----
  var navItems = document.querySelectorAll('[data-nav-item]');
  function closeAllNavDropdowns(except) {
    navItems.forEach(function (item) {
      if (item === except) return;
      item.classList.remove('is-open');
      item.querySelector('.nav-link').setAttribute('aria-expanded', 'false');
    });
  }
  navItems.forEach(function (item) {
    var trigger = item.querySelector('.nav-link');
    trigger.addEventListener('click', function () {
      var wasOpen = item.classList.contains('is-open');
      closeAllNavDropdowns(item);
      item.classList.toggle('is-open', !wasOpen);
      trigger.setAttribute('aria-expanded', !wasOpen ? 'true' : 'false');
    });
    item.querySelectorAll('.nav-dropdown-link, .nav-dropdown-foot').forEach(function (link) {
      link.addEventListener('click', function () { closeAllNavDropdowns(); });
    });
  });
  document.addEventListener('click', function (e) {
    if (!e.target.closest('[data-nav-item]')) { closeAllNavDropdowns(); }
  });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') { closeAllNavDropdowns(); }
  });

  // ---- Services mega-menu: category tabs ----
  document.querySelectorAll('[data-service-tablist]').forEach(function (tablist) {
    var tabs = tablist.querySelectorAll('.nav-dropdown-tab');
    var panels = tablist.closest('.nav-dropdown-row').querySelectorAll('.nav-dropdown-tabpanel');
    function activateServiceTab(index) {
      tabs.forEach(function (t, i) {
        t.classList.toggle('is-active', i === index);
        t.setAttribute('aria-selected', i === index ? 'true' : 'false');
      });
      panels.forEach(function (p, i) { p.classList.toggle('is-active', i === index); });
    }
    tabs.forEach(function (tab, i) {
      tab.addEventListener('mouseenter', function () { activateServiceTab(i); });
      tab.addEventListener('focus', function () { activateServiceTab(i); });
      tab.addEventListener('click', function () { activateServiceTab(i); });
    });
  });

  // ---- Mobile nav accordion ----
  var navMobileItems = document.querySelectorAll('[data-nav-mobile-item]');
  function closeAllMobileSubmenus(except) {
    navMobileItems.forEach(function (item) {
      if (item === except) return;
      item.classList.remove('is-open');
      item.querySelector('.nav-mobile-link').setAttribute('aria-expanded', 'false');
      item.querySelector('.nav-mobile-submenu').style.maxHeight = '';
    });
  }
  navMobileItems.forEach(function (item) {
    var trigger = item.querySelector('.nav-mobile-link');
    var submenu = item.querySelector('.nav-mobile-submenu');
    trigger.addEventListener('click', function () {
      var wasOpen = item.classList.contains('is-open');
      closeAllMobileSubmenus(item);
      item.classList.toggle('is-open', !wasOpen);
      trigger.setAttribute('aria-expanded', !wasOpen ? 'true' : 'false');
      submenu.style.maxHeight = !wasOpen ? submenu.scrollHeight + 'px' : '';
    });
    submenu.querySelectorAll('a').forEach(function (link) {
      link.addEventListener('click', function () {
        mobilePanel.classList.remove('is-open');
        hamburgerBtn.setAttribute('aria-expanded', 'false');
        closeAllMobileSubmenus();
      });
    });
  });

  // ---- Word-by-word heading reveal on scroll (any .text-reveal element) ----
  function prepareTextReveal(el) {
    var words = el.textContent.split(' ');
    el.textContent = '';
    words.forEach(function (word, i) {
      var span = document.createElement('span');
      span.className = 'text-reveal-word';
      span.textContent = word;
      el.appendChild(span);
      if (i < words.length - 1) { el.appendChild(document.createTextNode(' ')); }
    });
  }
  function triggerTextReveal(el) {
    var words = el.querySelectorAll('.text-reveal-word');
    words.forEach(function (word, i) {
      setTimeout(function () { word.classList.add('is-visible'); }, i * 100);
    });
  }
  var textRevealHeadings = document.querySelectorAll('.text-reveal');
  textRevealHeadings.forEach(function (heading) { prepareTextReveal(heading); });
  var textRevealObserver = new IntersectionObserver(function (entries) {
    entries.forEach(function (entry) {
      if (entry.isIntersecting) {
        triggerTextReveal(entry.target);
        textRevealObserver.unobserve(entry.target);
      }
    });
  }, { threshold: 0.4 });
  textRevealHeadings.forEach(function (heading) { textRevealObserver.observe(heading); });
})();
