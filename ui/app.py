"""Interactive Research UI for Evidence-Grounded Misinformation Verification.

Run with: streamlit run ui/app.py
"""

import html
import json
from pathlib import Path
import sys
import streamlit as st

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.pipeline.schema import NLILabel, Verdict
from src.pipeline.verifier import MisinformationVerifier
from src.utils.config import load_config

st.set_page_config(
    page_title="Evidence-Grounded Misinformation Verification",
    page_icon="🔍",
    layout="wide",
)

# Custom CSS for rich research presentation
st.markdown(
    """
    <style>
    .verdict-supported {
        background-color: #d1fae5;
        color: #065f46;
        padding: 12px 20px;
        border-radius: 8px;
        font-weight: 700;
        font-size: 1.5rem;
        display: inline-block;
        border: 2px solid #10b981;
    }
    .verdict-contradicted {
        background-color: #fee2e2;
        color: #991b1b;
        padding: 12px 20px;
        border-radius: 8px;
        font-weight: 700;
        font-size: 1.5rem;
        display: inline-block;
        border: 2px solid #ef4444;
    }
    .verdict-insufficient {
        background-color: #fef3c7;
        color: #92400e;
        padding: 12px 20px;
        border-radius: 8px;
        font-weight: 700;
        font-size: 1.5rem;
        display: inline-block;
        border: 2px solid #f59e0b;
    }
    .evidence-card {
        padding: 14px;
        border-radius: 8px;
        margin-bottom: 12px;
        border-left: 5px solid #6b7280;
        background-color: #f9fafb;
    }
    .evidence-support {
        border-left-color: #10b981;
        background-color: #f0fdf4;
    }
    .evidence-contradict {
        border-left-color: #ef4444;
        background-color: #fef2f2;
    }
    .evidence-neutral {
        border-left-color: #9ca3af;
        background-color: #f9fafb;
    }
    </style>
""",
    unsafe_allow_html=True,
)


@st.cache_resource
def get_verifier(config_path: str = "configs/default.yaml"):
    return MisinformationVerifier(config_path=config_path)


def format_passage_html(p, card_class: str) -> str:
    """Safely format an EvidencePassage into an HTML card with all dynamic fields escaped."""
    safe_source = html.escape(str(p.source if p.source is not None else "Corpus"), quote=True)
    safe_date = html.escape(str(p.published_date if p.published_date is not None else "N/A"), quote=True)
    relation_val = (
        p.nli_label.value
        if (p.nli_label and hasattr(p.nli_label, "value"))
        else (str(p.nli_label) if p.nli_label else "N/A")
    )
    safe_relation = html.escape(str(relation_val), quote=True)
    nli_score_str = f"{p.nli_score:.1%}" if p.nli_score is not None else "N/A"
    rel_score_str = f"{p.relevance_score:.2f}" if p.relevance_score is not None else "N/A"
    temp_valid_str = f"{p.temporal_validity:.2f}" if p.temporal_validity is not None else "N/A"
    safe_text = html.escape(str(p.text if p.text is not None else ""), quote=True)
    safe_notes = html.escape(str(p.temporal_notes if p.temporal_notes is not None else ""), quote=True)
    safe_card_class = html.escape(str(card_class), quote=True)

    notes_block = f"\n                    <small><i>{safe_notes}</i></small>" if safe_notes else ""

    return f"""
                <div class="evidence-card {safe_card_class}">
                    <b>Source:</b> {safe_source} &nbsp;|&nbsp; <b>Date:</b> {safe_date} &nbsp;|&nbsp; 
                    <b>NLI Relation:</b> <code>{safe_relation}</code> ({nli_score_str}) &nbsp;|&nbsp;
                    <b>Relevance:</b> {rel_score_str} &nbsp;|&nbsp; <b>Temporal Validity:</b> {temp_valid_str}<br>
                    <p style="margin-top: 8px;">{safe_text}</p>{notes_block}
                </div>
                """


# Sidebar controls
st.sidebar.title("Configuration & Benchmarks")
config_choice = st.sidebar.selectbox(
    "Active Pipeline Configuration",
    ["configs/default.yaml", "configs/baseline.yaml"],
    index=0,
)

sample_claims = [
    "The Earth has experienced its hottest year on record.",
    "The Eiffel Tower is located in Paris, France.",
    "Roman Atwood was born in London, England.",
    "Acme Corporation is currently the market leader in autonomous delivery drones.",
    "Vaccine-X is 92% effective with absolutely zero reported cases of severe adverse reactions.",
    "The company launched its product in 2024 and generated $10 million in revenue that year.",
    "The mysterious civilization of Atlantis built a crystal pyramid on Europa in 1492.",
]

selected_sample = st.sidebar.selectbox("Choose Benchmark Example:", ["-- Custom Claim --"] + sample_claims)

st.title("Evidence-Grounded Misinformation Verification")
st.markdown(
    "**Claim-level verification with external evidence retrieval, NLI, temporal awareness, conflict detection, and calibrated uncertainty.**"
)

default_claim = "" if selected_sample == "-- Custom Claim --" else selected_sample
claim_input = st.text_area("Enter textual claim to verify:", value=default_claim, height=100)

col_btn, _ = st.columns([1, 4])
with col_btn:
    verify_clicked = st.button("Verify Claim", type="primary", use_container_width=True)

if verify_clicked and claim_input.strip():
    with st.spinner("Executing verification pipeline..."):
        verifier = get_verifier(config_choice)
        result = verifier.verify(claim_input.strip())

    st.markdown("---")
    st.subheader("Verification Decision")

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        if result.verdict == Verdict.SUPPORTED:
            st.markdown('<div class="verdict-supported">SUPPORTED</div>', unsafe_allow_html=True)
        elif result.verdict == Verdict.CONTRADICTED:
            st.markdown('<div class="verdict-contradicted">CONTRADICTED</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="verdict-insufficient">INSUFFICIENT EVIDENCE</div>', unsafe_allow_html=True)

    with c2:
        st.metric("Calibrated Confidence", f"{result.confidence:.1%}")
    with c3:
        st.metric("Total Uncertainty", f"{result.uncertainty:.1%}")
    with c4:
        conflict_status = "⚠️ DETECTED" if result.conflict_detected else "✅ None"
        st.metric("Evidence Conflict", conflict_status)

    # Subclaims if decomposed
    if result.subclaims and len(result.subclaims) > 1:
        st.markdown("#### Atomic Subclaim Decomposition")
        for sc in result.subclaims:
            v_val = sc.verdict.value if sc.verdict else "N/A"
            conf_val = f"{sc.confidence:.1%}" if sc.confidence is not None else "N/A"
            st.info(f"**[{v_val}]** (Confidence: {conf_val}) — {sc.text}")

    # Explanation
    st.markdown("#### Auditable Explanation")
    st.info(result.reasoning)

    # Evidence breakdown
    st.markdown("---")
    st.subheader(f"Retrieved External Evidence ({len(result.evidence)} Passages)")

    if not result.evidence:
        st.warning("No relevant external evidence found in corpus matching this claim.")
    else:
        tab_all, tab_sup, tab_con, tab_neu = st.tabs([
            f"All Evidence ({len(result.evidence)})",
            f"Supporting ({sum(1 for p in result.evidence if p.nli_label == NLILabel.SUPPORT)})",
            f"Contradicting ({sum(1 for p in result.evidence if p.nli_label == NLILabel.CONTRADICT)})",
            f"Neutral / Other ({sum(1 for p in result.evidence if p.nli_label not in (NLILabel.SUPPORT, NLILabel.CONTRADICT))})",
        ])

        def render_passage(p, card_class):
            st.markdown(format_passage_html(p, card_class), unsafe_allow_html=True)

        with tab_all:
            for p in result.evidence:
                cls = "evidence-support" if p.nli_label == NLILabel.SUPPORT else ("evidence-contradict" if p.nli_label == NLILabel.CONTRADICT else "evidence-neutral")
                render_passage(p, cls)

        with tab_sup:
            sup_passages = [p for p in result.evidence if p.nli_label == NLILabel.SUPPORT]
            if not sup_passages:
                st.write("No supporting evidence passages found.")
            for p in sup_passages:
                render_passage(p, "evidence-support")

        with tab_con:
            con_passages = [p for p in result.evidence if p.nli_label == NLILabel.CONTRADICT]
            if not con_passages:
                st.write("No contradicting evidence passages found.")
            for p in con_passages:
                render_passage(p, "evidence-contradict")

        with tab_neu:
            neu_passages = [p for p in result.evidence if p.nli_label not in (NLILabel.SUPPORT, NLILabel.CONTRADICT)]
            if not neu_passages:
                st.write("No neutral passages.")
            for p in neu_passages:
                render_passage(p, "evidence-neutral")

    # Diagnostic metadata
    with st.expander("Diagnostic Metadata & Signal Decomposition"):
        st.json(result.metadata)
