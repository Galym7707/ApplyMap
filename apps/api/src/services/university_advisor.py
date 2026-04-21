import json
import re
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any
from urllib.parse import urlparse

import httpx

from ..config import settings
from .chancellor_analysis import ADMISSIONS_FRAMEWORK
from .counselor_knowledge import CHANCELLOR_COUNSELOR_FRAMEWORK


ADVISOR_SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {"type": "string"},
        "exams_to_prioritize": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "exam": {"type": "string"},
                    "why": {"type": "string"},
                    "priority": {"type": "string", "enum": ["high", "medium", "low"]},
                },
                "required": ["exam", "why", "priority"],
            },
        },
        "profile_actions": {
            "type": "array",
            "items": {"type": "string"},
        },
        "low_value_activities": {
            "type": "array",
            "items": {"type": "string"},
        },
        "research_or_summer_programs": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "why_it_helps": {"type": "string"},
                    "source_url": {"type": "string"},
                },
                "required": ["name", "why_it_helps"],
            },
        },
        "source_notes": {
            "type": "array",
            "items": {"type": "string"},
        },
    },
    "required": [
        "summary",
        "exams_to_prioritize",
        "profile_actions",
        "low_value_activities",
        "research_or_summer_programs",
        "source_notes",
    ],
}

SEARCH_TIME_BUDGET_SECONDS = 22.0

KAZAKHSTAN_FINAL_CREDENTIAL_PHRASES = (
    "nis grade 12 certificate",
    "grade 12 certificate",
    "mesk",
    "мэск",
    "нзм 12",
    "ниc grade 12",
    "certificate gpa",
)

KAZAKHSTAN_FINAL_CREDENTIAL_PATTERNS = (
    r"\bunt\b",
    r"\bent\b",
    r"\bент\b",
    r"\bұбт\b",
)

US_TARGET_NAME_HINTS = (
    "common app",
    "harvard",
    "stanford",
    "mit",
    "massachusetts institute of technology",
    "yale",
    "princeton",
    "columbia",
    "brown",
    "cornell",
    "dartmouth",
    "university of pennsylvania",
    "upenn",
    "duke",
    "northwestern",
    "uchicago",
    "university of chicago",
    "vanderbilt",
    "rice",
    "washington university in st. louis",
    "washu",
    "university of california",
    "caltech",
    "california institute of technology",
)


class SearchNotConfiguredError(RuntimeError):
    pass


def _compact(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def _google_search(query: str, *, num: int = 5) -> list[dict[str, str]]:
    api_key = settings.GOOGLE_SEARCH_API_KEY.strip()
    engine_id = settings.GOOGLE_SEARCH_ENGINE_ID.strip()
    if not api_key or not engine_id:
        raise SearchNotConfiguredError("Google Custom Search is not configured")

    with httpx.Client(timeout=8.0) as client:
        response = client.get(
            "https://www.googleapis.com/customsearch/v1",
            params={
                "key": api_key,
                "cx": engine_id,
                "q": query,
                "num": num,
                "safe": "active",
                "hl": "en",
            },
        )
        response.raise_for_status()

    items = response.json().get("items") or []
    return [
        {
            "title": str(item.get("title") or ""),
            "url": str(item.get("link") or ""),
            "snippet": str(item.get("snippet") or ""),
        }
        for item in items
        if item.get("link")
    ]


def _resolve_redirect_url(url: str) -> str:
    if not url:
        return ""
    host = urlparse(url).netloc.lower()
    if "vertexaisearch.cloud.google.com" not in host:
        return url

    try:
        with httpx.Client(timeout=3.0, follow_redirects=True) as client:
            response = client.head(url)
            if response.status_code >= 400 or str(response.url) == url:
                response = client.get(url)
            return str(response.url)
    except httpx.HTTPError:
        return url


def _gemini_grounded_search(query: str, *, num: int = 5) -> list[dict[str, str]]:
    api_key = settings.GEMINI_API_KEY.strip()
    if not api_key:
        raise SearchNotConfiguredError("Gemini Search grounding is not configured")

    model = (settings.GEMINI_MODEL or "gemini-2.5-flash").strip()
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    request_payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": (
                            "Find current official source pages for this university admissions query. "
                            "Prefer official university admissions, financial aid, program, and summer/research pages. "
                            "Return a concise source-backed answer.\n\n"
                            f"Query: {query}"
                        )
                    }
                ]
            }
        ],
        "tools": [{"google_search": {}}],
        "generationConfig": {"temperature": 0.0},
    }

    with httpx.Client(timeout=16.0) as client:
        response = client.post(
            url,
            headers={"x-goog-api-key": api_key, "Content-Type": "application/json"},
            json=request_payload,
        )
        response.raise_for_status()

    payload = response.json()
    candidates = payload.get("candidates") or []
    candidate = candidates[0] if candidates else {}
    parts = (candidate.get("content") or {}).get("parts") or []
    answer_text = _compact(str(parts[0].get("text") or "")) if parts else ""
    chunks = (candidate.get("groundingMetadata") or {}).get("groundingChunks") or []

    raw_results: list[tuple[str, str]] = []
    for chunk in chunks:
        web = chunk.get("web") or {}
        raw_url = str(web.get("uri") or "")
        raw_title = _compact(str(web.get("title") or ""))
        if raw_url:
            raw_results.append((raw_title, raw_url))
        if len(raw_results) >= num:
            break

    if not raw_results:
        return []

    with ThreadPoolExecutor(max_workers=min(6, len(raw_results))) as executor:
        resolved_urls = list(executor.map(_resolve_redirect_url, [item[1] for item in raw_results]))

    results: list[dict[str, str]] = []
    seen: set[str] = set()
    for (raw_title, _), resolved_url in zip(raw_results, resolved_urls):
        if not resolved_url or resolved_url in seen:
            continue
        seen.add(resolved_url)
        results.append(
            {
                "title": raw_title or urlparse(resolved_url).netloc,
                "url": resolved_url,
                "snippet": answer_text[:320],
            }
        )
    return results


def _search_web(query: str, *, num: int = 5) -> list[dict[str, str]]:
    google_error: Exception | None = None
    try:
        google_results = _google_search(query, num=num)
        if google_results:
            return google_results
    except (SearchNotConfiguredError, httpx.HTTPError) as exc:
        google_error = exc

    try:
        return _gemini_grounded_search(query, num=num)
    except (SearchNotConfiguredError, httpx.HTTPError):
        if isinstance(google_error, SearchNotConfiguredError):
            raise google_error
        return []


def _source_tier(url: str, university_name: str, title: str = "") -> str:
    host = urlparse(url).netloc.lower()
    source_text = f"{host} {title}".lower()
    name_tokens = [token for token in university_name.lower().replace("-", " ").split() if len(token) > 3]
    has_name_token = any(token in source_text for token in name_tokens)
    if has_name_token and (".edu" in host or ".ac." in host or host.endswith(".edu")):
        return "official"
    if ".edu" in host or ".ac." in host:
        return "education_domain"
    return "third_party"


def _target_region(university_name: str, search_results: list[dict[str, str]]) -> str:
    text = " ".join(
        [
            university_name,
            *[item.get("url", "") for item in search_results],
            *[item.get("title", "") for item in search_results],
        ]
    ).lower()
    hosts = [urlparse(item.get("url", "")).netloc.lower() for item in search_results]
    if "hong kong" in text or any(host.endswith(".hk") for host in hosts):
        return "hong_kong"
    if "korea" in text or any(host.endswith(".kr") for host in hosts):
        return "korea"
    if "japan" in text or any(host.endswith(".jp") for host in hosts):
        return "japan"
    if any(hint in text for hint in US_TARGET_NAME_HINTS):
        return "us"
    if any(host.endswith(".edu") for host in hosts):
        return "us"
    return "unknown"


def _is_kazakhstan_final_credential(exam_name: str) -> bool:
    normalized = exam_name.lower()
    return any(term in normalized for term in KAZAKHSTAN_FINAL_CREDENTIAL_PHRASES) or any(
        re.search(pattern, normalized) for pattern in KAZAKHSTAN_FINAL_CREDENTIAL_PATTERNS
    )


def _append_unique(values: list[str], item: str) -> None:
    if item not in values:
        values.append(item)


def _sanitize_application_timeline(
    plan: dict[str, Any],
    *,
    university_name: str,
    search_results: list[dict[str, str]],
) -> dict[str, Any]:
    region = _target_region(university_name, search_results)
    plan.setdefault("exams_to_prioritize", [])
    plan.setdefault("profile_actions", [])
    plan.setdefault("source_notes", [])

    if region == "us":
        filtered_exams = []
        removed_credentials: list[str] = []
        for item in plan.get("exams_to_prioritize", []):
            exam_name = str(item.get("exam") or "")
            if _is_kazakhstan_final_credential(exam_name):
                removed_credentials.append(exam_name)
                continue
            filtered_exams.append(item)
        plan["exams_to_prioritize"] = filtered_exams

        if removed_credentials:
            _append_unique(
                plan["profile_actions"],
                (
                    "For U.S. fall applications, do not rely on final UNT/ENT or final NIS Grade 12 Certificate/MESK "
                    "results as application-stage exams unless the target's official source explicitly allows that "
                    "for the relevant deadline. Use school transcripts, current Grade 12 coursework, school profile, "
                    "recommendations, and required standardized tests."
                ),
            )
            _append_unique(
                plan["source_notes"],
                (
                    "Timeline correction: removed Kazakhstan final credentials from U.S. exams_to_prioritize. "
                    "Only mention them as final/post-admission records or as an official-source exception."
                ),
            )

    if region == "hong_kong":
        _append_unique(
            plan["profile_actions"],
            (
                "For Hong Kong targets, confirm whether the portal asks for predicted and/or actual school-leaving "
                "results, then ask your school whether it can issue predicted NIS Grade 12 Certificate/internal Grade 12 grades."
            ),
        )

    return plan


def search_university_sources(university_name: str, intended_major: str | None = None) -> list[dict[str, str]]:
    major = intended_major or "undergraduate"
    queries = [
        (
            f"{university_name} official undergraduate admissions international students requirements "
            f"application deadlines standardized testing {major}"
        ),
        f"{university_name} official scholarships financial aid international undergraduate students",
        f"{university_name} official {major} undergraduate department research opportunities",
        f"{university_name} official summer programs high school students {major}",
        f"{university_name} official pre-collegiate summer program high school students",
        f"{university_name} official outreach programs high school students {major}",
    ]

    deadline = time.monotonic() + SEARCH_TIME_BUDGET_SECONDS
    seen: set[str] = set()
    results: list[dict[str, str]] = []
    for query_index, query in enumerate(queries):
        if time.monotonic() >= deadline and results:
            break
        request_count = 5 if query_index < 2 else 6
        for item in _search_web(query, num=request_count):
            url = item["url"]
            if url in seen:
                continue
            seen.add(url)
            results.append(
                {
                    **item,
                    "query": query,
                    "source_tier": _source_tier(url, university_name, item.get("title", "")),
                }
            )
            if len(results) >= 24:
                break
        if len(results) >= 24:
            break

    tier_priority = {
        "official": 0,
        "likely_official": 1,
        "education_domain": 2,
        "third_party": 3,
    }
    results.sort(key=lambda item: tier_priority.get(item["source_tier"], 9))
    official_or_education = [
        item
        for item in results
        if item["source_tier"] in {"official", "likely_official", "education_domain"}
    ]
    if len(official_or_education) >= 4:
        return official_or_education[:16]
    return results[:16]


def _profile_payload(user: Any) -> dict[str, Any]:
    profile = getattr(user, "profile", None)
    return {
        "country": getattr(user, "country", None),
        "graduation_year": getattr(profile, "graduation_year", None),
        "curriculum": getattr(profile, "curriculum", None),
        "intended_major": getattr(profile, "intended_major", None),
        "sat_score": getattr(profile, "sat_score", None),
        "sat_math": getattr(profile, "sat_math", None),
        "sat_ebrw": getattr(profile, "sat_ebrw", None),
        "act_score": getattr(profile, "act_score", None),
        "ielts_score": getattr(profile, "ielts_score", None),
        "toefl_score": getattr(profile, "toefl_score", None),
        "duolingo_score": getattr(profile, "duolingo_score", None),
        "a_level_subjects": getattr(profile, "a_level_subjects", None),
        "ib_predicted_score": getattr(profile, "ib_predicted_score", None),
        "unt_score": getattr(profile, "unt_score", None),
        "nis_grade12_certificate_gpa": getattr(profile, "nis_grade12_certificate_gpa", None),
    }


def _achievement_payload(achievements: list[Any]) -> list[dict[str, Any]]:
    return [
        {
            "type": getattr(item.type, "value", item.type),
            "title": item.title,
            "organization_name": item.organization_name,
            "role_title": item.role_title,
            "description_raw": item.description_raw,
            "category": item.category,
            "impact_scope": getattr(item.impact_scope, "value", item.impact_scope),
            "leadership_level": getattr(item.leadership_level, "value", item.leadership_level),
            "major_relevance_score": item.major_relevance_score,
            "selectivity_score": item.selectivity_score,
            "continuity_score": item.continuity_score,
            "distinctiveness_score": item.distinctiveness_score,
        }
        for item in achievements
    ]


def _truncate_text(value: Any, limit: int) -> str:
    text = _compact(str(value or ""))
    if len(text) <= limit:
        return text
    truncated = text[:limit]
    last_space = truncated.rfind(" ")
    if last_space > max(0, limit - 30):
        truncated = truncated[:last_space]
    return truncated.rstrip(" ,.;:")


def _is_generic_program_name(name: str) -> bool:
    normalized = name.lower().strip()
    generic_names = {
        "research opportunities",
        "summer programs",
        "internships",
        "summer internships",
        "research or summer programs",
        "high school summer programs",
        "official summer programs",
    }
    return (
        normalized in generic_names
        or normalized.startswith("seek ")
        or normalized.startswith("find ")
        or "cannot be confirmed" in normalized
        or "not confirmed" in normalized
    )


def _normalize_advisor_plan(plan: dict[str, Any]) -> dict[str, Any]:
    normalized: dict[str, Any] = {
        "summary": _truncate_text(plan.get("summary"), 160),
        "exams_to_prioritize": [],
        "profile_actions": [],
        "low_value_activities": [],
        "research_or_summer_programs": [],
        "source_notes": [],
    }

    for item in plan.get("exams_to_prioritize") or []:
        if not isinstance(item, dict):
            continue
        exam = _truncate_text(item.get("exam"), 80)
        why = _truncate_text(item.get("why"), 190)
        priority = str(item.get("priority") or "medium").lower()
        if priority not in {"high", "medium", "low"}:
            priority = "medium"
        if exam and why:
            normalized["exams_to_prioritize"].append(
                {"exam": exam, "why": why, "priority": priority}
            )
        if len(normalized["exams_to_prioritize"]) >= 5:
            break

    for key, limit, max_items in (
        ("profile_actions", 210, 7),
        ("low_value_activities", 180, 5),
        ("source_notes", 220, 5),
    ):
        seen: set[str] = set()
        for item in plan.get(key) or []:
            text = _truncate_text(item, limit)
            if text and text not in seen:
                normalized[key].append(text)
                seen.add(text)
            if len(normalized[key]) >= max_items:
                break

    program_seen: set[str] = set()
    for item in plan.get("research_or_summer_programs") or []:
        if not isinstance(item, dict):
            continue
        name = _truncate_text(item.get("name"), 110)
        if not name or _is_generic_program_name(name) or name in program_seen:
            continue
        program = {
            "name": name,
            "why_it_helps": _truncate_text(item.get("why_it_helps"), 210),
        }
        source_url = _compact(str(item.get("source_url") or ""))
        if source_url.startswith(("http://", "https://")):
            program["source_url"] = source_url
        normalized["research_or_summer_programs"].append(program)
        program_seen.add(name)
        if len(normalized["research_or_summer_programs"]) >= 8:
            break

    if not normalized["research_or_summer_programs"]:
        _append_unique(
            normalized["source_notes"],
            "No exact named research or summer program was confirmed from the current official sources.",
        )
    return normalized


def _prompt(
    *,
    university_name: str,
    user: Any,
    achievements: list[Any],
    search_results: list[dict[str, str]],
) -> str:
    payload = {
        "target_university": university_name,
        "student_profile": _profile_payload(user),
        "student_achievements": _achievement_payload(achievements),
        "web_search_results": search_results,
    }
    return (
        "You are ApplyMap Chancellor. Give a concise, factual action plan for one target university. "
        "Use only the student profile, achievements, and the supplied web search results. "
        "Do not invent admission requirements, scores, deadlines, program names, or scholarships. "
        "If a fact is not supported by a source result, write that it cannot be confirmed from the current sources.\n\n"
        "Kazakhstan context: interpret NIS school context, IB, A-levels, UNT/ENT, MESK/NIS Grade 12 Certificate, "
        "and 11 vs 12 years of schooling with strict timeline awareness. MESK in Russian/Kazakh user language maps "
        "to NIS Grade 12 Certificate in English.\n\n"
        f"{ADMISSIONS_FRAMEWORK}\n\n"
        f"{CHANCELLOR_COUNSELOR_FRAMEWORK}\n\n"
        "Be direct. Do not write a portfolio analysis paragraph. Return a practical plan the student can act on. "
        "Keep summary under 160 characters. Keep every why/action under 210 characters. Identify exams that could "
        "materially improve the application, activities that are low-value for this target, and exact research, "
        "summer, pre-collegiate, outreach, or department program names only when they appear in the supplied source "
        "results. Never write generic items like 'seek internships', 'find research', or 'summer programs'. Name the "
        "actual program and include source_url when the source result gives one. If no exact program name is supported, "
        "return an empty research_or_summer_programs array and one short source_note. Do not make the student search manually.\n\n"
        "Output rules:\n"
        "- exams_to_prioritize: max 5. Only tests or exam-like requirements, not long transcript commentary.\n"
        "- profile_actions: max 7. Concrete next moves, not broad advice.\n"
        "- low_value_activities: max 5. Say what to stop or avoid for this exact target.\n"
        "- research_or_summer_programs: max 8 exact named programs with concise relevance.\n"
        "- source_notes: only warnings about source limits or timeline corrections. Do not paste links as advice.\n\n"
        "Critical Kazakhstan timeline rules:\n"
        "- For U.S. fall applications, do not list final UNT/ENT, final MESK/NIS Grade 12 Certificate, or final Grade 12 "
        "GPA as high/medium exams to prioritize unless the target's official source explicitly allows that for the "
        "relevant deadline. Kazakhstan students commonly apply during Grade 12 before final school-leaving results exist.\n"
        "- For U.S. targets, exams_to_prioritize should focus only on application-stage tests such as SAT/ACT when "
        "required/useful and English proficiency when the official source requires it. Treat transcripts, school reports, "
        "course rigor, midyear reports, and final reports as application records, not exams to prioritize.\n"
        "- If a U.S. target official source accepts national leaving exam results or predictions only as an exception "
        "when SAT/ACT access is impossible, describe it as an exception in source_notes/profile_actions, not as the main plan.\n"
        "- For Hong Kong targets, predicted and/or actual grades may matter when the official portal asks for them; ask "
        "whether the school can issue predicted NIS Grade 12 Certificate/internal Grade 12 grades. Do not assume U.S. "
        "Common App logic applies to Hong Kong.\n"
        "- For every other country, verify the exact portal timing before advising on predicted grades, final certificates, "
        "or national exams. Return JSON only.\n\n"
        f"Input JSON:\n{json.dumps(payload, ensure_ascii=False, default=str)}"
    )


def _extract_text(response_payload: dict[str, Any]) -> str:
    candidates = response_payload.get("candidates") or []
    content = candidates[0].get("content") if candidates else {}
    parts = content.get("parts") or []
    return str(parts[0].get("text", "")) if parts else ""


def generate_university_action_plan(
    *,
    university_name: str,
    user: Any,
    achievements: list[Any],
    search_results: list[dict[str, str]],
) -> dict[str, Any]:
    api_key = settings.GEMINI_API_KEY.strip()
    if not api_key:
        return {
            "summary": "Gemini is not configured, so ApplyMap cannot generate a source-backed action plan yet.",
            "exams_to_prioritize": [],
            "profile_actions": [],
            "low_value_activities": [],
            "research_or_summer_programs": [],
            "source_notes": ["Set GEMINI_API_KEY to enable the Chancellor action plan."],
        }

    model = (settings.GEMINI_MODEL or "gemini-2.5-flash").strip()
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    request_payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": _prompt(
                            university_name=university_name,
                            user=user,
                            achievements=achievements,
                            search_results=search_results,
                        )
                    }
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.1,
            "responseMimeType": "application/json",
            "responseJsonSchema": ADVISOR_SCHEMA,
        },
    }

    try:
        with httpx.Client(timeout=16.0) as client:
            response = client.post(
                url,
                headers={"x-goog-api-key": api_key, "Content-Type": "application/json"},
                json=request_payload,
            )
            response.raise_for_status()
        plan = json.loads(_extract_text(response.json()))
        if not isinstance(plan, dict):
            raise ValueError("Advisor response was not a JSON object")
        return _normalize_advisor_plan(
            _sanitize_application_timeline(
                plan,
                university_name=university_name,
                search_results=search_results,
            )
        )
    except (httpx.HTTPError, json.JSONDecodeError, KeyError, TypeError, ValueError):
        return {
            "summary": "The Chancellor could not generate a reliable JSON plan from the current sources.",
            "exams_to_prioritize": [],
            "profile_actions": [],
            "low_value_activities": [],
            "research_or_summer_programs": [],
            "source_notes": ["Retry with a more specific university name or after checking API configuration."],
        }
