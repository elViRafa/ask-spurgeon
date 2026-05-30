# Multilingual Support Plan for Ask Spurgeon

**Goal**: Enable users to ask questions and receive answers in languages other than English, starting with Portuguese (pt-BR).

## Core Challenges

1. **Corpus is English-only**: All ~3,500 sermons are in 19th-century English.
2. **Embeddings are English-optimized**: `BAAI/bge-small-en-v1.5` performs best on English.
3. **Spurgeon's Voice is highly idiomatic**: Archaic, rhetorical, Victorian English style is difficult to preserve when translating.
4. **Theological Terminology**: Portuguese has its own established evangelical/Reformed vocabulary that must be respected.

## Recommended Architecture (Translation Pipeline)

We will use a **"Translate → Retrieve in English → Generate in English → Translate"** approach.

### Why this approach?

- Best retrieval quality (English embeddings + English corpus).
- Best fidelity to Spurgeon's actual words and style.
- Easier to control and improve over time.
- Much faster to implement than switching to multilingual embeddings.

### Flow for Non-English Queries

```
User Question (Portuguese)
        ↓
1. Translate Question → English          (using LLM)
        ↓
2. Semantic Retrieval (English corpus)   (current system)
        ↓
3. Generate Answer in English            (current Spurgeon prompt + context)
        ↓
4. Translate Answer → Portuguese         (specialized prompt)
        ↓
Final Answer to User (Portuguese)
```

### For English Users

Normal current flow (no translation overhead).

## Phased Implementation Plan

### Phase 1: Foundation (Portuguese MVP) — Recommended first step

- [ ] Add language selection in the UI (sidebar): English / Português
- [ ] Create `utils/translator.py` with two main functions:
  - `translate_to_english(text: str, source_lang: str) -> str`
  - `translate_to_language(english_text: str, target_lang: str) -> str`
- [ ] Use Groq (same provider) for translations (cost-effective and consistent).
- [ ] Modify the main generation flow in `app.py` to support the 4-step pipeline when language ≠ English.
- [ ] Create language-specific instructions for the final translation step (especially important for Portuguese theological language).
- [ ] Update example questions to include Portuguese versions.
- [ ] Add disclaimer that answers are translated.

**Prompt Strategy for Translation**:
- Use the strong model (`llama-3.3-70b-versatile`) for final answer translation.
- Give it a glossary of Spurgeon/ Reformed terms in Portuguese.

### Phase 2: Quality Improvements

- Build a small **Portuguese theological glossary** (e.g. "sovereign grace" → "graça soberana", "immutability" → "imutabilidade", "covenant of grace" → "pacto da graça", etc.).
- Improve the translation prompt with few-shot examples of good Spurgeon-style Portuguese.
- Add caching for translations (to save tokens and latency).
- Allow users to see the original English answer (toggle).

### Phase 3: Advanced (Optional)

- Experiment with multilingual embeddings (`BAAI/bge-m3` or `intfloat/multilingual-e5-large-instruct`).
- Re-index a copy of the collection in the new embedding space.
- A/B test retrieval quality between English-only vs multilingual embeddings for Portuguese queries.
- Add support for more languages (Spanish, French, German, etc.) using the same pipeline.

## Technical Recommendations

### Where to Hook Language Support

1. **UI Layer** (`app.py`):
   - Add language selector in sidebar.
   - Store selected language in `st.session_state["language"]`.

2. **Orchestration Layer** (new or in `app.py`):
   - Create a function `process_query(question, language)` that decides whether to go through the translation pipeline.

3. **Prompt Layer** (`utils/prompts.py`):
   - Keep the Spurgeon generation prompt in English (best results).
   - Create a separate `get_translation_prompt(target_lang)`.

4. **New Module**:
   - `utils/translator.py` (central place for all translation logic).

### Model Usage Strategy (Cost Control)

- **Query Translation** (PT → EN): Use cheaper/faster model (`llama-3.1-8b-instant`)
- **Answer Generation**: Current strong model (as today)
- **Final Translation** (EN → PT): Use strong model with good instructions

### Handling Spurgeon's Voice in Portuguese

This is the hardest part. Options:

**Option A (Recommended initially)**: Generate in English first → Translate with style instructions.
**Option B**: Instruct the LLM to "translate while preserving 19th-century preacher rhetorical style" using examples.
**Option C** (Long term): Curate a small set of high-quality Portuguese translations of famous Spurgeon passages as few-shot examples.

## Risks & Mitigations

| Risk                              | Mitigation                                      |
|-----------------------------------|-------------------------------------------------|
| Poor translation quality          | Use strong model + good glossary + examples    |
| Loss of Spurgeon's voice          | Always generate in English first               |
| Increased latency                 | Cache translations + use fast model for query  |
| Increased cost                    | Monitor usage; offer English as default        |
| Theological terminology errors    | Maintain a Portuguese glossary file            |

## Proposed File Structure Additions

```
utils/
├── translator.py           # New: translation logic
├── prompts.py              # Extend with translation prompts
└── language.py             # New: language codes, detection, constants

docs/
└── multilingual_support_plan.md   # This document
```

## Next Steps (Recommended Order)

1. Create `utils/language.py` with supported languages and constants.
2. Create `utils/translator.py` with basic translation functions using Groq.
3. Add language selector to the Streamlit sidebar.
4. Modify the chat response generation to route through translation when needed.
5. Test with real Portuguese questions (especially theological ones).
6. Iterate on the Portuguese translation prompt + glossary.

## Open Questions for Discussion

- Should we let the user choose between "Translate Spurgeon's voice" vs "Answer directly in Portuguese with modern language"?
- Do we want to support asking in Portuguese but receiving the answer in English (for language learners)?
- Should we eventually support fully Portuguese-generated answers (even if retrieval stays in English)?

---

**Status**: Planning phase complete. Ready to begin implementation starting with Portuguese.
