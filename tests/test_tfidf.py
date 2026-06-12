"""Tests for TF-IDF retrieval index."""
import pytest
from mingrpg.retrieval.tfidf import TfidfIndex, _tokenize


class TestTokenize:
    def test_segments_chinese(self):
        tokens = _tokenize("凡殴打官员者杖一百")
        assert len(tokens) > 0
        # jieba should segment this into meaningful parts
        assert any("殴" in t or "打" in t or "官员" in t for t in tokens)

    def test_handles_empty_string(self):
        assert _tokenize("") == []

    def test_lowercases(self):
        tokens = _tokenize("ABC DEF")
        assert all(t == t.lower() for t in tokens)


class TestTfidfIndex:
    SAMPLE_DOCS = [
        {"id": "law.1", "text": "凡殴打官员者杖一百", "keywords": ["打", "殴", "官员"],
         "category": "斗殴"},
        {"id": "law.2", "text": "凡斗殴以手足殴人不成伤者笞二十", "keywords": ["打", "殴", "斗"],
         "category": "斗殴"},
        {"id": "law.3", "text": "凡窃盗已行而不得财者笞五十", "keywords": ["偷", "窃", "盗"],
         "category": "贼盗"},
        {"id": "law.4", "text": "凡谋杀人造意者斩", "keywords": ["杀", "谋杀"],
         "category": "杀人"},
    ]

    def test_returns_empty_for_no_docs(self):
        idx = TfidfIndex([])
        assert idx.query("打人") == []

    def test_finds_relevant_doc(self):
        idx = TfidfIndex(self.SAMPLE_DOCS)
        results = idx.query("殴打官员")
        assert len(results) > 0
        assert results[0]["id"] == "law.1"

    def test_differentiates_theft_from_violence(self):
        idx = TfidfIndex(self.SAMPLE_DOCS)
        r_theft = idx.query("偷窃财物")
        r_violence = idx.query("殴打斗殴")
        assert len(r_theft) > 0
        assert len(r_violence) > 0
        assert r_theft[0]["id"] == "law.3"
        assert r_violence[0]["id"] != "law.3"

    def test_respects_top_k(self):
        idx = TfidfIndex(self.SAMPLE_DOCS)
        results = idx.query("打", top_k=2)
        assert len(results) <= 2

    def test_score_is_between_0_and_1(self):
        idx = TfidfIndex(self.SAMPLE_DOCS)
        results = idx.query("殴打官员")
        for r in results:
            assert 0 < r["_score"] <= 1.0

    def test_handles_no_match(self):
        idx = TfidfIndex(self.SAMPLE_DOCS)
        results = idx.query("完全无关的内容xyz")
        assert len(results) == 0

    def test_index_includes_keywords_field(self):
        """Keywords field should be indexed for better recall."""
        idx = TfidfIndex(self.SAMPLE_DOCS)
        # "谋杀" is only in keywords of law.4, not in text
        results = idx.query("谋杀")
        ids = [r["id"] for r in results]
        assert "law.4" in ids

    def test_real_laws_data(self):
        """Integration test with actual law YAML files."""
        from pathlib import Path
        import yaml, os
        law_dir = Path(__file__).parent.parent / "data" / "laws"
        laws = []
        for fname in sorted(os.listdir(law_dir)):
            if fname.endswith(".yaml"):
                with open(law_dir / fname, encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                    if isinstance(data, list):
                        laws.extend(data)
        idx = TfidfIndex(laws)
        # Query about violence against officials
        results = idx.query("平民殴打知府")
        assert len(results) > 0
        top_ids = [r["id"] for r in results[:3]]
        assert any("殴" in lid or "斗殴" in lid for lid in top_ids)

        # Query about theft
        results = idx.query("偷东西被抓住了")
        assert len(results) > 0
        top_ids = [r["id"] for r in results[:3]]
        assert any("窃" in lid or "盗" in lid for lid in top_ids)
