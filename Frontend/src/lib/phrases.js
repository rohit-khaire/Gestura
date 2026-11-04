// Phrase book: sign label -> text in each supported language.
// Pure data + pure functions (no browser APIs) so it can be unit-tested with `node --test`.
//
// PHRASES is the *vocabulary*: translations for every sign we have prepared, including signs the
// deployed model has not been trained on yet. ACTIVE_SIGNS is what the model can actually
// recognise right now; it must equal the classes in Model/src/config.json (a test enforces this,
// and `python src/utils/add_signs.py` updates both files together).
//
// To add a language: add it to LANGUAGES and give every sign a translation.

export const LANGUAGES = {
  en: { name: "English", speech: "en-US", recog: "en-US" },
  hi: { name: "हिन्दी (Hindi)", speech: "hi-IN", recog: "hi-IN" },
  mr: { name: "मराठी (Marathi)", speech: "mr-IN", recog: "mr-IN" },
  es: { name: "Español (Spanish)", speech: "es-ES", recog: "es-ES" },
};

export const PHRASES = {
  hello: { en: "Hello", hi: "नमस्ते", mr: "नमस्कार", es: "Hola" },
  iloveyou: {
    en: "I love you",
    hi: "मुझे तुमसे प्यार है",
    mr: "माझं तुझ्यावर प्रेम आहे",
    es: "Te quiero",
  },
  thankyou: { en: "Thank you", hi: "धन्यवाद", mr: "धन्यवाद", es: "Gracias" },

  // --- prepared for the next training round (see docs/ADD_SIGNS.md) ---
  stop: { en: "Stop", hi: "रुकिए", mr: "थांबा", es: "Alto" },
  yes: { en: "Yes", hi: "हाँ", mr: "होय", es: "Sí" },
  no: { en: "No", hi: "नहीं", mr: "नाही", es: "No" },
  good: { en: "Good", hi: "अच्छा", mr: "छान", es: "Bien" },
  ok: { en: "Okay", hi: "ठीक है", mr: "ठीक आहे", es: "De acuerdo" },
  water: { en: "I need water", hi: "मुझे पानी चाहिए", mr: "मला पाणी हवे आहे", es: "Necesito agua" },
  help: { en: "I need help", hi: "मुझे मदद चाहिए", mr: "मला मदत हवी आहे", es: "Necesito ayuda" },
  please: { en: "Please", hi: "कृपया", mr: "कृपया", es: "Por favor" },
  sorry: { en: "Sorry", hi: "माफ़ कीजिए", mr: "माफ करा", es: "Lo siento" },
};

/** Signs the deployed model recognises (keep in sync with Model/src/config.json). */
export const ACTIVE_SIGNS = ["hello", "iloveyou", "thankyou"];

/** Every sign that has translations. */
export const SIGN_LABELS = Object.keys(PHRASES);

const prettify = (label) => {
  const s = String(label).replace(/[_-]+/g, " ").trim();
  return s.charAt(0).toUpperCase() + s.slice(1);
};

/** Text for one sign in one language (falls back to English, then to the raw label). */
export function translateLabel(label, lang = "en") {
  const entry = PHRASES[label];
  if (!entry) return prettify(label);
  return entry[lang] ?? entry.en ?? prettify(label);
}

/** Turn a list of recognised sign labels into one natural-looking sentence. */
export function composeSentence(labels, lang = "en") {
  if (!labels?.length) return "";
  const latin = lang === "en" || lang === "es";
  const parts = labels.map((label, i) => {
    const text = translateLabel(label, lang);
    // "Hello, thank you." – lower-case later parts, but keep the pronoun "I".
    if (i > 0 && latin && !/^I\b/.test(text)) return text.charAt(0).toLowerCase() + text.slice(1);
    return text;
  });
  const joined = parts.join(", ");
  const first = joined.charAt(0).toUpperCase() + joined.slice(1);
  return first + (lang === "hi" ? "।" : ".");
}
