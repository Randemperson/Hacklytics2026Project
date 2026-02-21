"""
Tests for the HousingAI recommendation engine and supporting modules.
"""
import os
import sys
import pandas as pd
import pytest

# Ensure src is importable from the repo root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.housing_ai import HousingAI, LANGUAGE_ALIASES
from src.agent_caller import AgentCaller


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def ai():
    """HousingAI instance backed by the real dataset."""
    return HousingAI()


# ---------------------------------------------------------------------------
# HousingAI — data loading
# ---------------------------------------------------------------------------

class TestDataLoading:
    def test_dataframe_not_empty(self, ai):
        assert len(ai.df) > 0

    def test_required_columns_present(self, ai):
        expected = {
            "id", "address", "city", "state", "monthly_rent",
            "bedrooms", "agent_name", "agent_phone", "agent_email",
            "section8_accepted", "hud_approved", "low_income_eligible",
        }
        assert expected.issubset(set(ai.df.columns))

    def test_monthly_rent_numeric(self, ai):
        assert pd.api.types.is_numeric_dtype(ai.df["monthly_rent"])

    def test_boolean_columns_are_bool(self, ai):
        for col in ("section8_accepted", "hud_approved", "low_income_eligible"):
            assert ai.df[col].dtype == object or ai.df[col].dtype == bool  # parsed by _parse_bool


# ---------------------------------------------------------------------------
# HousingAI — search / filtering
# ---------------------------------------------------------------------------

class TestSearch:
    def test_search_no_filters_returns_results(self, ai):
        results = ai.search()
        assert len(results) > 0

    def test_search_max_rent(self, ai):
        results = ai.search(max_rent=750)
        assert all(results["monthly_rent"] <= 750)

    def test_search_min_bedrooms(self, ai):
        results = ai.search(min_bedrooms=2)
        assert all(results["bedrooms"] >= 2)

    def test_search_city(self, ai):
        results = ai.search(city="Atlanta")
        assert all(results["city"].str.lower() == "atlanta")

    def test_search_section8(self, ai):
        results = ai.search(section8=True)
        assert all(results["section8_accepted"])

    def test_search_language_spanish(self, ai):
        results = ai.search(language="Spanish")
        assert all(
            results["languages_spoken"].str.contains("Spanish", case=False, na=False)
        )

    def test_search_language_alias(self, ai):
        # "mandarin" should map to "Chinese"
        results_alias = ai.search(language="mandarin")
        results_direct = ai.search(language="Chinese")
        assert list(results_alias.index) == list(results_direct.index)

    def test_search_low_income(self, ai):
        results = ai.search(low_income_only=True)
        assert all(results["low_income_eligible"])

    def test_search_top_n(self, ai):
        results = ai.search(top_n=3)
        assert len(results) <= 3

    def test_search_no_match_returns_empty(self, ai):
        results = ai.search(max_rent=1, min_bedrooms=10)
        assert results.empty

    def test_search_results_sorted_by_score(self, ai):
        results = ai.search(top_n=10)
        scores = results["score"].tolist()
        assert scores == sorted(scores, reverse=True)

    def test_search_transit_filter(self, ai):
        results = ai.search(needs_transit=True)
        assert all(results["nearby_transit"])


# ---------------------------------------------------------------------------
# HousingAI — natural-language query parsing
# ---------------------------------------------------------------------------

class TestQueryParsing:
    def test_parse_max_rent(self, ai):
        params = ai.parse_query("I need an apartment under $800 per month")
        assert params.get("max_rent") == 800

    def test_parse_bedrooms(self, ai):
        params = ai.parse_query("looking for 2 bedroom apartment in Atlanta")
        assert params.get("min_bedrooms") == 2

    def test_parse_city(self, ai):
        params = ai.parse_query("find housing in Atlanta")
        assert params.get("city", "").lower() == "atlanta"

    def test_parse_section8(self, ai):
        params = ai.parse_query("section 8 housing")
        assert params.get("section8") is True

    def test_parse_low_income(self, ai):
        params = ai.parse_query("affordable low income housing")
        assert params.get("low_income_only") is True

    def test_parse_transit(self, ai):
        params = ai.parse_query("near MARTA transit")
        assert params.get("needs_transit") is True

    def test_parse_language(self, ai):
        params = ai.parse_query("Spanish speaking agent")
        assert params.get("language") == "Spanish"

    def test_parse_accessibility(self, ai):
        params = ai.parse_query("wheelchair accessible apartment")
        assert params.get("accessibility") is True


# ---------------------------------------------------------------------------
# HousingAI — answer_query integration
# ---------------------------------------------------------------------------

class TestAnswerQuery:
    def test_answer_query_returns_dict_keys(self, ai):
        result = ai.answer_query("affordable housing in Atlanta")
        assert "params" in result
        assert "results" in result
        assert "summary" in result

    def test_answer_query_summary_is_string(self, ai):
        result = ai.answer_query("2 bedroom under $900")
        assert isinstance(result["summary"], str)

    def test_answer_query_no_match_has_helpful_message(self, ai):
        # $100/mo budget with 10 bedrooms — impossible to match
        result = ai.answer_query("10 bedroom apartment under $100 per month in Atlanta")
        assert "sorry" in result["summary"].lower() or "couldn't" in result["summary"].lower()


# ---------------------------------------------------------------------------
# HousingAI — metadata helpers
# ---------------------------------------------------------------------------

class TestMetadata:
    def test_get_cities_returns_list(self, ai):
        cities = ai.get_cities()
        assert isinstance(cities, list)
        assert len(cities) > 0

    def test_get_languages_returns_list(self, ai):
        langs = ai.get_languages()
        assert isinstance(langs, list)
        assert "English" in langs

    def test_get_price_range(self, ai):
        lo, hi = ai.get_price_range()
        assert lo > 0
        assert hi >= lo


# ---------------------------------------------------------------------------
# AgentCaller — script / email generation (no network calls)
# ---------------------------------------------------------------------------

SAMPLE_LISTING = {
    "id": 1,
    "address": "123 Main St",
    "city": "Atlanta",
    "state": "GA",
    "monthly_rent": 750,
    "agent_name": "Maria Garcia",
    "agent_phone": "+14045550101",
    "agent_email": "maria@example.com",
}


class TestAgentCaller:
    def setup_method(self):
        self.caller = AgentCaller()

    def test_build_call_script_english(self):
        script = self.caller.build_call_script(
            SAMPLE_LISTING, "John Doe", "+15550001234", "English"
        )
        assert "John Doe" in script
        assert "123 Main St" in script
        assert "750" in script

    def test_build_call_script_spanish(self):
        script = self.caller.build_call_script(
            SAMPLE_LISTING, "Ana López", "+15550001234", "Spanish"
        )
        assert "Ana López" in script
        assert "Hola" in script

    def test_build_call_script_fallback_to_english(self):
        script = self.caller.build_call_script(
            SAMPLE_LISTING, "Test User", "+15550001234", "Klingon"
        )
        assert "Hello" in script

    def test_build_email_english(self):
        email = self.caller.build_email(
            SAMPLE_LISTING, "John Doe", "+15550001234", "john@example.com", "English"
        )
        assert "subject" in email
        assert "body" in email
        assert "John Doe" in email["body"]
        assert "Maria Garcia" in email["body"]

    def test_call_agent_no_credentials(self):
        result = self.caller.call_agent("+15550001234", "Hello")
        assert result["success"] is False
        assert "error" in result

    def test_send_email_no_credentials(self):
        result = self.caller.send_email(
            "agent@example.com", "Test Subject", "Test Body"
        )
        assert result["success"] is False
        assert "error" in result

    def test_contact_agent_email_no_credentials(self):
        result = self.caller.contact_agent_for_listing(
            SAMPLE_LISTING, "John Doe", "+15550001234",
            "john@example.com", "English", "email"
        )
        assert result["success"] is False

    def test_contact_agent_missing_email(self):
        listing_no_email = {**SAMPLE_LISTING, "agent_email": ""}
        result = self.caller.contact_agent_for_listing(
            listing_no_email, "John Doe", "+15550001234",
            method="email"
        )
        assert result["success"] is False


# ---------------------------------------------------------------------------
# LANGUAGE_ALIASES mapping
# ---------------------------------------------------------------------------

class TestLanguageAliases:
    def test_mandarin_maps_to_chinese(self):
        assert LANGUAGE_ALIASES["mandarin"] == "Chinese"

    def test_cantonese_maps_to_chinese(self):
        assert LANGUAGE_ALIASES["cantonese"] == "Chinese"

    def test_creole_maps_to_haitian_creole(self):
        assert LANGUAGE_ALIASES["creole"] == "Haitian Creole"
