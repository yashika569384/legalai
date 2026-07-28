# import streamlit as st
# import time

# from views.chatbotLegalv2 import process_input, create_new_chat
# from views.docGen import generate_legal_document
# from vector_database import index_pdf, upload_pdf
# from rag_pipeline import answer_query, retrieve_docs, llm_model, summarize_document, generate_report

# st.set_page_config(page_title="⚖️ Legal AI System", page_icon="⚖️", layout="wide")

# st.markdown("""
# <style>
# html, body, [class*="css"] {
#     font-size: 18px;
# }

# /* ── Chatbot bubbles ── */
# .user-box {
#     background-color: #DCF8C6;
#     color: #000000;
#     padding: 10px;
#     border-radius: 10px;
#     margin: 10px 0;
#     text-align: left;
# }

# .bot-box {
#     background-color: #F1F0F0;
#     color: #000000;
#     padding: 10px;
#     border-radius: 10px;
#     margin: 10px 0;
#     text-align: left;
# }

# /* ── Document Analyzer ── */
# .summary-box {
#     background-color: #1E1E1E;
#     padding: 15px;
#     border-left: 5px solid #4CAF50;
#     color: #E0E0E0;
#     border-radius: 10px;
#     box-shadow: 0px 4px 10px rgba(76, 175, 80, 0.3);
# }

# .stButton button {
#     border-radius: 10px;
#     font-weight: bold;
# }
# </style>
# """, unsafe_allow_html=True)

# st.title("⚖️ Legal AI System")

# tab1, tab2, tab3 = st.tabs(["💬 IPC Chatbot", "📄 Document Generator", "🔍 Document Analyzer"])


# # ════════════════════════════════════════════════════════
# # TAB 1 — IPC CHATBOT
# # ════════════════════════════════════════════════════════
# with tab1:

#     if "chat_name" not in st.session_state:
#         st.session_state.chat_name = create_new_chat()

#     if "chat" not in st.session_state:
#         st.session_state.chat = []

#     if "input_counter" not in st.session_state:
#         st.session_state.input_counter = 0

#     current_key = f"user_input_{st.session_state.input_counter}"
#     user_input = st.text_input("Ask your legal question", key=current_key)

#     col1, col2 = st.columns([1, 5])
#     with col1:
#         send = st.button("Send", key="send_btn")
#     with col2:
#         clear = st.button("🗑️ Clear Chat", key="clear_btn")

#     if clear:
#         st.session_state.chat = []
#         st.session_state.input_counter += 1
#         st.rerun()

#     if send:
#         if user_input:
#             response, _ = process_input(
#                 st.session_state.chat_name,
#                 user_input,
#                 return_source=True
#             )
#             st.session_state.chat.insert(0, ("Bot", response))
#             st.session_state.chat.insert(0, ("You", user_input))
#             st.session_state.input_counter += 1
#             st.rerun()

#     for role, msg in st.session_state.chat:
#         if role == "You":
#             st.markdown(
#                 f'<div class="user-box"><b>You:</b><br>{msg}</div>',
#                 unsafe_allow_html=True
#             )
#         else:
#             st.markdown(
#                 f'<div class="bot-box"><b>Legal AI:</b><br>{msg}</div>',
#                 unsafe_allow_html=True
#             )


# # ════════════════════════════════════════════════════════
# # TAB 2 — DOCUMENT GENERATOR
# # ════════════════════════════════════════════════════════
# with tab2:

#     prompt = st.text_area("Enter document request", key="doc_gen_prompt")

#     if st.button("Generate Document", key="gen_doc_btn"):
#         if prompt:
#             file_path, file_name = generate_legal_document(prompt)
#             st.success("Document generated!")
#             with open(file_path, "rb") as f:
#                 st.download_button(
#                     "⬇ Download",
#                     f,
#                     file_name=file_name,
#                     key="download_doc_btn"
#                 )


# # ════════════════════════════════════════════════════════
# # TAB 3 — DOCUMENT ANALYZER
# # ════════════════════════════════════════════════════════
# with tab3:

#     st.markdown("### 🔍 Document Analyzer")
#     st.markdown("Upload a legal PDF and ask questions or get a summary .")

#     # Session state for analyzer chat history
#     if "analyzer_queries" not in st.session_state:
#         st.session_state.analyzer_queries = []
#     if "analyzer_responses" not in st.session_state:
#         st.session_state.analyzer_responses = []

#     uploaded_file = st.file_uploader(
#         "📂 Upload a legal document (PDF)",
#         type="pdf",
#         accept_multiple_files=False,
#         key="doc_analyzer_upload"
#     )

#     if uploaded_file:
#         st.success(f"📄 Uploaded: **{uploaded_file.name}**")

#         file_path = upload_pdf(uploaded_file)
#         index_pdf(file_path)

#         # ── Summarize ──
#         if st.button("📜 Summarize Document", key="summarize_btn"):
#             with st.spinner("🔍 Generating summary..."):
#                 time.sleep(1)
#                 retrieved_docs = retrieve_docs("Summarize this document", uploaded_file.name)
#                 if not retrieved_docs:
#                     st.error("❌ No content retrieved. Try re-uploading the document.")
#                 else:
#                     summary = summarize_document(retrieved_docs)
#                     st.markdown("### 📝 Document Summary")
#                     # Extract text if response is an AIMessage object
#                     summary_text = summary.content if hasattr(summary, "content") else str(summary)
#                     st.markdown(f"<div class='summary-box'>{summary_text}</div>", unsafe_allow_html=True)

#         st.markdown("---")

#         # ── Q&A ──
#         analyzer_query = st.text_area(
#             "💬 Ask a question about the document:",
#             height=120,
#             placeholder="Type your question here...",
#             key="analyzer_query_input"
#         )

#         col3, col4 = st.columns([1, 5])
#         with col3:
#             ask_btn = st.button("🔍 Ask", key="ask_analyzer_btn")
#         with col4:
#             clear_analyzer = st.button("🗑️ Clear", key="clear_analyzer_btn")

#         if clear_analyzer:
#             st.session_state.analyzer_queries = []
#             st.session_state.analyzer_responses = []
#             st.rerun()

#         if ask_btn:
#             if analyzer_query:
#                 with st.spinner("⚡ Analyzing document..."):
#                     time.sleep(1)
#                     retrieved_docs = retrieve_docs(analyzer_query, uploaded_file.name)
#                     history = "\n".join([
#                         f"User: {q}\nAI: {a}"
#                         for q, a in zip(
#                             st.session_state.analyzer_queries,
#                             st.session_state.analyzer_responses
#                         )
#                     ])
#                     response = answer_query(
#                         documents=retrieved_docs,
#                         model=llm_model,
#                         query=analyzer_query,
#                         history=history
#                     )
#                     response_text = response.content if hasattr(response, "content") else str(response)

#                     st.session_state.analyzer_queries.append(analyzer_query)
#                     st.session_state.analyzer_responses.append(response_text)
#                     st.rerun()
#             else:
#                 st.warning("Please enter a question.")

#         # ── Display conversation ──
#         for q, a in zip(
#             reversed(st.session_state.analyzer_queries),
#             reversed(st.session_state.analyzer_responses)
#         ):
#             st.markdown(f'<div class="user-box"><b>You:</b><br>{q}</div>', unsafe_allow_html=True)
#             st.markdown(f'<div class="bot-box"><b>Legal AI:</b><br>{a}</div>', unsafe_allow_html=True)

#         # ── Download Report ──
#         if st.session_state.analyzer_queries:
#             st.markdown("---")
#             if st.button("📥 Download Report", key="download_report_btn"):
#                 report_path = generate_report(
#                     st.session_state.analyzer_queries,
#                     st.session_state.analyzer_responses
#                 )
#                 with open(report_path, "rb") as f:
#                     st.download_button(
#                         label="📄 Download AI Lawyer Report",
#                         data=f,
#                         file_name="AI_Lawyer_Report.pdf",
#                         mime="application/pdf",
#                         key="dl_report_btn"
#                     )
#     else:
#         st.info("👆 Please upload a PDF to get started.")
import streamlit as st
import time

from views.chatbotLegalv2 import process_input, create_new_chat
from views.docGen import generate_legal_document
from vector_database import index_pdf, upload_pdf
from rag_pipeline import answer_query, retrieve_docs, llm_model, summarize_document, generate_report

st.set_page_config(page_title="AskLegal.ai", page_icon="⚖️", layout="wide")

st.markdown("""
<style>
html, body, [class*="css"] {
    font-size: 17px;
}

/* ── Chat bubbles ── */
.user-box {
    background-color: #DCF8C6;
    color: #000000;
    padding: 10px 14px;
    border-radius: 10px;
    margin: 8px 0;
    text-align: left;
}
.bot-box {
    background-color: #F1F0F0;
    color: #000000;
    padding: 10px 14px;
    border-radius: 10px;
    margin: 8px 0;
    text-align: left;
}

/* ── Summary box ── */
.summary-box {
    background-color: #f9f9f9;
    padding: 15px;
    border-left: 5px solid #4A90D9;
    color: #111111;
    border-radius: 10px;
}

/* ── Hero / Welcome screen ── */
.hero {
    text-align: center;
    padding: 40px 20px 20px 20px;
}
.hero h1 {
    font-size: 3em;
    color: white;    #1a1a2e
    margin-bottom: 8px;
}
.hero p {
    font-size: 1.15em;
    color: #444;
    max-width: 680px;
    margin: 0 auto 30px auto;
    line-height: 1.7;
}
.hero-cards {
    display: flex;
    justify-content: center;
    gap: 24px;
    flex-wrap: wrap;
    margin-top: 10px;
}
.card {
    background: #ffffff;
    border: 1.5px solid #e0e0e0;
    border-radius: 14px;
    padding: 28px 24px;
    width: 210px;
    box-shadow: 0 4px 14px rgba(0,0,0,0.07);
    text-align: center;
}
.card .icon {
    font-size: 2.4em;
    margin-bottom: 10px;
}
.card h3 {
    font-size: 1.05em;
    color: #1a1a2e;
    margin-bottom: 8px;
}
.card p {
    font-size: 0.88em;
    color: #666;
    line-height: 1.5;
}
.disclaimer {
    margin-top: 40px;
    font-size: 0.82em;
    color: #999;
    text-align: center;
    font-style: italic;
}

/* ── Sidebar buttons ── */
section[data-testid="stSidebar"] .stButton button {
    width: 100%;
    text-align: left;
    border-radius: 10px;
    font-size: 1em;
    font-weight: 500;
    margin-bottom: 6px;
    padding: 10px 14px;
    background-color: transparent;
    border: 1.5px solid #ddd;
    color: inherit;
    transition: 0.2s;
}
section[data-testid="stSidebar"] .stButton button:hover {
    background-color: #f0f4ff;
    border-color: #4A90D9;
}
</style>
""", unsafe_allow_html=True)


# ── Session state for page ──
if "page" not in st.session_state:
    st.session_state.page = "home"


# ════════════════════════════════════════════════════════
# SIDEBAR
# ════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("## ⚖️ AskLegal.ai")
    st.markdown("---")

    if st.button("🏠  Home"):
        st.session_state.page = "home"
        st.rerun()

    if st.button("💬  Legal Chatbot"):
        st.session_state.page = "chatbot"
        st.rerun()

    if st.button("📄  Document Generator"):
        st.session_state.page = "docgen"
        st.rerun()

    if st.button("🔍  Document Analyzer"):
        st.session_state.page = "analyzer"
        st.rerun()

    st.markdown("---")
    

# ════════════════════════════════════════════════════════
# HOME / WELCOME SCREEN
# ════════════════════════════════════════════════════════
if st.session_state.page == "home":
    st.markdown("""
    <div class="hero">
        <h1>⚖️ AskLegal.ai</h1>
        <p>
            Your AI-powered legal assistant. Navigating legal matters can be overwhelming —
            AskLegal.ai simplifies it for you. Whether you want to understand Indian law,
            generate legal documents, or analyze your own legal files, we've got you covered.
        </p>
        <div class="hero-cards">
            <div class="card">
                <div class="icon">💬</div>
                <h3>Legal Chatbot</h3>
                <p>Ask anything about Indian law and get instant, accurate answers grounded in legal statutes.</p>
            </div>
            <div class="card">
                <div class="icon">📄</div>
                <h3>Document Generator</h3>
                <p>Generate ready-to-use legal documents in seconds just by describing what you need.</p>
            </div>
            <div class="card">
                <div class="icon">🔍</div>
                <h3>Document Analyzer</h3>
                <p>Upload any legal PDF, get a summary, ask questions, and download a full report.</p>
            </div>
        </div>
        
    </div>
    """, unsafe_allow_html=True)

    # Quick-access buttons below cards
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("💬 Open Legal Chatbot", use_container_width=True):
            st.session_state.page = "chatbot"
            st.rerun()
    with col2:
        if st.button("📄 Open Document Generator", use_container_width=True):
            st.session_state.page = "docgen"
            st.rerun()
    with col3:
        if st.button("🔍 Open Document Analyzer", use_container_width=True):
            st.session_state.page = "analyzer"
            st.rerun()


# ════════════════════════════════════════════════════════
# PAGE: LEGAL CHATBOT
# ════════════════════════════════════════════════════════
elif st.session_state.page == "chatbot":
    st.markdown("## 💬 Legal Chatbot")
    st.markdown("Ask questions about Indian law and get AI-powered explanations.")
    st.markdown("---")

    if "chat_name" not in st.session_state:
        st.session_state.chat_name = create_new_chat()
    if "chat" not in st.session_state:
        st.session_state.chat = []
    if "input_counter" not in st.session_state:
        st.session_state.input_counter = 0

    current_key = f"user_input_{st.session_state.input_counter}"
    user_input = st.text_input("Ask your legal question", key=current_key)

    col1, col2 = st.columns([1, 5])
    with col1:
        send = st.button("Send", key="send_btn")
    with col2:
        clear = st.button("🗑️ Clear Chat", key="clear_btn")

    if clear:
        st.session_state.chat = []
        st.session_state.input_counter += 1
        st.rerun()

    if send:
        if user_input:
            response, _ = process_input(
                st.session_state.chat_name,
                user_input,
                return_source=True
            )
            st.session_state.chat.insert(0, ("Bot", response))
            st.session_state.chat.insert(0, ("You", user_input))
            st.session_state.input_counter += 1
            st.rerun()

    for role, msg in st.session_state.chat:
        if role == "You":
            st.markdown(f'<div class="user-box"><b>You:</b><br>{msg}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="bot-box"><b>Legal AI:</b><br>{msg}</div>', unsafe_allow_html=True)


# ════════════════════════════════════════════════════════
# PAGE: DOCUMENT GENERATOR
# ════════════════════════════════════════════════════════
elif st.session_state.page == "docgen":
    st.markdown("## 📄 Document Generator")
    st.markdown("Describe the legal document you need and download it instantly.")
    st.markdown("---")

    prompt = st.text_area("Enter document request", height=150, key="doc_gen_prompt")

    if st.button("Generate Document", key="gen_doc_btn"):
        if prompt:
            with st.spinner("Generating your document..."):
                file_path, file_name = generate_legal_document(prompt)
            st.success("Document generated!")
            with open(file_path, "rb") as f:
                st.download_button(
                    "⬇ Download Document",
                    f,
                    file_name=file_name,
                    key="download_doc_btn"
                )
        else:
            st.warning("Please enter a document request.")


# ════════════════════════════════════════════════════════
# PAGE: DOCUMENT ANALYZER
# ════════════════════════════════════════════════════════
elif st.session_state.page == "analyzer":
    st.markdown("## 🔍 Document Analyzer")
    st.markdown("Upload a legal PDF — get a summary, ask questions, and download a full report.")
    st.markdown("---")

    if "analyzer_queries" not in st.session_state:
        st.session_state.analyzer_queries = []
    if "analyzer_responses" not in st.session_state:
        st.session_state.analyzer_responses = []

    uploaded_file = st.file_uploader(
        "📂 Upload a legal document (PDF)",
        type="pdf",
        accept_multiple_files=False,
        key="doc_analyzer_upload"
    )

    if uploaded_file:
        st.success(f"📄 Uploaded: **{uploaded_file.name}**")

        file_path = upload_pdf(uploaded_file)
        index_pdf(file_path)

        if st.button("📜 Summarize Document", key="summarize_btn"):
            with st.spinner("Generating summary..."):
                time.sleep(1)
                retrieved_docs = retrieve_docs("Summarize this document", uploaded_file.name)
                if not retrieved_docs:
                    st.error("❌ No content retrieved. Try re-uploading the document.")
                else:
                    summary = summarize_document(retrieved_docs)
                    summary_text = summary.content if hasattr(summary, "content") else str(summary)
                    st.markdown("### 📝 Document Summary")
                    st.markdown(f"<div class='summary-box'>{summary_text}</div>", unsafe_allow_html=True)

        st.markdown("---")

        analyzer_query = st.text_area(
            "💬 Ask a question about the document:",
            height=120,
            placeholder="e.g. What are the penalty clauses in this contract?",
            key="analyzer_query_input"
        )

        col3, col4 = st.columns([1, 5])
        with col3:
            ask_btn = st.button("🔍 Ask", key="ask_analyzer_btn")
        with col4:
            clear_analyzer = st.button("🗑️ Clear", key="clear_analyzer_btn")

        if clear_analyzer:
            st.session_state.analyzer_queries = []
            st.session_state.analyzer_responses = []
            st.rerun()

        if ask_btn:
            if analyzer_query:
                with st.spinner("Analyzing document..."):
                    time.sleep(1)
                    retrieved_docs = retrieve_docs(analyzer_query, uploaded_file.name)
                    history = "\n".join([
                        f"User: {q}\nAI: {a}"
                        for q, a in zip(
                            st.session_state.analyzer_queries,
                            st.session_state.analyzer_responses
                        )
                    ])
                    response = answer_query(
                        documents=retrieved_docs,
                        model=llm_model,
                        query=analyzer_query,
                        history=history
                    )
                    response_text = response.content if hasattr(response, "content") else str(response)
                    st.session_state.analyzer_queries.append(analyzer_query)
                    st.session_state.analyzer_responses.append(response_text)
                    st.rerun()
            else:
                st.warning("Please enter a question.")

        for q, a in zip(
            reversed(st.session_state.analyzer_queries),
            reversed(st.session_state.analyzer_responses)
        ):
            st.markdown(f'<div class="user-box"><b>You:</b><br>{q}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="bot-box"><b>Legal AI:</b><br>{a}</div>', unsafe_allow_html=True)

        if st.session_state.analyzer_queries:
            st.markdown("---")
            if st.button("📥 Download Report", key="download_report_btn"):
                report_path = generate_report(
                    st.session_state.analyzer_queries,
                    st.session_state.analyzer_responses
                )
                with open(report_path, "rb") as f:
                    st.download_button(
                        label="📄 Download AI Lawyer Report",
                        data=f,
                        file_name="AI_Lawyer_Report.pdf",
                        mime="application/pdf",
                        key="dl_report_btn"
                    )
    else:
        st.info("👆 Please upload a PDF to get started.")