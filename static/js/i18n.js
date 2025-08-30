async function loadLocale(lang = 'en') {
  try {
    const res = await fetch(`static/locales/${lang}.json`);
    const translations = await res.json();

    document.querySelectorAll('[data-i18n]').forEach(el => {
      const key = el.getAttribute('data-i18n');
      if (translations[key]) {
        el.textContent = translations[key];
      }
    });

    currentLanguage = lang; // salva globalmente
  } catch (err) {
    console.error(`Error loading language file for "${lang}"`, err);
  }
}
