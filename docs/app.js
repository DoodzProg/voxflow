// docs/app.js
/**
 * app.js
 * Voxflow landing page — behaviour, micro-interactions, and i18n.
 *
 * Responsibilities:
 *  - EN / FR translation system with localStorage persistence
 *  - Language toggle button handler
 *  - Scroll-aware navbar background opacity
 *  - Smooth reveal animation for cards and sections (IntersectionObserver)
 *  - Download tracking
 */

'use strict';

// ── Translation table ─────────────────────────────────────────────
const TRANSLATIONS = {
  en: {
    'nav.features':        'Features',
    'nav.how':             'How it works',
    'nav.github':          'GitHub',
    'nav.download':        'Download',

    'hero.badge':          'v1.0.1 \u2014 Free &amp; Open Source',
    'hero.h1a':            'Speak.',
    'hero.h1b':            "Don't type.",
    'hero.sub':            'Hold a hotkey, speak, release \u2014 your words appear instantly in any application. Powered by Groq Whisper. No subscription, no cloud account.',
    'hero.cta.download':   'Download for free',
    'hero.cta.github':     'View on GitHub',
    'hero.note':           'Windows 10 / 11 \u00b7 Free Groq API key required',

    'demo.title':          'Voxflow 1.0.1',
    'example.eyebrow':     'In action',
    'example.title':       'Hold. Speak. Done.',
    'example.titlebar':    'Live dictation',

    'stats.latency.value': '&lt;&nbsp;1s',
    'stats.latency.label': 'Transcription latency',
    'stats.local.value':   '100%',
    'stats.local.label':   'Local \u2014 no data stored',
    'stats.free.value':    'Free',
    'stats.free.label':    'Groq free tier included',

    'feat.eyebrow':        'Features',
    'feat.title':          "Everything you need.<br>Nothing you don't.",
    'feat.sub':            'A focused tool that does one thing exceptionally well.',
    'feat.hotkey.title':   'Hotkey-driven dictation',
    'feat.hotkey.body':    'Hold <span class="chip">Right Ctrl + Right Shift</span> and speak. Release to transcribe. Works in any application \u2014 browser, editor, chat, email. Fully customisable hotkeys with Push-to-Talk or Toggle mode.',
    'feat.stt.title':      'Groq Whisper STT',
    'feat.stt.body':       'State-of-the-art speech recognition. Fast, accurate, multi-language. Supports English, French, Spanish, German and Italian.',
    'feat.llm.title':      'LLM post-processing',
    'feat.llm.body':       'Llama-3 fixes punctuation, removes filler words, formats bullet lists and converts spoken emoji descriptions \u2014 automatically.',
    'feat.bilingual.title':'Bilingual interface',
    'feat.bilingual.body': 'Full English / French UI switchable live without restart. Dictation language is independent \u2014 transcribe in any supported language.',
    'feat.context.title':  'Context instructions',
    'feat.context.body':   'Select text, hold <span class="chip">Right Alt + Right Shift</span>, speak an instruction. Llama-3 rewrites or replies using your selection as context.',
    'feat.tray.title':     'System tray &amp; startup',
    'feat.tray.body':      'Runs silently in the background. Minimises to tray. Optionally launches at Windows startup \u2014 one toggle in Settings.',

    'how.eyebrow':         'How it works',
    'how.title':           'Three keystrokes.<br>Your words, anywhere.',
    'how.step1.title':     'Place your cursor',
    'how.step1.body':      'Click in any text field \u2014 browser, Notepad, Slack, Word, VS Code. Anywhere that accepts keyboard input.',
    'how.step2.title':     'Hold &amp; speak',
    'how.step2.body':      "Hold your hotkey and speak naturally. A floating overlay shows you're recording with a live VU meter.",
    'how.step3.title':     'Release &amp; done',
    'how.step3.body':      'Release the key. Groq transcribes, Llama-3 cleans, and the text is pasted \u2014 all in under a second.',

    'screenshots.eyebrow': 'Screenshots',
    'screenshots.title':   'See it in action.',
    'screenshots.cap1':    'Dashboard \u2014 stats &amp; shortcuts',
    'screenshots.cap2':    'Settings \u2014 hotkeys &amp; language',
    'screenshots.cap3':    'Audio \u2014 microphone &amp; VU meter',
    'screenshots.cap4':    'Overlay \u2014 floating recording bubble',

    'oss.eyebrow':         'Open Source',
    'oss.title':           'Built in the open.<br>Free forever.',
    'oss.body':            'No subscription, no telemetry, no accounts. Your API key stays on your machine. Audit every line of code.',
    'oss.star':            'Star on GitHub',
    'oss.bug':             'Report a bug',
    'oss.contribute':      'Contribute',

    'dl.title':            'Ready to stop typing?',
    'dl.body':             'Free download. No account. No subscription. Just your voice.',
    'dl.btn':              'Download Voxflow for Windows',
    'dl.badge':            'Windows 10 / 11 (x64) \u00b7 v1.0.1',

    'footer.releases':     'Releases',
    'footer.license':      'MIT License',
    'footer.support':      'Support',
    'footer.copy':         '\u00a9 2026 DoodzProg \u00b7 MIT License',
  },

  fr: {
    'nav.features':        'Fonctionnalit\u00e9s',
    'nav.how':             'Comment \u00e7a marche',
    'nav.github':          'GitHub',
    'nav.download':        'T\u00e9l\u00e9charger',

    'hero.badge':          'v1.0.1 \u2014 Gratuit &amp; Open Source',
    'hero.h1a':            'Parle.',
    'hero.h1b':            "Arr\u00eate d'\u00e9crire.",
    'hero.sub':            'Maintiens un raccourci, parle, rel\u00e2che \u2014 tes mots apparaissent instantan\u00e9ment dans n\u2019importe quelle application. Propuls\u00e9 par Groq Whisper. Sans abonnement, sans compte cloud.',
    'hero.cta.download':   'T\u00e9l\u00e9charger gratuitement',
    'hero.cta.github':     'Voir sur GitHub',
    'hero.note':           'Windows 10 / 11 \u00b7 Cl\u00e9 API Groq gratuite requise',

    'demo.title':          'Voxflow 1.0.1',
    'example.eyebrow':     'En action',
    'example.title':       'Maintiens. Parle. C\u2019est fait.',
    'example.titlebar':    'Dict\u00e9e en direct',

    'stats.latency.value': '&lt;&nbsp;1s',
    'stats.latency.label': 'Latence de transcription',
    'stats.local.value':   '100%',
    'stats.local.label':   'Local \u2014 aucune donn\u00e9e stock\u00e9e',
    'stats.free.value':    'Gratuit',
    'stats.free.label':    'Tier gratuit Groq inclus',

    'feat.eyebrow':        'Fonctionnalit\u00e9s',
    'feat.title':          'Tout ce qu\u2019il te faut.<br>Rien de superflu.',
    'feat.sub':            'Un outil focalis\u00e9 qui fait une chose exceptionnellement bien.',
    'feat.hotkey.title':   'Dict\u00e9e par raccourci',
    'feat.hotkey.body':    'Maintiens <span class="chip">Right Ctrl + Right Shift</span> et parle. Rel\u00e2che pour transcrire. Fonctionne partout \u2014 navigateur, \u00e9diteur, chat, email. Raccourcis enti\u00e8rement personnalisables.',
    'feat.stt.title':      'Groq Whisper STT',
    'feat.stt.body':       'Reconnaissance vocale de pointe. Rapide, pr\u00e9cise, multilingue. Supporte l\u2019anglais, le fran\u00e7ais, l\u2019espagnol, l\u2019allemand et l\u2019italien.',
    'feat.llm.title':      'Post-traitement LLM',
    'feat.llm.body':       'Llama-3 corrige la ponctuation, supprime les mots de remplissage, formate les listes \u2014 automatiquement.',
    'feat.bilingual.title':'Interface bilingue',
    'feat.bilingual.body': 'Interface EN / FR basculable en direct sans red\u00e9marrage. La langue de dict\u00e9e est ind\u00e9pendante.',
    'feat.context.title':  'Instructions contextuelles',
    'feat.context.body':   'S\u00e9lectionne du texte, maintiens <span class="chip">Right Alt + Right Shift</span>, parle. Llama-3 r\u00e9\u00e9crit ou r\u00e9pond en utilisant ta s\u00e9lection.',
    'feat.tray.title':     'Barre syst\u00e8me &amp; d\u00e9marrage',
    'feat.tray.body':      'Tourne silencieusement en arri\u00e8re-plan. Se r\u00e9duit dans la barre syst\u00e8me. Lancement optionnel au d\u00e9marrage Windows.',

    'how.eyebrow':         'Comment \u00e7a marche',
    'how.title':           'Trois touches.<br>Tes mots, partout.',
    'how.step1.title':     'Place ton curseur',
    'how.step1.body':      'Clique dans n\u2019importe quel champ de texte \u2014 navigateur, Notepad, Slack, Word, VS Code.',
    'how.step2.title':     'Maintiens &amp; parle',
    'how.step2.body':      'Maintiens ton raccourci et parle naturellement. Une bulle flottante confirme l\u2019enregistrement.',
    'how.step3.title':     'Rel\u00e2che &amp; c\u2019est fait',
    'how.step3.body':      'Rel\u00e2che la touche. Groq transcrit, Llama-3 nettoie, le texte se colle \u2014 en moins d\u2019une seconde.',

    'screenshots.eyebrow': 'Captures d\u2019\u00e9cran',
    'screenshots.title':   'Vois par toi-m\u00eame.',
    'screenshots.cap1':    'Tableau de bord \u2014 stats &amp; raccourcis',
    'screenshots.cap2':    'Param\u00e8tres \u2014 raccourcis &amp; langue',
    'screenshots.cap3':    'Audio \u2014 microphone &amp; VU-m\u00e8tre',
    'screenshots.cap4':    'Overlay \u2014 bulle d\u2019enregistrement flottante',

    'oss.eyebrow':         'Open Source',
    'oss.title':           'Construit ouvertement.<br>Gratuit pour toujours.',
    'oss.body':            'Pas d\u2019abonnement, pas de t\u00e9l\u00e9m\u00e9trie, pas de compte. Ta cl\u00e9 API reste sur ta machine. Audite chaque ligne de code.',
    'oss.star':            'Star sur GitHub',
    'oss.bug':             'Signaler un bug',
    'oss.contribute':      'Contribuer',

    'dl.title':            "Pr\u00eat \u00e0 arr\u00eater d'\u00e9crire\u00a0?",
    'dl.body':             'T\u00e9l\u00e9chargement gratuit. Sans compte. Sans abonnement. Juste ta voix.',
    'dl.btn':              'T\u00e9l\u00e9charger Voxflow pour Windows',
    'dl.badge':            'Windows 10 / 11 (x64) \u00b7 v1.0.1',

    'footer.releases':     'Versions',
    'footer.license':      'Licence MIT',
    'footer.support':      'Support',
    'footer.copy':         '\u00a9 2026 DoodzProg \u00b7 Licence MIT',
  },
};

// ── i18n core ─────────────────────────────────────────────────────
const LANG_STORAGE_KEY = 'voxflow_lang';

/**
 * Apply a language to all [data-i18n] elements on the page.
 * If the translation string contains HTML tags it uses innerHTML,
 * otherwise textContent (safer for plain strings).
 *
 * @param {string} lang  'en' | 'fr'
 */
function applyLang(lang) {
  const strings = TRANSLATIONS[lang];
  if (!strings) return;

  document.querySelectorAll('[data-i18n]').forEach((el) => {
    const key = el.getAttribute('data-i18n');
    const value = strings[key];
    if (value === undefined) return;

    // Use innerHTML when the string contains markup, textContent otherwise
    if (value.includes('<') || value.includes('&')) {
      el.innerHTML = value;
    } else {
      el.textContent = value;
    }
  });

  // Update <html lang="…"> for accessibility / SEO
  document.documentElement.lang = lang;
}

// ── Language toggle ───────────────────────────────────────────────
(function initLang() {
  const btn      = document.getElementById('lang-toggle');
  const flagEl   = document.getElementById('lang-flag');
  const codeEl   = document.getElementById('lang-code');

  const FLAGS = { en: '🇬🇧', fr: '🇫🇷' };
  const CODES = { en: 'EN',  fr: 'FR'  };

  function setLangUI(lang) {
    if (flagEl) flagEl.textContent = FLAGS[lang] || FLAGS.en;
    if (codeEl) codeEl.textContent = CODES[lang] || CODES.en;
  }

  // Read saved language (default 'en')
  let currentLang = localStorage.getItem(LANG_STORAGE_KEY) || 'en';
  if (!TRANSLATIONS[currentLang]) currentLang = 'en';

  setLangUI(currentLang);
  applyLang(currentLang);

  if (!btn) return;

  btn.addEventListener('click', () => {
    currentLang = currentLang === 'en' ? 'fr' : 'en';
    localStorage.setItem(LANG_STORAGE_KEY, currentLang);
    setLangUI(currentLang);
    applyLang(currentLang);
  });
})();


// ── Navbar scroll effect ──────────────────────────────────────────
(function initNavScroll() {
  const nav = document.querySelector('nav');
  if (!nav) return;

  const onScroll = () => {
    const scrolled = window.scrollY > 20;
    nav.style.borderBottomColor = scrolled
      ? 'rgba(42, 38, 64, 1)'
      : 'rgba(42, 38, 64, 0.6)';
  };

  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();
})();


// ── Scroll-reveal animation ───────────────────────────────────────
(function initReveal() {
  const TARGETS = [
    '.feat-card',
    '.step',
    '.stat-item',
    '.demo-window',
    '.oss-card',
    '.download-card',
    '.section-header',
    '.screenshot-grid',
    '.screenshot-item',
  ];

  // Inject the base reveal style once
  const style = document.createElement('style');
  style.textContent = `
    .reveal {
      opacity: 0;
      transform: translateY(20px);
      transition: opacity 0.55s cubic-bezier(.4,0,.2,1),
                  transform 0.55s cubic-bezier(.4,0,.2,1);
    }
    .reveal.visible {
      opacity: 1;
      transform: none;
    }
  `;
  document.head.appendChild(style);

  // Mark all target elements (skip those already marked in HTML)
  document.querySelectorAll(TARGETS.join(',')).forEach((el, i) => {
    el.classList.add('reveal');
    el.style.transitionDelay = `${(i % 4) * 60}ms`;
  });

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible');
          observer.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.12 }
  );

  document.querySelectorAll('.reveal').forEach((el) => observer.observe(el));
})();


// ── Download button — track clicks ───────────────────────────────
(function initDownloadTracking() {
  const buttons = document.querySelectorAll('a[href*="VoxflowSetup.exe"]');
  buttons.forEach((btn) => {
    btn.addEventListener('click', () => {
      console.info('[Voxflow] Download initiated');
    });
  });
})();
