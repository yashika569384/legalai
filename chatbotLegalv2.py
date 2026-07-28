# import json
# import os
# import re
# from dotenv import load_dotenv

# from groq import Groq                                # pip install groq
# from langchain_community.vectorstores import FAISS
# from langchain_huggingface import HuggingFaceEmbeddings
# from langchain_core.documents import Document
# from transformers import AutoTokenizer, AutoModel

# load_dotenv()

# # ── LOCAL JSON STORAGE ─────────────────────────────────────────────────────────
# CHATS_FILE = os.path.join(os.path.dirname(__file__), "..", "chats.json")

# def _load_all_chats() -> dict:
#     if os.path.exists(CHATS_FILE):
#         with open(CHATS_FILE, "r", encoding="utf-8") as f:
#             try:
#                 return json.load(f)
#             except json.JSONDecodeError:
#                 return {}
#     return {}

# def _save_all_chats(data: dict) -> None:
#     with open(CHATS_FILE, "w", encoding="utf-8") as f:
#         json.dump(data, f, ensure_ascii=False, indent=2)


# # ── GROQ INIT ──────────────────────────────────────────────────────────────────
# groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
# GROQ_MODEL  = "llama-3.3-70b-versatile"   # best quality on Groq for legal queries

# SYSTEM_PROMPT = """You are an AI Legal Assistant specialized in Indian law.
# Provide accurate, clear, concise explanations grounded in the Indian Penal Code (IPC) and related doctrines.
# This is an educational legal summary, not legal advice.
# Use neutral, academic phrasing. Avoid sensational or graphic language.
# If a specific section is not available in the context, give a general explanation without inventing statutory wording."""


# # ── LAZY GLOBALS ───────────────────────────────────────────────────────────────
# MODEL_NAME      = "law-ai/InLegalBERT"
# model_cache_dir = os.path.join(os.path.expanduser("~"), ".cache", "huggingface", "hub")

# _embedding_model = None
# _vectorstore     = None


# def get_embedding_model():
#     global _embedding_model
#     if _embedding_model is None:
#         try:
#             AutoTokenizer.from_pretrained(MODEL_NAME, cache_dir=model_cache_dir)
#             AutoModel.from_pretrained(MODEL_NAME, cache_dir=model_cache_dir)
#             print("✅ InLegalBERT ready.")
#         except Exception as e:
#             print(f"⚠️ InLegalBERT load warning: {e}")
#         _embedding_model = HuggingFaceEmbeddings(model_name=MODEL_NAME)
#     return _embedding_model


# def build_faiss_index():
#     print("⚠️ Rebuilding FAISS index...")
#     with open("laws_raw.json", "r", encoding="utf-8") as f:
#         ipc_data = json.load(f)

#     docs = []
#     for section, details in ipc_data["IPC"].items():
#         title   = details.get("title", "")
#         content = details.get("content", "")
#         text    = f"{section}: {title}\n{content}"
#         docs.append(Document(page_content=text, metadata={"section": section, "title": title}))

#     vs = FAISS.from_documents(docs, get_embedding_model())
#     vs.save_local("ipc_embed_db_inlegalbert")
#     print("✅ FAISS index rebuilt.")
#     return vs


# def get_vectorstore():
#     global _vectorstore
#     if _vectorstore is None:
#         try:
#             _vectorstore = FAISS.load_local(
#                 "ipc_embed_db_inlegalbert",
#                 get_embedding_model(),
#                 allow_dangerous_deserialization=True
#             )
#             _ = _vectorstore.similarity_search("test", k=1)
#             print("✅ FAISS index loaded.")
#         except Exception as e:
#             print(f"❌ FAISS load failed: {e}. Rebuilding...")
#             _vectorstore = build_faiss_index()
#     return _vectorstore


# # ── HYBRID RETRIEVAL ───────────────────────────────────────────────────────────

# def hybrid_retrieve(query: str, k: int = 5, score_threshold: float = 1.2):
#     """
#     Retrieve relevant IPC context using JSON lookup + FAISS semantic search.
#     FAISS L2 distance — lower = more similar.
#     """
#     context_parts = []
#     source        = "GEN"

#     # 1️⃣ Exact JSON lookup for explicit section references
#     section_match = re.search(r'\bsection\s*(\d+[a-zA-Z]*)\b', query, re.IGNORECASE)
#     if section_match:
#         section_number = section_match.group(1)
#         try:
#             with open("laws_raw.json", "r", encoding="utf-8") as f:
#                 ipc_data = json.load(f)
#             if section_number in ipc_data["IPC"]:
#                 details      = ipc_data["IPC"][section_number]
#                 section_text = f"Section {section_number}: {details.get('title', '')}\n{details.get('content', '')}"
#                 context_parts.append(section_text)
#                 source = "JSON"
#                 print(f"✅ JSON hit: Section {section_number}")
#         except Exception as e:
#             print(f"⚠️ JSON lookup failed: {e}")

#     # 2️⃣ FAISS semantic search — always runs
#     try:
#         vectorstore = get_vectorstore()
#         results     = vectorstore.similarity_search_with_score(query, k=k)

#         if results:
#             top_doc, top_score = results[0]
#             print(f"📊 FAISS top score: {top_score:.4f} (lower = better)")

#             if top_score <= score_threshold:
#                 for doc, score in results:
#                     snippet = f"Section {doc.metadata.get('section', '')} — {doc.metadata.get('title', '')}\n{doc.page_content}"
#                     if snippet not in context_parts:
#                         context_parts.append(snippet)
#                 source = "RAG" if source == "GEN" else "HYBRID"
#             else:
#                 print(f"⚠️ FAISS score {top_score:.4f} above threshold — skipping.")
#     except Exception as e:
#         print(f"⚠️ FAISS search failed: {e}")

#     context = "\n\n".join(context_parts)
#     return context.strip(), source


# # ── CHAT STORAGE HELPERS ───────────────────────────────────────────────────────

# def load_chat(chat_name: str) -> dict:
#     all_chats = _load_all_chats()
#     return all_chats.get(chat_name, {"generated": [], "past": [], "source": []})

# def save_chat(chat_name: str, chat_data: dict) -> None:
#     all_chats            = _load_all_chats()
#     all_chats[chat_name] = chat_data
#     _save_all_chats(all_chats)

# def create_new_chat() -> str:
#     all_chats     = _load_all_chats()
#     new_chat_name = f"Chat {len(all_chats) + 1}"
#     all_chats[new_chat_name] = {"generated": [], "past": [], "source": []}
#     _save_all_chats(all_chats)
#     return new_chat_name

# def get_chat_list() -> list:
#     return list(_load_all_chats().keys())

# def delete_chat(chat_name: str) -> None:
#     all_chats = _load_all_chats()
#     if chat_name in all_chats:
#         del all_chats[chat_name]
#         _save_all_chats(all_chats)


# # ── GROQ GENERATION ────────────────────────────────────────────────────────────

# def groq_generate(prompt: str, temperature: float = 0.2) -> str:
#     """
#     Call Groq API with the system prompt and user prompt.
#     Returns response text or empty string on failure.
#     No safety blocking issues — Groq handles legal content fine.
#     """
#     try:
#         response = groq_client.chat.completions.create(
#             model=GROQ_MODEL,
#             messages=[
#                 {"role": "system", "content": SYSTEM_PROMPT},
#                 {"role": "user",   "content": prompt}
#             ],
#             temperature=temperature,
#             max_tokens=800,
#             top_p=0.9,
#         )
#         return response.choices[0].message.content.strip()

#     except Exception as e:
#         print(f"❌ Groq API error: {e}")
#         return ""


# def generate_response(prompt: str) -> str:
#     """
#     Generate response with automatic retry on empty/failure.
#     """
#     response = groq_generate(prompt, temperature=0.2)
#     if response:
#         return response

#     # Retry once with lower temperature
#     print("⚠️ Retrying Groq with lower temperature...")
#     response = groq_generate(prompt, temperature=0.1)
#     return response or "Unable to generate a response at this time. Please try again."


# # ── MAIN PIPELINE ──────────────────────────────────────────────────────────────

# def process_input(chat_name: str, user_input: str, return_source: bool = False):
#     """
#     Main chatbot pipeline:
#       1. Load chat history
#       2. Hybrid retrieval (JSON + FAISS)
#       3. Build prompt with context + history
#       4. Generate response via Groq
#       5. Save and return

#     Args:
#         chat_name     : active chat session name
#         user_input    : user's question
#         return_source : if True returns (response, source_type)

#     Returns:
#         response string, or (response, source_type) tuple
#     """
#     if not user_input or not user_input.strip():
#         return ("Please enter a valid question.", "GEN") if return_source else "Please enter a valid question."

#     current_chat  = load_chat(chat_name)
#     history_pairs = list(zip(current_chat.get("past", []), current_chat.get("generated", [])))

#     # Last 4 exchanges for context window efficiency
#     history_prompt = "\n".join(
#         [f"User: {q}\nAssistant: {a}" for q, a in history_pairs[-4:]]
#     )

#     # Hybrid retrieval
#     context_text, source_type = hybrid_retrieve(user_input, k=5)

#     # Build context block
#     if context_text and len(context_text.strip()) > 30 and source_type != "GEN":
#         context_block = (
#             f"Relevant IPC context retrieved from database:\n\n"
#             f"{context_text}\n\n"
#             f"Use the above context to answer the user's question accurately."
#         )
#     else:
#         source_type   = "GEN"
#         context_block = (
#             "No specific IPC section was retrieved for this query. "
#             "Provide a general, educational summary based on Indian law."
#         )

#     # Build final prompt
#     full_prompt = f"""{context_block}

# {'Conversation History:' + chr(10) + history_prompt if history_prompt else ''}

# User: {user_input}
# Assistant:"""

#     response = generate_response(full_prompt)

#     # Save to chat history
#     current_chat["past"].append(user_input)
#     current_chat["generated"].append(response)
#     current_chat["source"].append(source_type)
#     save_chat(chat_name, current_chat)

#     print(f"⚡ Source: {source_type} | Q: {user_input[:60]}...")
#     return (response, source_type) if return_source else response
# import json
# import os
# import re
# from dotenv import load_dotenv

# from groq import Groq
# from langchain_community.vectorstores import FAISS
# from langchain_huggingface import HuggingFaceEmbeddings
# from langchain_core.documents import Document
# from transformers import AutoTokenizer, AutoModel

# load_dotenv()

# # ── CONFIG ─────────────────────────────────────────────────────────────────────

# CHATS_FILE = os.path.join(os.path.dirname(__file__), "..", "chats.json")
# LAWS_DIR   = os.path.join(os.path.dirname(__file__), "..", "laws_json")
# FAISS_PATH = "laws_embed_db"

# # Map filename → law abbreviation
# LAW_FILES = {
#     "ipc.json":  "IPC",
#     "crpc.json": "CrPC",
#     "cpc.json":  "CPC",
#     "iea.json":  "IEA",
#     "mva.json":  "MVA",
#     "nia.json":  "NIA",
# }

# # Keywords to detect which law a query is about
# LAW_KEYWORDS = {
#     "IPC":  ["ipc", "indian penal code", "murder", "theft", "assault", "rape",
#              "cheating", "fraud", "robbery", "kidnapping", "hurt", "criminal"],
#     "CrPC": ["crpc", "criminal procedure", "arrest", "bail", "fir", "cognizable",
#              "magistrate", "trial", "warrant", "summons", "investigation"],
#     "CPC":  ["cpc", "civil procedure", "civil court", "decree", "suit", "plaint",
#              "execution", "injunction", "appeal", "civil"],
#     "IEA":  ["iea", "evidence act", "evidence", "admissible", "witness",
#              "confession", "burden of proof", "presumption"],
#     "MVA":  ["mva", "motor vehicle", "traffic", "driving licence", "accident",
#              "vehicle", "road", "insurance", "permit"],
#     "NIA":  ["nia", "negotiable instrument", "cheque", "bounce", "dishonour",
#              "promissory note", "bill of exchange", "section 138"],
# }

# GROQ_MODEL = "llama-3.3-70b-versatile"

# SYSTEM_PROMPT = """You are an AI Legal Assistant specialized in Indian law.
# You will be given relevant legal sections retrieved from a database.
# Your job is to explain them clearly and accurately based ONLY on the provided context.
# If the context is insufficient, say so honestly — do not invent legal provisions.
# This is educational information, not legal advice.
# Use neutral, academic language."""


# # ── LOCAL CHAT STORAGE ─────────────────────────────────────────────────────────

# def _load_all_chats() -> dict:
#     if os.path.exists(CHATS_FILE):
#         with open(CHATS_FILE, "r", encoding="utf-8") as f:
#             try:
#                 return json.load(f)
#             except json.JSONDecodeError:
#                 return {}
#     return {}

# def _save_all_chats(data: dict) -> None:
#     with open(CHATS_FILE, "w", encoding="utf-8") as f:
#         json.dump(data, f, ensure_ascii=False, indent=2)

# def load_chat(chat_name: str) -> dict:
#     return _load_all_chats().get(chat_name, {"generated": [], "past": [], "source": []})

# def save_chat(chat_name: str, chat_data: dict) -> None:
#     all_chats = _load_all_chats()
#     all_chats[chat_name] = chat_data
#     _save_all_chats(all_chats)

# def create_new_chat() -> str:
#     all_chats = _load_all_chats()
#     new_chat_name = f"Chat {len(all_chats) + 1}"
#     all_chats[new_chat_name] = {"generated": [], "past": [], "source": []}
#     _save_all_chats(all_chats)
#     return new_chat_name

# def get_chat_list() -> list:
#     return list(_load_all_chats().keys())

# def delete_chat(chat_name: str) -> None:
#     all_chats = _load_all_chats()
#     if chat_name in all_chats:
#         del all_chats[chat_name]
#         _save_all_chats(all_chats)


# # ── NORMALIZER ─────────────────────────────────────────────────────────────────

# def normalize_entry(entry: dict, law: str) -> dict | None:
#     """
#     Normalize all law JSON formats into one standard structure:
#     { "law": str, "section": str, "title": str, "content": str }

#     Handles all 3 formats:
#     - IPC:            { "Section"(capital S), "section_title", "section_desc" }
#     - CrPC/IEA/NIA:   { "section", "section_title", "section_desc" }
#     - CPC/MVA:        { "section", "title", "description" }
#     """
#     try:
#         # Section number — IPC uses capital "Section"
#         section = str(
#             entry.get("Section") or
#             entry.get("section") or ""
#         ).strip()

#         if not section:
#             return None

#         # Title
#         title = str(
#             entry.get("section_title") or
#             entry.get("title") or ""
#         ).strip()

#         # Content
#         content = str(
#             entry.get("section_desc") or
#             entry.get("description") or
#             entry.get("content") or ""
#         ).strip()

#         if not content:
#             return None

#         return {
#             "law":     law,
#             "section": section,
#             "title":   title,
#             "content": content,
#         }
#     except Exception as e:
#         print(f"⚠️ Normalize error [{law}]: {e}")
#         return None


# def load_all_laws() -> list[dict]:
#     """Load and normalize all law JSON files into a unified list."""
#     all_entries = []

#     for filename, law_name in LAW_FILES.items():
#         filepath = os.path.join(LAWS_DIR, filename)

#         if not os.path.exists(filepath):
#             print(f"⚠️ File not found: {filepath}")
#             continue

#         with open(filepath, "r", encoding="utf-8") as f:
#             try:
#                 data = json.load(f)
#             except json.JSONDecodeError as e:
#                 print(f"❌ JSON parse error in {filename}: {e}")
#                 continue

#         if not isinstance(data, list):
#             print(f"⚠️ Unexpected format in {filename} — expected a list")
#             continue

#         count = 0
#         for entry in data:
#             normalized = normalize_entry(entry, law_name)
#             if normalized:
#                 all_entries.append(normalized)
#                 count += 1

#         print(f"✅ Loaded {count} sections from {filename} ({law_name})")

#     print(f"📚 Total sections loaded across all laws: {len(all_entries)}")
#     return all_entries


# # ── EMBEDDING & FAISS ──────────────────────────────────────────────────────────

# MODEL_NAME      = "law-ai/InLegalBERT"
# model_cache_dir = os.path.join(os.path.expanduser("~"), ".cache", "huggingface", "hub")

# _embedding_model = None
# _vectorstore     = None
# _law_data        = None   # In-memory dict for fast JSON lookup


# def get_embedding_model() -> HuggingFaceEmbeddings:
#     global _embedding_model
#     if _embedding_model is None:
#         try:
#             AutoTokenizer.from_pretrained(MODEL_NAME, cache_dir=model_cache_dir)
#             AutoModel.from_pretrained(MODEL_NAME, cache_dir=model_cache_dir)
#             print("✅ InLegalBERT ready.")
#         except Exception as e:
#             print(f"⚠️ InLegalBERT load warning: {e}")
#         _embedding_model = HuggingFaceEmbeddings(model_name=MODEL_NAME)
#     return _embedding_model


# def get_law_data() -> dict:
#     """
#     Build in-memory lookup index from all law files:
#     { "IPC": { "302": { law, section, title, content }, ... }, "CrPC": { ... }, ... }
#     """
#     global _law_data
#     if _law_data is None:
#         _law_data = {}
#         for entry in load_all_laws():
#             law     = entry["law"]
#             section = entry["section"]
#             if law not in _law_data:
#                 _law_data[law] = {}
#             _law_data[law][section] = entry
#     return _law_data


# def build_faiss_index() -> FAISS:
#     """Build combined FAISS index from all law files."""
#     print("🔨 Building FAISS index from all law files...")
#     all_entries = load_all_laws()

#     docs = []
#     for entry in all_entries:
#         text = (
#             f"[{entry['law']}] Section {entry['section']}: "
#             f"{entry['title']}\n{entry['content']}"
#         )
#         docs.append(Document(
#             page_content=text,
#             metadata={
#                 "law":     entry["law"],
#                 "section": entry["section"],
#                 "title":   entry["title"],
#             }
#         ))

#     vs = FAISS.from_documents(docs, get_embedding_model())
#     vs.save_local(FAISS_PATH)
#     print(f"✅ FAISS index built with {len(docs)} total documents.")
#     return vs


# def get_vectorstore() -> FAISS:
#     global _vectorstore
#     if _vectorstore is None:
#         try:
#             _vectorstore = FAISS.load_local(
#                 FAISS_PATH,
#                 get_embedding_model(),
#                 allow_dangerous_deserialization=True
#             )
#             _ = _vectorstore.similarity_search("test", k=1)
#             print("✅ FAISS index loaded from disk.")
#         except Exception as e:
#             print(f"❌ FAISS load failed: {e}. Rebuilding...")
#             _vectorstore = build_faiss_index()
#     return _vectorstore


# # ── LAW DETECTION ──────────────────────────────────────────────────────────────

# def detect_laws(query: str) -> list[str]:
#     """
#     Detect which laws are relevant to the query.
#     Returns list of law abbreviations e.g. ["IPC", "CrPC"]
#     Falls back to all laws if nothing detected.
#     """
#     query_lower = query.lower()

#     # 1. Explicit law name in query e.g. "Section 138 NIA", "IPC 302"
#     explicit_map = {
#         "ipc": "IPC", "indian penal code": "IPC",
#         "crpc": "CrPC", "criminal procedure": "CrPC",
#         "cpc": "CPC", "civil procedure": "CPC",
#         "iea": "IEA", "evidence act": "IEA",
#         "mva": "MVA", "motor vehicle": "MVA",
#         "nia": "NIA", "negotiable instrument": "NIA",
#     }
#     for keyword, law in explicit_map.items():
#         if keyword in query_lower:
#             print(f"🎯 Explicit law detected: {law}")
#             return [law]

#     # 2. Keyword-based detection
#     detected = []
#     for law, keywords in LAW_KEYWORDS.items():
#         if any(kw in query_lower for kw in keywords):
#             detected.append(law)

#     if detected:
#         print(f"🔍 Laws detected from keywords: {detected}")
#         return detected

#     # 3. No match — search all laws
#     print("🌐 No specific law detected — searching all laws")
#     return list(LAW_FILES.values())


# # ── HYBRID RETRIEVAL ───────────────────────────────────────────────────────────

# def json_lookup(query: str, target_laws: list[str]) -> list[str]:
#     """
#     Exact section number lookup from in-memory law data.
#     Handles: Section 302, Section 138, Section 2A, Section 2.1, etc.
#     """
#     results  = []
#     law_data = get_law_data()

#     section_match = re.search(
#         r'\bsection\s*(\d+[a-zA-Z]*(?:\.\d+)?)\b',
#         query,
#         re.IGNORECASE
#     )
#     if not section_match:
#         return results

#     section_num = section_match.group(1).strip()
#     print(f"🔎 JSON lookup: Section {section_num} in {target_laws}")

#     for law in target_laws:
#         if law not in law_data:
#             continue

#         sections = law_data[law]

#         # Exact match
#         if section_num in sections:
#             entry = sections[section_num]
#             results.append(
#                 f"[{law}] Section {section_num}: {entry['title']}\n{entry['content']}"
#             )
#             print(f"✅ JSON hit: [{law}] Section {section_num}")

#         else:
#             # Case-insensitive fallback (e.g. "2a" vs "2A")
#             for key, entry in sections.items():
#                 if key.lower() == section_num.lower():
#                     results.append(
#                         f"[{law}] Section {key}: {entry['title']}\n{entry['content']}"
#                     )
#                     print(f"✅ JSON hit (fallback): [{law}] Section {key}")
#                     break

#     return results


# def faiss_search(query: str, target_laws: list[str], k: int = 5, threshold: float = 1.5) -> list[str]:
#     """
#     Semantic FAISS search filtered to target laws.
#     FAISS L2 distance — lower = more similar.
#     """
#     results = []
#     try:
#         vectorstore  = get_vectorstore()
#         # Fetch extra results to allow law filtering
#         raw_results  = vectorstore.similarity_search_with_score(query, k=k * 3)

#         if not raw_results:
#             return results

#         top_score = raw_results[0][1]
#         print(f"📊 FAISS top score: {top_score:.4f} (threshold: {threshold})")

#         if top_score > threshold:
#             print("⚠️ FAISS score above threshold — skipping")
#             return results

#         seen = set()
#         for doc, score in raw_results:
#             law     = doc.metadata.get("law", "")
#             section = doc.metadata.get("section", "")
#             key     = f"{law}_{section}"

#             if law not in target_laws:
#                 continue
#             if key in seen or score > threshold:
#                 continue

#             seen.add(key)
#             results.append(
#                 f"[{law}] Section {section} — {doc.metadata.get('title', '')}\n"
#                 f"{doc.page_content}"
#             )

#             if len(results) >= k:
#                 break

#         print(f"✅ FAISS returned {len(results)} results")
#     except Exception as e:
#         print(f"⚠️ FAISS search error: {e}")

#     return results


# def hybrid_retrieve(query: str, k: int = 5) -> tuple[str, str]:
#     """
#     Combines JSON exact lookup + FAISS semantic search.

#     Returns:
#         (context_text, source_type)
#         source_type: "JSON" | "RAG" | "HYBRID" | "GEN"
#     """
#     target_laws   = detect_laws(query)
#     context_parts = []
#     source        = "GEN"

#     # Step 1: Exact JSON lookup
#     json_results = json_lookup(query, target_laws)
#     if json_results:
#         context_parts.extend(json_results)
#         source = "JSON"

#     # Step 2: FAISS semantic search
#     faiss_results = faiss_search(query, target_laws, k=k)
#     for result in faiss_results:
#         if result not in context_parts:
#             context_parts.append(result)

#     if faiss_results:
#         source = "HYBRID" if source == "JSON" else "RAG"

#     context = "\n\n".join(context_parts)
#     return context.strip(), source


# # ── GROQ GENERATION ────────────────────────────────────────────────────────────

# groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))


# def groq_generate(prompt: str, temperature: float = 0.2) -> str:
#     try:
#         response = groq_client.chat.completions.create(
#             model=GROQ_MODEL,
#             messages=[
#                 {"role": "system", "content": SYSTEM_PROMPT},
#                 {"role": "user",   "content": prompt},
#             ],
#             temperature=temperature,
#             max_tokens=800,
#             top_p=0.9,
#         )
#         return response.choices[0].message.content.strip()
#     except Exception as e:
#         print(f"❌ Groq API error: {e}")
#         return ""


# def generate_response(prompt: str) -> str:
#     response = groq_generate(prompt, temperature=0.2)
#     if response:
#         return response
#     print("⚠️ Retrying with lower temperature...")
#     return groq_generate(prompt, temperature=0.1) or \
#         "Unable to generate a response at this time. Please try again."


# # ── MAIN PIPELINE ──────────────────────────────────────────────────────────────

# def process_input(chat_name: str, user_input: str, return_source: bool = False):
#     """
#     Full RAG pipeline:
#       1. Load chat history
#       2. Detect relevant laws from query
#       3. Hybrid retrieval (exact JSON + semantic FAISS)
#       4. Build prompt with context + history
#       5. Generate via Groq
#       6. Save and return

#     Args:
#         chat_name    : active chat session name
#         user_input   : user's question
#         return_source: if True, returns (response, source_type)

#     Returns:
#         str response, or (str, str) tuple if return_source=True
#     """
#     if not user_input or not user_input.strip():
#         msg = "Please enter a valid question."
#         return (msg, "GEN") if return_source else msg

#     # Load history
#     current_chat  = load_chat(chat_name)
#     history_pairs = list(zip(
#         current_chat.get("past", []),
#         current_chat.get("generated", [])
#     ))
#     history_prompt = "\n".join(
#         [f"User: {q}\nAssistant: {a}" for q, a in history_pairs[-4:]]
#     )

#     # Hybrid retrieval
#     context_text, source_type = hybrid_retrieve(user_input, k=5)

#     # Build context block
#     if context_text and len(context_text.strip()) > 30 and source_type != "GEN":
#         context_block = (
#             "The following legal sections have been retrieved from the database "
#             "and are directly relevant to the user's question:\n\n"
#             f"{context_text}\n\n"
#             "Answer the user's question using ONLY the above context. "
#             "If the context does not fully cover the question, say so clearly."
#         )
#     else:
#         source_type   = "GEN"
#         context_block = (
#             "No specific legal section was found in the database for this query. "
#             "Provide a general educational summary based on Indian law. "
#             "Clearly state this is general information, not a specific legal provision."
#         )

#     # Final prompt
#     full_prompt = f"""{context_block}

# {'Conversation History:' + chr(10) + history_prompt if history_prompt else ''}

# User Question: {user_input}
# Assistant:"""

#     response = generate_response(full_prompt)

#     # Persist to chat history
#     current_chat["past"].append(user_input)
#     current_chat["generated"].append(response)
#     current_chat["source"].append(source_type)
#     save_chat(chat_name, current_chat)

#     print(f"⚡ Source: {source_type} | Q: {user_input[:60]}...")
#     return (response, source_type) if return_source else response
import json
import os
import re
from dotenv import load_dotenv

from groq import Groq
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document
from transformers import AutoTokenizer, AutoModel

load_dotenv()

# ── CONFIG ─────────────────────────────────────────────────────────────────────

CHATS_FILE = os.path.join(os.path.dirname(__file__), "..", "chats.json")
LAWS_DIR   = os.path.join(os.path.dirname(__file__), "..", "laws_json")
FAISS_PATH = "laws_embed_db"

# Map filename → law abbreviation
LAW_FILES = {
    "ipc.json":  "IPC",
    "crpc.json": "CrPC",
    "cpc.json":  "CPC",
    "iea.json":  "IEA",
    "mva.json":  "MVA",
    "nia.json":  "NIA",
}

# Keywords to detect which law a query is about
LAW_KEYWORDS = {
    "IPC":  ["ipc", "indian penal code", "murder", "theft", "assault", "rape",
             "cheating", "fraud", "robbery", "kidnapping", "hurt", "criminal"],
    "CrPC": ["crpc", "criminal procedure", "arrest", "bail", "fir", "cognizable",
             "magistrate", "trial", "warrant", "summons", "investigation"],
    "CPC":  ["cpc", "civil procedure", "civil court", "decree", "suit", "plaint",
             "execution", "injunction", "appeal", "civil"],
    "IEA":  ["iea", "evidence act", "evidence", "admissible", "witness",
             "confession", "burden of proof", "presumption"],
    "MVA":  ["mva", "motor vehicle", "traffic", "driving licence", "accident",
             "vehicle", "road", "insurance", "permit"],
    "NIA":  ["nia", "negotiable instrument", "cheque", "bounce", "dishonour",
             "promissory note", "bill of exchange", "section 138"],
}

GROQ_MODEL = "llama-3.3-70b-versatile"

SYSTEM_PROMPT = """You are an AI Legal Assistant specialized in Indian law.
You will be given relevant legal sections retrieved from a database.
Your job is to explain them clearly and accurately based ONLY on the provided context.
Do NOT use any outside knowledge — only explain what is in the given context.
This is educational information, not legal advice.
Use neutral, academic language."""


# ── LOCAL CHAT STORAGE ─────────────────────────────────────────────────────────

def _load_all_chats() -> dict:
    if os.path.exists(CHATS_FILE):
        with open(CHATS_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}

def _save_all_chats(data: dict) -> None:
    with open(CHATS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_chat(chat_name: str) -> dict:
    return _load_all_chats().get(chat_name, {"generated": [], "past": [], "source": []})

def save_chat(chat_name: str, chat_data: dict) -> None:
    all_chats = _load_all_chats()
    all_chats[chat_name] = chat_data
    _save_all_chats(all_chats)

def create_new_chat() -> str:
    all_chats = _load_all_chats()
    new_chat_name = f"Chat {len(all_chats) + 1}"
    all_chats[new_chat_name] = {"generated": [], "past": [], "source": []}
    _save_all_chats(all_chats)
    return new_chat_name

def get_chat_list() -> list:
    return list(_load_all_chats().keys())

def delete_chat(chat_name: str) -> None:
    all_chats = _load_all_chats()
    if chat_name in all_chats:
        del all_chats[chat_name]
        _save_all_chats(all_chats)


# ── NORMALIZER ─────────────────────────────────────────────────────────────────

def normalize_entry(entry: dict, law: str) -> dict | None:
    """
    Normalize all law JSON formats into one standard structure:
    { "law": str, "section": str, "title": str, "content": str }

    Handles all 3 formats:
    - IPC:          { "Section"(capital S), "section_title", "section_desc" }
    - CrPC/IEA/NIA: { "section", "section_title", "section_desc" }
    - CPC/MVA:      { "section", "title", "description" }
    """
    try:
        # Section number — IPC uses capital "Section"
        section = str(
            entry.get("Section") or
            entry.get("section") or ""
        ).strip()

        if not section:
            return None

        # Title
        title = str(
            entry.get("section_title") or
            entry.get("title") or ""
        ).strip()

        # Content
        content = str(
            entry.get("section_desc") or
            entry.get("description") or
            entry.get("content") or ""
        ).strip()

        if not content:
            return None

        return {
            "law":     law,
            "section": section,
            "title":   title,
            "content": content,
        }
    except Exception as e:
        print(f"⚠️ Normalize error [{law}]: {e}")
        return None


def load_all_laws() -> list[dict]:
    """Load and normalize all law JSON files into a unified list."""
    all_entries = []

    for filename, law_name in LAW_FILES.items():
        filepath = os.path.join(LAWS_DIR, filename)

        if not os.path.exists(filepath):
            print(f"⚠️ File not found: {filepath}")
            continue

        with open(filepath, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError as e:
                print(f"❌ JSON parse error in {filename}: {e}")
                continue

        if not isinstance(data, list):
            print(f"⚠️ Unexpected format in {filename} — expected a list")
            continue

        count = 0
        for entry in data:
            normalized = normalize_entry(entry, law_name)
            if normalized:
                all_entries.append(normalized)
                count += 1

        print(f"✅ Loaded {count} sections from {filename} ({law_name})")

    print(f"📚 Total sections loaded across all laws: {len(all_entries)}")
    return all_entries


# ── EMBEDDING & FAISS ──────────────────────────────────────────────────────────

MODEL_NAME      = "sentence-transformers/all-MiniLM-L6-v2"
model_cache_dir = os.path.join(os.path.expanduser("~"), ".cache", "huggingface", "hub")

_embedding_model = None
_vectorstore     = None
_law_data        = None


def get_embedding_model() -> HuggingFaceEmbeddings:
    global _embedding_model
    if _embedding_model is None:
        try:
            AutoTokenizer.from_pretrained(MODEL_NAME, cache_dir=model_cache_dir)
            AutoModel.from_pretrained(MODEL_NAME, cache_dir=model_cache_dir)
            print("✅ InLegalBERT ready.")
        except Exception as e:
            print(f"⚠️ InLegalBERT load warning: {e}")
        _embedding_model = HuggingFaceEmbeddings(model_name=MODEL_NAME)
    return _embedding_model


def get_law_data() -> dict:
    """
    Build in-memory lookup index:
    { "IPC": { "302": {...}, "378": {...} }, "CrPC": { "41": {...} }, ... }
    """
    global _law_data
    if _law_data is None:
        _law_data = {}
        for entry in load_all_laws():
            law     = entry["law"]
            section = entry["section"]
            if law not in _law_data:
                _law_data[law] = {}
            _law_data[law][section] = entry
    return _law_data


def build_faiss_index() -> FAISS:
    """Build combined FAISS index from all law files."""
    print("🔨 Building FAISS index from all law files...")
    all_entries = load_all_laws()

    docs = []
    for entry in all_entries:
        text = (
            f"[{entry['law']}] Section {entry['section']}: "
            f"{entry['title']}\n{entry['content']}"
        )
        docs.append(Document(
            page_content=text,
            metadata={
                "law":     entry["law"],
                "section": entry["section"],
                "title":   entry["title"],
            }
        ))

    vs = FAISS.from_documents(docs, get_embedding_model())
    vs.save_local(FAISS_PATH)
    print(f"✅ FAISS index built with {len(docs)} total documents.")
    return vs


def get_vectorstore() -> FAISS:
    global _vectorstore
    if _vectorstore is None:
        try:
            _vectorstore = FAISS.load_local(
                FAISS_PATH,
                get_embedding_model(),
                allow_dangerous_deserialization=True
            )
            _ = _vectorstore.similarity_search("test", k=1)
            print("✅ FAISS index loaded from disk.")
        except Exception as e:
            print(f"❌ FAISS load failed: {e}. Rebuilding...")
            _vectorstore = build_faiss_index()
    return _vectorstore


# ── LAW DETECTION ──────────────────────────────────────────────────────────────

def detect_laws(query: str) -> list[str]:
    """
    Detect which laws are relevant to the query.
    Returns list of law abbreviations e.g. ["IPC", "CrPC"]
    Falls back to all laws if nothing detected.
    """
    query_lower = query.lower()

    # Explicit law name in query
    explicit_map = {
        "ipc": "IPC", "indian penal code": "IPC",
        "crpc": "CrPC", "criminal procedure": "CrPC",
        "cpc": "CPC", "civil procedure": "CPC",
        "iea": "IEA", "evidence act": "IEA",
        "mva": "MVA", "motor vehicle": "MVA",
        "nia": "NIA", "negotiable instrument": "NIA",
    }
    for keyword, law in explicit_map.items():
        if keyword in query_lower:
            print(f"🎯 Explicit law detected: {law}")
            return [law]

    # Keyword-based detection
    detected = []
    for law, keywords in LAW_KEYWORDS.items():
        if any(kw in query_lower for kw in keywords):
            detected.append(law)

    if detected:
        print(f"🔍 Laws detected from keywords: {detected}")
        return detected

    print("🌐 No specific law detected — searching all laws")
    return list(LAW_FILES.values())


# ── HYBRID RETRIEVAL ───────────────────────────────────────────────────────────

def json_lookup(query: str, target_laws: list[str]) -> list[str]:
    """
    Exact section number lookup from in-memory law data.
    Handles: Section 302, Section 138, Section 2A, etc.
    """
    results  = []
    law_data = get_law_data()

    section_match = re.search(
        r'\bsection\s*(\d+[a-zA-Z]*(?:\.\d+)?)\b',
        query,
        re.IGNORECASE
    )
    if not section_match:
        return results

    section_num = section_match.group(1).strip()
    print(f"🔎 JSON lookup: Section {section_num} in {target_laws}")

    for law in target_laws:
        if law not in law_data:
            continue

        sections = law_data[law]

        if section_num in sections:
            entry = sections[section_num]
            results.append(
                f"[{law}] Section {section_num}: {entry['title']}\n{entry['content']}"
            )
            print(f"✅ JSON hit: [{law}] Section {section_num}")
        else:
            for key, entry in sections.items():
                if key.lower() == section_num.lower():
                    results.append(
                        f"[{law}] Section {key}: {entry['title']}\n{entry['content']}"
                    )
                    print(f"✅ JSON hit (fallback): [{law}] Section {key}")
                    break

    return results


def faiss_search(query: str, target_laws: list[str], k: int = 5, threshold: float = 60.0) -> list[str]:
    """
    Semantic FAISS search filtered to target laws.
    FAISS L2 distance — lower = more similar.
    """
    results = []
    try:
        vectorstore = get_vectorstore()
        raw_results = vectorstore.similarity_search_with_score(query, k=k * 3)

        if not raw_results:
            return results

        top_score = raw_results[0][1]
        print(f"📊 FAISS top score: {top_score:.4f} (threshold: {threshold})")

        if top_score > threshold:
            print("⚠️ FAISS score above threshold — skipping")
            return results

        seen = set()
        for doc, score in raw_results:
            law     = doc.metadata.get("law", "")
            section = doc.metadata.get("section", "")
            key     = f"{law}_{section}"

            if law not in target_laws:
                continue
            if key in seen or score > threshold:
                continue

            seen.add(key)
            results.append(
                f"[{law}] Section {section} — {doc.metadata.get('title', '')}\n"
                f"{doc.page_content}"
            )

            if len(results) >= k:
                break

        print(f"✅ FAISS returned {len(results)} results")
    except Exception as e:
        print(f"⚠️ FAISS search error: {e}")

    return results


def hybrid_retrieve(query: str, k: int = 5) -> tuple[str, str]:
    """
    Combines JSON exact lookup + FAISS semantic search.
    Returns: (context_text, source_type)
    source_type: "JSON" | "RAG" | "HYBRID" | "GEN"
    """
    target_laws   = detect_laws(query)
    context_parts = []
    source        = "GEN"

    # Step 1: Exact JSON lookup
    json_results = json_lookup(query, target_laws)
    if json_results:
        context_parts.extend(json_results)
        source = "JSON"

    # Step 2: FAISS semantic search
    faiss_results = faiss_search(query, target_laws, k=k)
    for result in faiss_results:
        if result not in context_parts:
            context_parts.append(result)

    if faiss_results:
        source = "HYBRID" if source == "JSON" else "RAG"

    context = "\n\n".join(context_parts)
    return context.strip(), source


# ── GROQ GENERATION ────────────────────────────────────────────────────────────

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def groq_generate(prompt: str, temperature: float = 0.2) -> str:
    try:
        response = groq_client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": prompt},
            ],
            temperature=temperature,
            max_tokens=800,
            top_p=0.9,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"❌ Groq API error: {e}")
        return ""


def generate_response(prompt: str) -> str:
    response = groq_generate(prompt, temperature=0.2)
    if response:
        return response
    print("⚠️ Retrying with lower temperature...")
    return groq_generate(prompt, temperature=0.1) or \
        "Unable to generate a response at this time. Please try again."


# ── MAIN PIPELINE ──────────────────────────────────────────────────────────────

def process_input(chat_name: str, user_input: str, return_source: bool = False):
    """
    Full RAG pipeline:
      1. Load chat history
      2. Detect relevant laws from query
      3. Hybrid retrieval (exact JSON + semantic FAISS)
      4. If nothing found → return "not found" message (NO AI hallucination)
      5. If found → build prompt and generate via Groq
      6. Save and return

    Args:
        chat_name    : active chat session name
        user_input   : user's question
        return_source: if True, returns (response, source_type)

    Returns:
        str response, or (str, str) tuple if return_source=True
    """
    if not user_input or not user_input.strip():
        msg = "Please enter a valid question."
        return (msg, "GEN") if return_source else msg

    # Load history
    current_chat  = load_chat(chat_name)
    history_pairs = list(zip(
        current_chat.get("past", []),
        current_chat.get("generated", [])
    ))
    history_prompt = "\n".join(
        [f"User: {q}\nAssistant: {a}" for q, a in history_pairs[-4:]]
    )

    # Hybrid retrieval
    context_text, source_type = hybrid_retrieve(user_input, k=8)

    # ── GEN GUARD — No hallucination allowed ──────────────────────────────────
    if source_type == "GEN" or not context_text or len(context_text.strip()) <= 30:
        msg = (
            "I could not find relevant information for your question in the legal database.\n"
            "Please try:\n"
            "• Rephrasing your question\n"
            "• Mentioning a specific law (IPC, CrPC, NIA, etc.)\n"
            "• Asking about a specific section number"
        )
        current_chat["past"].append(user_input)
        current_chat["generated"].append(msg)
        current_chat["source"].append("GEN")
        save_chat(chat_name, current_chat)
        print(f"⚠️ GEN blocked | Q: {user_input[:60]}...")
        return (msg, "GEN") if return_source else msg

    # ── RAG answer from retrieved context only ────────────────────────────────
    context_block = (
        "The following legal sections have been retrieved from the database "
        "and are directly relevant to the user's question:\n\n"
        f"{context_text}\n\n"
        "Answer the user's question using ONLY the above context. "
        "Do NOT use any outside knowledge. "
        "If the context does not fully cover the question, say so clearly."
    )

    full_prompt = f"""{context_block}

{'Conversation History:' + chr(10) + history_prompt if history_prompt else ''}

User Question: {user_input}
Assistant:"""

    response = generate_response(full_prompt)

    # Persist to chat history
    current_chat["past"].append(user_input)
    current_chat["generated"].append(response)
    current_chat["source"].append(source_type)
    save_chat(chat_name, current_chat)

    print(f"⚡ Source: {source_type} | Q: {user_input[:60]}...")
    return (response, source_type) if return_source else response