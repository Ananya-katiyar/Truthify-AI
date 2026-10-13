"""
Internet Fact-Checking & Live Trusted Source Retrieval Engine.

Dynamically searches verified, trusted internet sources (Reuters Fact Check,
AP Fact Check, WHO, CDC, Snopes, FactCheck.org, Wikipedia, etc.) in real-time
without relying on hardcoded facts.

Features:
- Live DuckDuckGo search targeting certified fact-checking and authoritative domains.
- Live Wikipedia REST API search for neutral, encyclopedic knowledge grounding.
- Google Fact Check Tools API integration (if GOOGLE_FACTCHECK_API_KEY is provided).
- Stance analysis (refutes, supports, disputed, unverified).
- Trust score and provenance attribution for every piece of evidence.
- Dynamic persistence cache for verified facts.
"""

import json
import logging
import os
import re
import urllib.parse
from html import unescape
from pathlib import Path
from typing import Optional

import httpx

try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False

logger = logging.getLogger(__name__)

CACHE_DIR = Path(__file__).resolve().parent.parent / "data" / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)
CACHE_FILE = CACHE_DIR / "internet_facts_cache.json"

# Directory of trusted domains with categories and reputation scores
TRUSTED_DOMAINS = {
    # Fact-checking organizations (IFCN certified / reputable)
    "reuters.com": {"name": "Reuters News & Fact Check", "category": "news_agency", "trust": 0.98},
    "apnews.com": {"name": "Associated Press (AP) Fact Check", "category": "news_agency", "trust": 0.98},
    "factcheck.org": {"name": "FactCheck.org (Annenberg Public Policy)", "category": "fact_checker", "trust": 0.96},
    "snopes.com": {"name": "Snopes Fact Check", "category": "fact_checker", "trust": 0.95},
    "politifact.com": {"name": "PolitiFact (Poynter)", "category": "fact_checker", "trust": 0.95},
    "fullfact.org": {"name": "Full Fact (UK)", "category": "fact_checker", "trust": 0.95},
    "afp.com": {"name": "Agence France-Presse (AFP)", "category": "news_agency", "trust": 0.96},
    "leadstories.com": {"name": "Lead Stories", "category": "fact_checker", "trust": 0.93},
    "healthfeedback.org": {"name": "Health Feedback (Science Feedback)", "category": "fact_checker", "trust": 0.97},
    "climatefeedback.org": {"name": "Climate Feedback", "category": "fact_checker", "trust": 0.97},

    # Health & Science Authorities
    "who.int": {"name": "World Health Organization (WHO)", "category": "health_authority", "trust": 0.99},
    "cdc.gov": {"name": "Centers for Disease Control and Prevention (CDC)", "category": "health_authority", "trust": 0.99},
    "nih.gov": {"name": "National Institutes of Health (NIH)", "category": "scientific_authority", "trust": 0.99},
    "fda.gov": {"name": "U.S. Food and Drug Administration (FDA)", "category": "government_authority", "trust": 0.98},
    "nature.com": {"name": "Nature Scientific Journal", "category": "peer_reviewed", "trust": 0.99},
    "science.org": {"name": "Science / AAAS", "category": "peer_reviewed", "trust": 0.99},
    "thelancet.com": {"name": "The Lancet", "category": "peer_reviewed", "trust": 0.99},
    "nasa.gov": {"name": "NASA", "category": "scientific_authority", "trust": 0.99},
    "un.org": {"name": "United Nations (UN)", "category": "international_org", "trust": 0.97},

    # Major News Agencies
    "bbc.com": {"name": "BBC News & Reality Check", "category": "news_agency", "trust": 0.94},
    "bbc.co.uk": {"name": "BBC News", "category": "news_agency", "trust": 0.94},
    "theguardian.com": {"name": "The Guardian", "category": "news_publisher", "trust": 0.90},
    "nytimes.com": {"name": "The New York Times", "category": "news_publisher", "trust": 0.91},
    "washingtonpost.com": {"name": "The Washington Post Fact Checker", "category": "news_publisher", "trust": 0.92},

    # Collaborative Encyclopedia
    "wikipedia.org": {"name": "Wikipedia Encyclopedia", "category": "encyclopedia", "trust": 0.88},
    "en.wikipedia.org": {"name": "Wikipedia Encyclopedia", "category": "encyclopedia", "trust": 0.88},
}

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


def _load_cache() -> dict:
    """Load cached internet verification results."""
    if CACHE_FILE.exists():
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def _save_cache(cache: dict) -> None:
    """Save verification cache to disk."""
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.warning(f"Could not persist internet search cache: {e}")


def identify_source_info(url: str) -> dict:
    """Identify reputation and metadata for a given URL domain."""
    domain_match = re.search(r"https?://(?:www\.)?([^/]+)", url)
    if not domain_match:
        return {"name": "Web Source", "domain": "unknown", "trust": 0.60, "category": "general", "is_trusted": False}

    raw_domain = domain_match.group(1).lower()

    # Direct match or subdomain check
    for trusted_domain, info in TRUSTED_DOMAINS.items():
        if raw_domain == trusted_domain or raw_domain.endswith("." + trusted_domain):
            return {
                "name": info["name"],
                "domain": raw_domain,
                "trust": info["trust"],
                "category": info["category"],
                "is_trusted": True,
            }

    # Government / Educational TLDs
    if raw_domain.endswith(".gov"):
        return {"name": f"Government Official ({raw_domain})", "domain": raw_domain, "trust": 0.95, "category": "government_authority", "is_trusted": True}
    if raw_domain.endswith(".edu"):
        return {"name": f"Academic Institution ({raw_domain})", "domain": raw_domain, "trust": 0.92, "category": "academic", "is_trusted": True}

    return {"name": raw_domain.title(), "domain": raw_domain, "trust": 0.65, "category": "general_web", "is_trusted": False}


def search_duckduckgo_live(query: str, max_results: int = 6) -> list[dict]:
    """
    Query DuckDuckGo live to find real-time web coverage and fact checks.
    Uses html.duckduckgo.com and lite.duckduckgo.com fallbacks.
    """
    clean_q = re.sub(r"[^\w\s-]", " ", query).strip()
    if not clean_q:
        return []

    search_query = f"{clean_q} fact check"
    results = []

    # Attempt 1: html.duckduckgo.com
    try:
        headers = dict(_HEADERS)
        headers["Referer"] = "https://duckduckgo.com/"
        with httpx.Client(timeout=10.0, follow_redirects=True, headers=headers) as client:
            resp = client.get("https://html.duckduckgo.com/html/", params={"q": search_query})
            if resp.status_code == 200 and HAS_BS4:
                soup = BeautifulSoup(resp.text, "html.parser")
                result_divs = soup.find_all("div", class_="result")
                for div in result_divs:
                    a_title = div.find("a", class_="result__a")
                    snippet_el = div.find("a", class_="result__snippet")
                    if not a_title:
                        continue

                    raw_href = a_title.get("href", "")
                    if "uddg=" in raw_href:
                        url = urllib.parse.unquote(raw_href.split("uddg=")[1].split("&")[0])
                    else:
                        url = raw_href

                    title = a_title.get_text(strip=True)
                    snip = snippet_el.get_text(strip=True) if snippet_el else ""

                    if not url.startswith("http"):
                        continue

                    source_meta = identify_source_info(url)
                    results.append({
                        "title": title,
                        "url": url,
                        "domain": source_meta["domain"],
                        "source_name": source_meta["name"],
                        "trust_score": source_meta["trust"],
                        "category": source_meta["category"],
                        "is_trusted": source_meta["is_trusted"],
                        "snippet": snip,
                    })
    except Exception as e:
        logger.warning(f"html.duckduckgo.com search attempt error: {e}")

    # Fallback attempt 2: lite.duckduckgo.com if no results
    if not results:
        try:
            with httpx.Client(timeout=10.0, follow_redirects=True, headers=_HEADERS) as client:
                resp = client.post("https://lite.duckduckgo.com/lite/", data={"q": search_query})
                if resp.status_code == 200 and HAS_BS4:
                    soup = BeautifulSoup(resp.text, "html.parser")
                    links = soup.find_all("a", class_="result-link")
                    snippets = soup.find_all("td", class_="result-snippet")
                    for a, td in zip(links, snippets):
                        url = a.get("href", "")
                        raw_title = a.get_text(strip=True)
                        raw_snip = td.get_text(strip=True)
                        if "uddg=" in url:
                            match = re.search(r"uddg=([^&]+)", url)
                            if match:
                                url = urllib.parse.unquote(match.group(1))

                        source_meta = identify_source_info(url)
                        results.append({
                            "title": raw_title,
                            "url": url,
                            "domain": source_meta["domain"],
                            "source_name": source_meta["name"],
                            "trust_score": source_meta["trust"],
                            "category": source_meta["category"],
                            "is_trusted": source_meta["is_trusted"],
                            "snippet": raw_snip,
                        })
        except Exception as e:
            logger.error(f"Lite DDG search fallback error: {e}")

    # Sort results: trusted sources first, then highest trust score
    results.sort(key=lambda x: (x["is_trusted"], x["trust_score"]), reverse=True)
    return results[:max_results]


def search_wikipedia_live(query: str, max_results: int = 2) -> list[dict]:
    """
    Search Wikipedia live via its official REST API for authoritative encyclopedic facts.
    """
    clean_q = re.sub(r"[^\w\s-]", " ", query).strip()
    if not clean_q:
        return []

    wiki_headers = {
        "User-Agent": "TruthifyAI-FactChecker/1.0 (https://truthify.ai; contact@truthify.ai)"
    }
    results = []

    try:
        with httpx.Client(timeout=8.0, headers=wiki_headers) as client:
            # Step 1: Search Wikipedia titles
            resp = client.get(
                "https://en.wikipedia.org/w/api.php",
                params={
                    "action": "query",
                    "list": "search",
                    "srsearch": clean_q,
                    "format": "json",
                    "srlimit": max_results,
                }
            )
            if resp.status_code != 200:
                return []

            data = resp.json()
            search_items = data.get("query", {}).get("search", [])

            for item in search_items:
                title = item.get("title", "")
                if not title:
                    continue

                # Step 2: Fetch clean summary extract
                summary_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(title.replace(' ', '_'))}"
                sum_resp = client.get(summary_url)
                if sum_resp.status_code == 200:
                    sum_data = sum_resp.json()
                    extract = sum_data.get("extract", "")
                    page_url = sum_data.get("content_urls", {}).get("desktop", {}).get("page", f"https://en.wikipedia.org/wiki/{title}")

                    if extract:
                        results.append({
                            "title": f"Wikipedia: {title}",
                            "url": page_url,
                            "domain": "en.wikipedia.org",
                            "source_name": "Wikipedia Encyclopedia",
                            "trust_score": 0.88,
                            "category": "encyclopedia",
                            "is_trusted": True,
                            "snippet": extract[:350] + ("..." if len(extract) > 350 else ""),
                        })
    except Exception as e:
        logger.warning(f"Wikipedia live query error: {e}")

    return results


def search_google_factcheck(query: str) -> list[dict]:
    """
    Query Google Fact Check Tools API if GOOGLE_FACTCHECK_API_KEY is configured.
    """
    api_key = os.getenv("GOOGLE_FACTCHECK_API_KEY")
    if not api_key:
        return []

    results = []
    try:
        with httpx.Client(timeout=8.0) as client:
            resp = client.get(
                "https://factchecktools.googleapis.com/v1alpha1/claims:search",
                params={"query": query, "key": api_key, "languageCode": "en"}
            )
            if resp.status_code == 200:
                data = resp.json()
                claims = data.get("claims", [])
                for c in claims[:3]:
                    claim_text = c.get("text", "")
                    claimant = c.get("claimant", "")
                    reviews = c.get("claimReview", [])
                    for r in reviews:
                        publisher = r.get("publisher", {}).get("name", "Fact Checker")
                        site = r.get("publisher", {}).get("site", "")
                        rating = r.get("textualRating", "Unrated")
                        url = r.get("url", "")
                        title = r.get("title", "")
                        results.append({
                            "title": title or f"{publisher} Fact Check: {claim_text[:60]}",
                            "url": url,
                            "domain": site or "factchecktools.googleapis.com",
                            "source_name": f"{publisher} ({rating})",
                            "trust_score": 0.98,
                            "category": "fact_checker",
                            "is_trusted": True,
                            "snippet": f"Claim by {claimant or 'Source'}: '{claim_text}'. Rated as '{rating}' by {publisher}.",
                            "verdict_rating": rating,
                        })
    except Exception as e:
        logger.warning(f"Google Fact Check API query failed: {e}")
    return results


def analyze_evidence_stance(claim: str, snippet: str, title: str = "") -> dict:
    """
    Analyzes whether the retrieved internet evidence refutes, supports, or disputes the claim.
    """
    combined_text = f"{title} {snippet}".lower()
    claim_lower = claim.lower()

    refuting_cues = [
        "false", "myth", "debunked", "hoax", "fake", "incorrect", "untrue",
        "no evidence", "disproven", "refuted", "misleading", "fraud", "scam",
        "not true", "bogus", "conspiracy", "fabricat", "retracted", "pseudoscience"
    ]
    supporting_cues = [
        "confirmed", "verified", "true", "accurate", "official data", "official statistics",
        "demonstrated", "evidence shows", "proven", "authentic", "corroborat"
    ]
    disputed_cues = [
        "partially", "unclear", "mixed", "disputed", "missing context", "debated",
        "unsubstantiated", "unconfirmed", "alleged"
    ]

    refute_matches = [w for w in refuting_cues if w in combined_text]
    support_matches = [w for w in supporting_cues if w in combined_text]
    dispute_matches = [w for w in disputed_cues if w in combined_text]

    # Stance classification
    if refute_matches and (len(refute_matches) >= len(support_matches)):
        stance = "refutes"
        stance_desc = f"Evidence directly debunks or refutes this claim (signals: {', '.join(refute_matches[:2])})."
    elif support_matches and not refute_matches:
        stance = "supports"
        stance_desc = f"Evidence supports or verifies this statement (signals: {', '.join(support_matches[:2])})."
    elif dispute_matches or (refute_matches and support_matches):
        stance = "disputed_or_context"
        stance_desc = "Evidence indicates the claim is disputed, partially true, or lacks critical context."
    else:
        stance = "contextual_mention"
        stance_desc = "Evidence discusses this topic without an explicit true/false verdict."

    return {
        "stance": stance,
        "stance_description": stance_desc,
        "refute_signals": refute_matches,
        "support_signals": support_matches,
    }


def verify_claim_against_internet(claim: str) -> dict:
    """
    Main verification pipeline for a single claim:
    1. Checks local cache for recent verification.
    2. Queries Google Fact Check Tools API (if key available).
    3. Queries live DuckDuckGo for certified fact-checks and authoritative reporting.
    4. Queries Wikipedia REST API for encyclopedic grounding.
    5. Determines overall verdict and stance across sources.
    6. Caches result.
    """
    clean_claim = claim.strip()
    if not clean_claim:
        return {
            "claim": claim,
            "verdict": "empty_claim",
            "top_similarity": 0.0,
            "evidence": [],
            "source": None,
        }

    # Check cache
    cache = _load_cache()
    norm_key = re.sub(r"\W+", "_", clean_claim.lower())[:80]
    if norm_key in cache:
        logger.info(f"Using cached internet verification for: '{clean_claim[:50]}'")
        return cache[norm_key]

    evidence_list = []

    # 1. Google Fact Check Tools
    g_results = search_google_factcheck(clean_claim)
    evidence_list.extend(g_results)

    # 2. Live DDG (targeting fact checkers & authorities)
    ddg_results = search_duckduckgo_live(clean_claim, max_results=5)
    evidence_list.extend(ddg_results)

    # 3. Live Wikipedia
    wiki_results = search_wikipedia_live(clean_claim, max_results=2)
    evidence_list.extend(wiki_results)

    # Deduplicate by URL
    seen_urls = set()
    unique_evidence = []
    for item in evidence_list:
        url = item.get("url")
        if url and url not in seen_urls:
            seen_urls.add(url)
            # Annotate stance
            stance_info = analyze_evidence_stance(clean_claim, item.get("snippet", ""), item.get("title", ""))
            item["stance"] = stance_info["stance"]
            item["stance_description"] = stance_info["stance_description"]
            unique_evidence.append(item)

    if not unique_evidence:
        res = {
            "claim": clean_claim,
            "verdict": "no_verified_evidence",
            "top_similarity": 0.0,
            "confidence": 0.30,
            "evidence": [],
            "source": None,
            "explanation": "No matching reporting found on trusted internet sources or certified fact-check archives.",
        }
        return res

    # Compute verdict based on trusted evidence stances
    refuting_count = sum(1 for e in unique_evidence if e["stance"] == "refutes")
    supporting_count = sum(1 for e in unique_evidence if e["stance"] == "supports")
    trusted_count = sum(1 for e in unique_evidence if e.get("is_trusted", False))

    top_evidence = unique_evidence[0]
    top_source = top_evidence.get("source_name", "Internet Source")

    if refuting_count > 0:
        verdict = "debunked_as_false"
        confidence = 0.92 if trusted_count > 0 else 0.75
        explanation = f"Trusted fact-check sources ({top_source}) directly refute this claim."
    elif supporting_count > 0 and refuting_count == 0:
        verdict = "confirmed_true"
        confidence = 0.90 if trusted_count > 0 else 0.70
        explanation = f"Authoritative sources ({top_source}) confirm this factual statement."
    elif any(e["stance"] == "disputed_or_context" for e in unique_evidence):
        verdict = "disputed_or_misleading"
        confidence = 0.75
        explanation = "Trusted reports indicate this claim is disputed or missing critical context."
    else:
        verdict = "context_found_unverified"
        confidence = 0.60
        explanation = f"Found related background on {top_source}, but no definitive debunk or confirmation."

    result = {
        "claim": clean_claim,
        "verdict": verdict,
        "confidence": confidence,
        "top_similarity": top_evidence.get("trust_score", 0.80),
        "source": top_source,
        "top_url": top_evidence.get("url", ""),
        "explanation": explanation,
        "evidence": unique_evidence[:5],
    }

    # Save to local cache
    cache[norm_key] = result
    _save_cache(cache)

    return result


def verify_claims_live(claims: list[str]) -> list[dict]:
    """Verify multiple extracted claims against live internet sources."""
    results = []
    for claim in claims:
        res = verify_claim_against_internet(claim)
        results.append(res)
    return results


if __name__ == "__main__":
    test_claim = "The MMR vaccine causes autism in children"
    print(f"Testing claim: {test_claim}")
    verdict = verify_claim_against_internet(test_claim)
    print(json.dumps(verdict, indent=2))
