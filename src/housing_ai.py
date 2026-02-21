"""
Housing AI Recommendation Engine
Helps immigrants and minorities find low-cost housing by analyzing a dataset
and scoring/filtering properties based on user preferences.
"""
import os
import pandas as pd
import numpy as np
from pathlib import Path

# Path to the dataset relative to this file's location
DATA_PATH = Path(__file__).parent.parent / "data" / "housing_data.csv"

# Language aliases so users can type variations
LANGUAGE_ALIASES = {
    "english": "English",
    "spanish": "Spanish",
    "spanish/latin": "Spanish",
    "chinese": "Chinese",
    "mandarin": "Chinese",
    "cantonese": "Chinese",
    "korean": "Korean",
    "vietnamese": "Vietnamese",
    "arabic": "Arabic",
    "hindi": "Hindi",
    "gujarati": "Gujarati",
    "french": "French",
    "amharic": "Amharic",
    "somali": "Somali",
    "haitian creole": "Haitian Creole",
    "creole": "Haitian Creole",
    "russian": "Russian",
}


class HousingAI:
    """AI-powered housing recommendation engine focused on affordability
    and accessibility for immigrants and minority communities."""

    def __init__(self, data_path: str = None):
        self.data_path = data_path or str(DATA_PATH)
        self.df = self._load_data()

    # ------------------------------------------------------------------
    # Data loading
    # ------------------------------------------------------------------

    def _load_data(self) -> pd.DataFrame:
        """Load and preprocess the housing dataset."""
        df = pd.read_csv(self.data_path)
        # Normalise boolean columns that may be stored as strings
        for col in ("section8_accepted", "hud_approved", "low_income_eligible",
                    "nearby_transit", "utilities_included", "pets_allowed"):
            if col in df.columns:
                df[col] = df[col].apply(self._parse_bool)
        df["monthly_rent"] = pd.to_numeric(df["monthly_rent"], errors="coerce")
        df["bedrooms"] = pd.to_numeric(df["bedrooms"], errors="coerce").fillna(0).astype(int)
        return df

    @staticmethod
    def _parse_bool(value) -> bool:
        if value is None:
            return False
        if isinstance(value, float) and np.isnan(value):
            return False
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.strip().lower() in ("yes", "true", "1")
        return bool(value)

    # ------------------------------------------------------------------
    # Core search / recommendation
    # ------------------------------------------------------------------

    def search(
        self,
        max_rent: float = None,
        min_bedrooms: int = 0,
        city: str = None,
        state: str = None,
        zip_code: str = None,
        language: str = None,
        section8: bool = False,
        hud_approved: bool = False,
        low_income_only: bool = False,
        needs_transit: bool = False,
        pets_allowed: bool = False,
        accessibility: bool = False,
        ami_percent: int = None,
        top_n: int = 10,
    ) -> pd.DataFrame:
        """Return the top-N housing options matching the given criteria,
        ranked by a composite affordability + accessibility score."""
        results = self.df.copy()

        # --- Hard filters ---
        if max_rent is not None:
            results = results[results["monthly_rent"] <= max_rent]
        if min_bedrooms:
            results = results[results["bedrooms"] >= min_bedrooms]
        if city:
            results = results[
                results["city"].str.lower() == city.strip().lower()
            ]
        if state:
            results = results[
                results["state"].str.upper() == state.strip().upper()
            ]
        if zip_code:
            results = results[results["zip_code"].astype(str) == str(zip_code).strip()]
        if section8:
            results = results[results["section8_accepted"]]
        if hud_approved:
            results = results[results["hud_approved"]]
        if low_income_only:
            results = results[results["low_income_eligible"]]
        if needs_transit:
            results = results[results["nearby_transit"]]
        if pets_allowed:
            results = results[results["pets_allowed"]]
        if accessibility:
            results = results[
                results["accessibility_features"].notna()
                & (results["accessibility_features"].str.strip() != "None")
                & (results["accessibility_features"].str.strip() != "")
            ]
        if ami_percent is not None:
            results = results[results["income_limit_percent_ami"] <= ami_percent]

        # --- Language filter ---
        if language:
            normalised = LANGUAGE_ALIASES.get(language.lower(), language)
            results = results[
                results["languages_spoken"].str.contains(
                    normalised, case=False, na=False
                )
            ]

        if results.empty:
            return results

        # --- Scoring ---
        results = results.copy()
        results["score"] = results.apply(self._score_listing, axis=1)
        results = results.sort_values("score", ascending=False)

        return results.head(top_n)

    @staticmethod
    def _score_listing(row) -> float:
        """Compute a composite score (higher = better) for a listing."""
        score = 0.0

        # Affordability: reward lower rents on a 0-40 scale
        try:
            rent = float(row["monthly_rent"])
            score += max(0, 40 - (rent / 30))  # $1,200 rent → 0 pts
        except (TypeError, ValueError):
            pass

        # Bonus for low-income eligibility
        if row.get("low_income_eligible"):
            score += 15
        # Bonus for Section 8 acceptance
        if row.get("section8_accepted"):
            score += 10
        # Bonus for HUD approval
        if row.get("hud_approved"):
            score += 10
        # Bonus for transit access
        if row.get("nearby_transit"):
            score += 5
        # Bonus for utilities included
        if row.get("utilities_included") not in (None, "", "None", False, np.nan):
            score += 5
        # Bonus for accessibility features
        accessibility = row.get("accessibility_features", "")
        if accessibility and str(accessibility).strip() not in ("None", ""):
            score += 5

        return round(score, 2)

    # ------------------------------------------------------------------
    # Natural language query parsing
    # ------------------------------------------------------------------

    def parse_query(self, query: str) -> dict:
        """Extract search parameters from a free-text or spoken query.

        Returns a dict of keyword arguments suitable for ``search()``.
        """
        import re

        q = query.lower()
        params: dict = {}

        # Budget / rent
        rent_match = re.search(
            r"\$?\b(\d{3,4})\b.*?(rent|month|budget|afford|per month)?", q
        )
        if rent_match:
            params["max_rent"] = int(rent_match.group(1))

        # Bedrooms
        bed_match = re.search(r"(\d)\s*(?:bed(?:room)?s?|br\b)", q)
        if bed_match:
            params["min_bedrooms"] = int(bed_match.group(1))

        # City — check known cities in dataset
        cities = ["atlanta", "decatur", "norcross", "chamblee", "sandy springs",
                  "college park", "brookhaven", "jonesboro"]
        for city in cities:
            if city in q:
                params["city"] = city.title()
                break

        # State
        if " ga " in q or "georgia" in q or q.endswith(" ga"):
            params["state"] = "GA"

        # Section 8
        if "section 8" in q or "section8" in q or "voucher" in q:
            params["section8"] = True

        # HUD
        if "hud" in q:
            params["hud_approved"] = True

        # Low income / affordable
        if any(w in q for w in ("low income", "low-income", "affordable",
                                "cheap", "subsidized")):
            params["low_income_only"] = True

        # Transit
        if any(w in q for w in ("transit", "bus", "marta", "train", "public transport")):
            params["needs_transit"] = True

        # Pets
        if "pet" in q or "dog" in q or "cat" in q:
            params["pets_allowed"] = True

        # Accessibility
        if any(w in q for w in ("wheelchair", "accessible", "accessibility",
                                "disability", "disabled")):
            params["accessibility"] = True

        # Language
        for alias, canonical in LANGUAGE_ALIASES.items():
            if alias in q:
                params["language"] = canonical
                break

        return params

    def answer_query(self, query: str, top_n: int = 5) -> dict:
        """Parse a natural-language query and return matching listings
        plus a human-readable summary string."""
        params = self.parse_query(query)
        params["top_n"] = top_n
        results = self.search(**params)

        if results.empty:
            summary = (
                "I'm sorry, I couldn't find any listings that match your criteria. "
                "Try broadening your search — for example, increase your budget or "
                "expand to nearby cities."
            )
        else:
            lines = [
                f"I found {len(results)} listing(s) that match your needs:\n"
            ]
            for _, row in results.iterrows():
                lines.append(
                    f"• {row['address']}, {row['city']}, {row['state']} "
                    f"— ${row['monthly_rent']:,.0f}/mo | "
                    f"{int(row['bedrooms'])} bed | "
                    f"Section 8: {'✓' if row['section8_accepted'] else '✗'} | "
                    f"Agent: {row['agent_name']} ({row['agent_phone']})"
                )
            summary = "\n".join(lines)

        return {"params": params, "results": results, "summary": summary}

    # ------------------------------------------------------------------
    # Dataset utilities
    # ------------------------------------------------------------------

    def get_cities(self) -> list:
        return sorted(self.df["city"].dropna().unique().tolist())

    def get_languages(self) -> list:
        langs: set = set()
        for cell in self.df["languages_spoken"].dropna():
            for lang in cell.split(","):
                langs.add(lang.strip())
        return sorted(langs)

    def get_price_range(self) -> tuple:
        rents = self.df["monthly_rent"].dropna()
        return float(rents.min()), float(rents.max())
