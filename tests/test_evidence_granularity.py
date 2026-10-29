"""Regression tests for Evidence Granularity, Segmentation, Provenance, and Aggregation."""

import pytest
from src.aggregation.aggregator import EvidenceAggregator, AggregationResult
from src.pipeline.schema import EvidencePassage, NLILabel
from src.retrieval.segmenter import EvidenceSegmenter


# ---------------------------------------------------------------------------
# Evidence Segmenter Unit Tests
# ---------------------------------------------------------------------------


def test_segmenter_sentence_splitting_with_abbreviations():
    """Verify sentence segmentation correctly preserves abbreviations like Dr., U.K., U.S."""
    segmenter = EvidenceSegmenter(enabled=True, unit="sentence")
    text = (
        "Margaret Hilda Thatcher was born in Grantham. "
        "She served in the U.K. as Prime Minister from 1979 to 1990. "
        "Was she a chemist? Yes, Dr. Roberts noted that she studied chemistry at Oxford. "
        "She also visited the U.S. frequently."
    )
    sentences = segmenter.split_into_sentences(text)
    assert len(sentences) == 5
    assert "U.K." in sentences[1]
    assert sentences[2] == "Was she a chemist?"
    assert "Dr. Roberts" in sentences[3]
    assert "U.S." in sentences[4]


def test_segmenter_provenance_preservation():
    """Verify that source doc_id, source title, dates, and scores are preserved across segments."""
    segmenter = EvidenceSegmenter(enabled=True, unit="sentence")
    parent = EvidencePassage(
        id="wiki_margaret_thatcher",
        doc_id="wiki_margaret_thatcher",
        text=(
            "Margaret Thatcher served as Prime Minister. "
            "She was the Leader of the Conservative Party. "
            "She studied chemistry at Oxford."
        ),
        source="Wikipedia: Margaret Thatcher",
        published_date="2021-01-01",
        retrieval_score=0.95,
        relevance_score=0.95,
    )

    passages = segmenter.segment_passage(parent)
    assert len(passages) == 3

    for idx, p in enumerate(passages):
        assert p.doc_id == "wiki_margaret_thatcher"
        assert p.id == f"wiki_margaret_thatcher#s{idx}"
        assert p.source == "Wikipedia: Margaret Thatcher"
        assert p.published_date == "2021-01-01"
        assert p.retrieval_score == 0.95


def test_segmenter_bounded_passages():
    """Verify bounded passage windowing with max_sentences_per_passage > 1."""
    segmenter = EvidenceSegmenter(
        enabled=True,
        unit="bounded_passage",
        max_sentences_per_passage=2,
        max_characters=400,
    )
    parent = EvidencePassage(
        id="doc_1",
        text="Sentence 1. Sentence 2. Sentence 3. Sentence 4.",
    )
    passages = segmenter.segment_passage(parent)
    assert len(passages) == 2
    assert passages[0].text == "Sentence 1. Sentence 2."
    assert passages[1].text == "Sentence 3. Sentence 4."


def test_segmenter_disabled_or_document_mode():
    """Verify that document mode or disabled segmenter returns original passages untouched."""
    seg_disabled = EvidenceSegmenter(enabled=False)
    seg_doc = EvidenceSegmenter(enabled=True, unit="document")

    parent = EvidencePassage(
        id="doc_1",
        text="Sentence 1. Sentence 2. Sentence 3.",
    )

    out_disabled = seg_disabled.segment_passage(parent)
    assert len(out_disabled) == 1
    assert out_disabled[0].text == parent.text

    out_doc = seg_doc.segment_passage(parent)
    assert len(out_doc) == 1
    assert out_doc[0].text == parent.text


def test_segmenter_short_text_handling():
    """Verify that short texts below threshold are kept intact without fragmentation."""
    segmenter = EvidenceSegmenter(enabled=True, min_characters=20)
    short_passage = EvidencePassage(id="p_short", text="Short snippet.")
    res = segmenter.segment_passage(short_passage)
    assert len(res) == 1
    assert res[0].text == "Short snippet."


# ---------------------------------------------------------------------------
# Document-Aware Evidence Aggregation Unit Tests
# ---------------------------------------------------------------------------


def test_aggregation_multi_passage_same_document_prevents_neutral_dilution():
    """Verify that multiple neutral sentences from the same document do not dilute a decisive supporting sentence."""
    aggregator = EvidenceAggregator(temperature=1.0, pooling_mode="document_aware")

    # Document 1 has 1 strong supporting sentence and 3 neutral background sentences
    passages = [
        EvidencePassage(
            id="doc_thatcher#s0",
            doc_id="doc_thatcher",
            text="Margaret Thatcher served as Prime Minister from 1979 to 1990.",
            relevance_score=1.0,
            nli_label=NLILabel.SUPPORT,
            nli_probs={"SUPPORT": 0.998, "CONTRADICT": 0.001, "NEUTRAL": 0.001},
        ),
        EvidencePassage(
            id="doc_thatcher#s1",
            doc_id="doc_thatcher",
            text="She studied chemistry at Somerville College.",
            relevance_score=0.9,
            nli_label=NLILabel.NEUTRAL,
            nli_probs={"SUPPORT": 0.01, "CONTRADICT": 0.01, "NEUTRAL": 0.98},
        ),
        EvidencePassage(
            id="doc_thatcher#s2",
            doc_id="doc_thatcher",
            text="She became Leader of the Opposition in 1975.",
            relevance_score=0.85,
            nli_label=NLILabel.NEUTRAL,
            nli_probs={"SUPPORT": 0.02, "CONTRADICT": 0.01, "NEUTRAL": 0.97},
        ),
        EvidencePassage(
            id="doc_thatcher#s3",
            doc_id="doc_thatcher",
            text="In 1986 she oversaw financial deregulation.",
            relevance_score=0.8,
            nli_label=NLILabel.NEUTRAL,
            nli_probs={"SUPPORT": 0.01, "CONTRADICT": 0.01, "NEUTRAL": 0.98},
        ),
    ]

    res = aggregator.aggregate(passages)

    # In document-aware pooling, the document's supporting statement is preserved
    assert res.dominant_label == NLILabel.SUPPORT
    assert res.support_prob > 0.90
    assert res.num_documents == 1
    assert res.effective_mass == 1.0  # Document counted once, not 4 times


def test_aggregation_duplicate_passages_do_not_inflate_evidence_mass():
    """Verify that multiple identical or overlapping sentences from one document do not multiply evidence count."""
    aggregator = EvidenceAggregator(temperature=1.0, pooling_mode="document_aware")

    passages = [
        EvidencePassage(
            id="doc_thatcher#s0",
            doc_id="doc_thatcher",
            text="Thatcher served as Prime Minister.",
            relevance_score=1.0,
            nli_label=NLILabel.SUPPORT,
            nli_probs={"SUPPORT": 0.99, "CONTRADICT": 0.0, "NEUTRAL": 0.01},
        ),
        EvidencePassage(
            id="doc_thatcher#s1",
            doc_id="doc_thatcher",
            text="Thatcher was the Prime Minister.",
            relevance_score=0.95,
            nli_label=NLILabel.SUPPORT,
            nli_probs={"SUPPORT": 0.99, "CONTRADICT": 0.0, "NEUTRAL": 0.01},
        ),
    ]

    res = aggregator.aggregate(passages)
    assert res.num_documents == 1
    # Effective mass is capped at max document weight (1.0), not summed to 1.95
    assert res.effective_mass == 1.0
    assert res.support_prob > 0.95


def test_aggregation_multi_document_weighted_consensus():
    """Verify aggregation across two independent supporting documents and one weak neutral document."""
    aggregator = EvidenceAggregator(temperature=1.0, pooling_mode="document_aware")

    passages = [
        EvidencePassage(
            id="doc_A#s0",
            doc_id="doc_A",
            text="Doc A supporting statement.",
            relevance_score=1.0,
            nli_label=NLILabel.SUPPORT,
            nli_probs={"SUPPORT": 0.95, "CONTRADICT": 0.01, "NEUTRAL": 0.04},
        ),
        EvidencePassage(
            id="doc_B#s0",
            doc_id="doc_B",
            text="Doc B corroborating statement.",
            relevance_score=0.9,
            nli_label=NLILabel.SUPPORT,
            nli_probs={"SUPPORT": 0.92, "CONTRADICT": 0.01, "NEUTRAL": 0.07},
        ),
        EvidencePassage(
            id="doc_C#s0",
            doc_id="doc_C",
            text="Doc C tangential detail.",
            relevance_score=0.2,
            nli_label=NLILabel.NEUTRAL,
            nli_probs={"SUPPORT": 0.05, "CONTRADICT": 0.05, "NEUTRAL": 0.90},
        ),
    ]

    res = aggregator.aggregate(passages)
    assert res.num_documents == 3
    assert res.dominant_label == NLILabel.SUPPORT
    assert res.support_prob > 0.80
    assert res.effective_mass == pytest.approx(2.1, abs=0.05)


def test_aggregation_pooling_mode_comparison():
    """Demonstrate difference between document_aware pooling and passage_flat averaging."""
    doc_aware_agg = EvidenceAggregator(temperature=1.0, pooling_mode="document_aware")
    flat_agg = EvidenceAggregator(temperature=1.0, pooling_mode="passage_flat")

    passages = [
        EvidencePassage(
            id="doc_1#s0",
            doc_id="doc_1",
            text="Supporting sentence.",
            relevance_score=1.0,
            nli_label=NLILabel.SUPPORT,
            nli_probs={"SUPPORT": 0.99, "CONTRADICT": 0.0, "NEUTRAL": 0.01},
        ),
        EvidencePassage(
            id="doc_1#s1",
            doc_id="doc_1",
            text="Neutral background 1.",
            relevance_score=1.0,
            nli_label=NLILabel.NEUTRAL,
            nli_probs={"SUPPORT": 0.01, "CONTRADICT": 0.0, "NEUTRAL": 0.99},
        ),
        EvidencePassage(
            id="doc_1#s2",
            doc_id="doc_1",
            text="Neutral background 2.",
            relevance_score=1.0,
            nli_label=NLILabel.NEUTRAL,
            nli_probs={"SUPPORT": 0.01, "CONTRADICT": 0.0, "NEUTRAL": 0.99},
        ),
    ]

    res_aware = doc_aware_agg.aggregate(passages)
    res_flat = flat_agg.aggregate(passages)

    # Document-aware pooling recognizes the document's support
    assert res_aware.dominant_label == NLILabel.SUPPORT
    assert res_aware.support_prob > 0.90

    # Flat passage averaging dilutes support to ~33%
    assert res_flat.dominant_label == NLILabel.NEUTRAL
    assert res_flat.support_prob < 0.40
