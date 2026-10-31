from __future__ import annotations

import re
from collections import Counter

from .model_adapter import MODEL


TECH_SKILLS = {
    "python", "java", "javascript", "typescript", "c++", "c#", "go", "rust", "sql", "nosql",
    "react", "angular", "vue", "node", "express", "django", "flask", "fastapi", "spring",
    "aws", "azure", "gcp", "docker", "kubernetes", "terraform", "linux", "git", "github",
    "machine learning", "deep learning", "nlp", "computer vision", "tensorflow", "pytorch",
    "scikit-learn", "pandas", "numpy", "power bi", "tableau", "excel", "spark", "hadoop",
    "mongodb", "postgresql", "mysql", "redis", "graphql", "rest api", "ci/cd", "jenkins",
}

SOFT_SKILLS = {
    "leadership", "communication", "collaboration", "problem solving", "ownership",
    "stakeholder management", "mentoring", "planning", "presentation", "analysis",
}

ACTION_VERBS = {
    "built", "created", "designed", "developed", "implemented", "launched", "led", "managed",
    "optimized", "improved", "reduced", "increased", "automated", "integrated", "delivered",
    "migrated", "analyzed", "architected", "trained", "deployed", "scaled", "resolved",
}

WEAK_BULLET_STARTS = {
    "responsible", "worked", "helped", "assisted", "participated", "involved", "handled",
    "did", "made", "used", "supported",
}

BUZZWORDS = {
    "hardworking", "go-getter", "synergy", "dynamic", "self-starter", "detail-oriented",
    "team player", "results-driven", "go getter", "fast learner",
}

SECTION_PATTERNS = {
    "summary": r"\b(summary|profile|objective|about)\b",
    "experience": r"\b(experience|employment|work history|professional experience)\b",
    "skills": r"\b(skills|technical skills|technologies|tools)\b",
    "education": r"\b(education|degree|university|college|bachelor|master)\b",
    "projects": r"\b(projects|portfolio|certifications|certificates|publications)\b",
}

STOPWORDS = {
    "and", "the", "for", "with", "that", "this", "from", "are", "was", "were", "you", "your",
    "will", "have", "has", "our", "their", "they", "into", "using", "use", "work", "team",
    "role", "job", "candidate", "experience", "skills", "ability", "required", "preferred",
    "need", "needs", "looking", "responsibilities", "requirements", "must", "should",
}


def _words(text: str) -> list[str]:
    return [word.strip(".-") for word in re.findall(r"[a-zA-Z][a-zA-Z+#.\-]{1,}", text.lower()) if word.strip(".-")]


def _phrases_found(text_lower: str, phrases: set[str]) -> list[str]:
    found = []
    for phrase in sorted(phrases):
        pattern = r"(?<![a-z0-9])" + re.escape(phrase.lower()) + r"(?![a-z0-9])"
        if re.search(pattern, text_lower):
            found.append(phrase)
    return found


def _job_keywords(job_description: str) -> list[str]:
    words = [word for word in _words(job_description) if len(word) > 2 and word not in STOPWORDS]
    counts = Counter(words)
    selected = [word for word, _ in counts.most_common(28)]

    jd_lower = job_description.lower()
    for phrase in sorted(TECH_SKILLS | SOFT_SKILLS):
        if " " in phrase and phrase in jd_lower and phrase not in selected:
            selected.insert(0, phrase)
    return selected[:32]


def _score_band(score: int) -> str:
    if score >= 85:
        return "Excellent"
    if score >= 72:
        return "Strong"
    if score >= 58:
        return "Fair"
    return "Needs work"


def _clamp(value: float, low: int = 0, high: int = 100) -> int:
    return int(max(low, min(high, round(value))))


def _sentences(text: str) -> list[str]:
    return [sentence.strip() for sentence in re.split(r"[.!?]+", text) if sentence.strip()]


def _resume_lines(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines() if line.strip()]


def _bullet_lines(text: str) -> list[str]:
    return [
        match.group(2).strip()
        for match in re.finditer(r"(^|\n)\s*(?:[\-*•]|\d+[.)])\s+(.+)", text)
    ]


def _estimate_experience_years(text_lower: str) -> int | None:
    values = [int(value) for value in re.findall(r"\b(\d{1,2})\+?\s+years?\b", text_lower)]
    if values:
        return max(values)
    return None


def _level_signal(text_lower: str, years: int | None) -> str:
    if re.search(r"\b(intern|internship|fresher|entry level|junior)\b", text_lower):
        return "Entry level"
    if re.search(r"\b(senior|lead|principal|staff|architect|manager)\b", text_lower):
        return "Senior"
    if years is not None:
        if years >= 7:
            return "Senior"
        if years <= 2:
            return "Entry level"
    return "Mid level"


def _analysis_band(score: float) -> str:
    if score >= 80:
        return "Strong"
    if score >= 60:
        return "Moderate"
    return "Needs attention"


def _section_depth(lines: list[str]) -> dict[str, dict[str, int | str]]:
    depths: dict[str, dict[str, int | str]] = {}
    section_order = list(SECTION_PATTERNS)
    current = "other"
    counts = {name: 0 for name in section_order}

    for line in lines:
        lowered = line.lower()
        matched = next((name for name, pattern in SECTION_PATTERNS.items() if re.search(pattern, lowered)), None)
        if matched:
            current = matched
            continue
        if current in counts:
            counts[current] += 1

    for name, count in counts.items():
        if count >= 6:
            depth = "Detailed"
        elif count >= 2:
            depth = "Adequate"
        else:
            depth = "Thin"
        depths[name] = {"lines": count, "depth": depth}
    return depths


def _top_terms(words: list[str], limit: int = 10) -> list[str]:
    useful = [word for word in words if len(word) > 3 and word not in STOPWORDS]
    return [word for word, _ in Counter(useful).most_common(limit)]


def _has_github(text_lower: str) -> bool:
    return "github.com" in text_lower or re.search(r"\bgithub\b", text_lower) is not None


def _has_portfolio(text_lower: str) -> bool:
    return any(token in text_lower for token in ("portfolio", "website", "personal site", "behance", "dribbble", "kaggle.com"))


def _certifications(text_lower: str) -> list[str]:
    patterns = {
        "AWS": r"\b(aws certified|aws cloud practitioner|solutions architect)\b",
        "Azure": r"\b(azure certified|az-900|az-104|azure fundamentals)\b",
        "Google Cloud": r"\b(gcp certified|google cloud certified|professional cloud)\b",
        "Scrum": r"\b(scrum master|csm|psm)\b",
        "Data": r"\b(coursera|udacity|data analytics certificate|tensorflow developer)\b",
        "Security": r"\b(comptia|security\+|cissp|ceh)\b",
    }
    return [label for label, pattern in patterns.items() if re.search(pattern, text_lower)]


def _extract_section_lines(lines: list[str], section_name: str) -> list[str]:
    current = ""
    collected: list[str] = []
    for line in lines:
        lowered = line.lower()
        matched = next((name for name, pattern in SECTION_PATTERNS.items() if re.search(pattern, lowered)), None)
        if matched:
            current = matched
            continue
        if current == section_name:
            collected.append(line)
    return collected


def _keyword_density(words: list[str], keywords: list[str]) -> list[dict[str, float | int | str]]:
    counts = Counter(words)
    total = max(1, len(words))
    rows = []
    for keyword in keywords[:16]:
        if " " in keyword:
            continue
        count = counts[keyword.lower()]
        rows.append({"keyword": keyword, "count": count, "density": round(count / total * 100, 2)})
    return rows


def _rewrite_suggestion(bullet: str) -> str:
    clean = re.sub(r"^[\s\-*•\d.)]+", "", bullet).strip()
    clean = re.sub(r"^(responsible for|worked on|helped|assisted with|supported)\s+", "", clean, flags=re.I)
    if not clean:
        clean = "the project"
    return f"Improved {clean} by adding a measurable result, scope, or business impact."


def _make_action_plan(missing_keywords: list[str], ats_risks: list[dict[str, str]], weak_bullets: list[str], sections: dict[str, bool], metric_count: int) -> dict[str, list[str]]:
    quick_wins: list[str] = []
    if missing_keywords:
        quick_wins.append("Add the top missing job keywords exactly where they naturally fit: " + ", ".join(missing_keywords[:5]) + ".")
    if not all(sections.values()):
        missing_sections = [name.title() for name, ok in sections.items() if not ok]
        quick_wins.append("Create clear section headings for: " + ", ".join(missing_sections) + ".")
    if metric_count < 3:
        quick_wins.append("Add at least three numbers to prove scale, speed, quality, savings, users, or revenue.")
    if not quick_wins:
        quick_wins.append("Keep this version as a base resume and tailor keywords for each job post.")

    high_impact_edits = []
    if weak_bullets:
        high_impact_edits.append("Rewrite weak bullets to start with a strong verb and end with a measurable outcome.")
    if any(risk["level"] == "High" for risk in ats_risks):
        high_impact_edits.append("Fix high-severity ATS parser risks before sending this resume.")
    high_impact_edits.append("Move the strongest project or achievement into the top third of the resume.")

    next_steps = [
        "Run the analyzer again with the exact job description before applying.",
        "Use the Interview prep topics to prepare short STAR stories.",
        "Export a simple text-based PDF after edits to keep parsing reliable.",
    ]
    return {"quick_wins": quick_wins, "high_impact_edits": high_impact_edits, "next_steps": next_steps}


def analyze_resume(resume_text: str, job_description: str, target_role: str, pdf_status: dict) -> dict:
    text_lower = resume_text.lower()
    words = _words(resume_text)
    word_count = len(words)
    lines = _resume_lines(resume_text)
    sentences = _sentences(resume_text)

    email = bool(re.search(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", resume_text, re.I))
    phone = bool(re.search(r"(\+\d{1,3}[\s.-]?)?(\(?\d{3,5}\)?[\s.-]?)?\d{3,5}[\s.-]?\d{4}", resume_text))
    linkedin = "linkedin.com" in text_lower or "linkedin" in text_lower

    sections = {name: bool(re.search(pattern, text_lower)) for name, pattern in SECTION_PATTERNS.items()}
    section_score = sum(sections.values()) / len(sections) * 100

    found_tech = _phrases_found(text_lower, TECH_SKILLS)
    found_soft = _phrases_found(text_lower, SOFT_SKILLS)
    found_actions = sorted({word for word in words if word in ACTION_VERBS})
    has_github = _has_github(text_lower)
    has_portfolio = _has_portfolio(text_lower)
    certs = _certifications(text_lower)

    metric_hits = re.findall(r"(\d+%|\$[\d,.]+|\b\d+[xX]\b|\b\d+\+?\s*(users|customers|projects|people|hours|days|months|years)\b)", resume_text)
    bullets = _bullet_lines(resume_text)
    bullet_count = len(bullets)

    job_keywords = _job_keywords(job_description)
    resume_token_set = set(words)
    matched_keywords = []
    for keyword in job_keywords:
        if " " in keyword:
            if keyword.lower() in text_lower:
                matched_keywords.append(keyword)
        elif keyword.lower() in resume_token_set:
            matched_keywords.append(keyword)
    missing_keywords = [keyword for keyword in job_keywords if keyword not in matched_keywords]
    keyword_coverage = len(matched_keywords) / len(job_keywords) * 100 if job_keywords else min(100, len(found_tech) * 8)

    semantic_similarity = MODEL.similarity(resume_text, job_description)
    if semantic_similarity is not None:
        keyword_component = (keyword_coverage * 0.7) + (semantic_similarity * 100 * 0.3)
    else:
        keyword_component = keyword_coverage

    contact_score = (email * 4) + (phone * 3) + (linkedin * 3)
    experience_score = min(100, (min(bullet_count, 12) / 12 * 40) + (min(len(found_actions), 12) / 12 * 35) + (min(len(metric_hits), 8) / 8 * 25))
    format_score = 100
    if word_count < 250:
        format_score -= 35
    elif word_count > 1100:
        format_score -= 12
    if len(re.findall(r"\s{8,}", resume_text)) > 12:
        format_score -= 12
    if "references available" in text_lower:
        format_score -= 5
    if not bullet_count:
        format_score -= 18

    impact_score = min(100, (min(len(metric_hits), 8) / 8 * 60) + (min(len(found_actions), 10) / 10 * 40))
    skill_score = min(100, len(found_tech) * 7 + len(found_soft) * 4)
    readability_score = 100
    avg_sentence_words = round(word_count / len(sentences), 1) if sentences else 0
    long_sentence_count = sum(1 for sentence in sentences if len(_words(sentence)) > 28)
    if avg_sentence_words > 24:
        readability_score -= 20
    if long_sentence_count:
        readability_score -= min(25, long_sentence_count * 5)
    if word_count < 250:
        readability_score -= 15
    readability_score = max(0, readability_score)

    quantified_bullets = [
        bullet for bullet in bullets
        if re.search(r"\d+%|\$[\d,.]+|\b\d+[xX]\b|\b\d+\+?\s*(users|customers|projects|people|hours|days|months|years)\b", bullet)
    ]
    weak_bullets = [
        bullet for bullet in bullets
        if _words(bullet) and _words(bullet)[0] in WEAK_BULLET_STARTS
    ]
    achievement_score = min(
        100,
        (len(quantified_bullets) / max(1, bullet_count) * 55)
        + (min(len(found_actions), 10) / 10 * 30)
        + (min(bullet_count, 10) / 10 * 15),
    )

    jd_tech = _phrases_found(job_description.lower(), TECH_SKILLS) if job_description.strip() else []
    matched_role_skills = [skill for skill in jd_tech if skill in found_tech]
    role_fit_score = (
        len(matched_role_skills) / len(jd_tech) * 100
        if jd_tech else
        min(100, len(found_tech) * 8 + len(found_soft) * 3)
    )

    years = _estimate_experience_years(text_lower)
    seniority = _level_signal(text_lower + " " + job_description.lower(), years)

    ats_risks: list[dict[str, str]] = []
    if word_count < 250:
        ats_risks.append({"level": "High", "label": "Resume looks short", "detail": "ATS systems may not have enough context to match your experience."})
    if word_count > 1100:
        ats_risks.append({"level": "Medium", "label": "Resume may be too long", "detail": "Dense resumes can dilute important keywords and accomplishments."})
    if len(re.findall(r"\s{8,}", resume_text)) > 12:
        ats_risks.append({"level": "Medium", "label": "Possible table or column layout", "detail": "Some ATS parsers read multi-column layouts in the wrong order."})
    if re.search(r"\b(i|me|my|we|our)\b", text_lower):
        ats_risks.append({"level": "Low", "label": "First-person wording", "detail": "Resume bullets usually scan better without I, me, my, we, or our."})
    found_buzzwords = _phrases_found(text_lower, BUZZWORDS)
    if found_buzzwords:
        ats_risks.append({"level": "Low", "label": "Generic buzzwords", "detail": "Replace generic claims with proof: " + ", ".join(found_buzzwords[:5]) + "."})
    if not ats_risks:
        ats_risks.append({"level": "Low", "label": "No major parser risk detected", "detail": "The extracted text looks reasonably ATS friendly."})

    top_terms = _top_terms(words)
    repeated_terms = [
        {"term": term, "count": count}
        for term, count in Counter(word for word in words if len(word) > 3 and word not in STOPWORDS).most_common(8)
        if count >= 3
    ]
    summary_lines = _extract_section_lines(lines, "summary")
    experience_lines = _extract_section_lines(lines, "experience")
    project_lines = _extract_section_lines(lines, "projects")
    education_lines = _extract_section_lines(lines, "education")
    section_depth = _section_depth(lines)
    strong_signals = []
    if found_tech:
        strong_signals.append(f"Shows {len(found_tech)} technical skills, led by {', '.join(found_tech[:4])}.")
    if len(quantified_bullets) >= 2:
        strong_signals.append(f"Includes {len(quantified_bullets)} quantified achievement bullets.")
    if contact_score == 10:
        strong_signals.append("Contact details are easy to identify.")
    if has_github or has_portfolio:
        strong_signals.append("Includes a public work/profile signal.")
    if not strong_signals:
        strong_signals.append("Resume has extractable text and enough structure for baseline ATS review.")

    recruiter_concerns = []
    if missing_keywords:
        recruiter_concerns.append("The resume may not mirror the target job language closely enough.")
    if word_count < 250:
        recruiter_concerns.append("The resume reads thin, so experience depth may be hard to judge.")
    if len(quantified_bullets) < 2:
        recruiter_concerns.append("Business impact is not quantified often enough.")
    if not has_github and any(skill in found_tech for skill in ("python", "react", "machine learning", "fastapi", "javascript")):
        recruiter_concerns.append("Technical work would be stronger with a GitHub, portfolio, or project link.")
    if not recruiter_concerns:
        recruiter_concerns.append("No major first-pass recruiter concern detected.")

    section_insights = [
        {
            "name": "Summary",
            "status": "Present" if sections["summary"] else "Missing",
            "insight": "Best when it names the target role, domain, top skills, and measurable value.",
            "evidence": f"{len(summary_lines)} content lines detected.",
        },
        {
            "name": "Experience",
            "status": section_depth["experience"]["depth"],
            "insight": "Should focus on impact bullets, ownership, technologies, and outcomes.",
            "evidence": f"{bullet_count} bullets and {len(quantified_bullets)} quantified bullets detected.",
        },
        {
            "name": "Projects",
            "status": section_depth["projects"]["depth"],
            "insight": "Projects are strongest when they include stack, deployment, links, and results.",
            "evidence": f"{len(project_lines)} project/certification lines detected.",
        },
        {
            "name": "Education",
            "status": section_depth["education"]["depth"],
            "insight": "Education should include degree, institution, dates when useful, and relevant coursework for early-career resumes.",
            "evidence": f"{len(education_lines)} education lines detected.",
        },
        {
            "name": "Skills",
            "status": section_depth["skills"]["depth"],
            "insight": "Skills should be grouped and aligned with the job description.",
            "evidence": f"{len(found_tech)} technical skills and {len(found_soft)} soft skills detected.",
        },
    ]

    bullet_rewrites = [
        {"original": bullet, "suggestion": _rewrite_suggestion(bullet)}
        for bullet in (weak_bullets[:3] or bullets[:3])
    ]

    ats_score = _clamp(
        contact_score * 1.0
        + section_score * 0.20
        + keyword_component * 0.25
        + experience_score * 0.15
        + max(format_score, 0) * 0.15
        + impact_score * 0.10
        + skill_score * 0.05
    )

    recommendations: list[dict[str, str]] = []
    if missing_keywords[:8]:
        recommendations.append({
            "title": "Close keyword gaps",
            "detail": "Add exact language for: " + ", ".join(missing_keywords[:8]) + ".",
            "priority": "High",
        })
    if section_score < 100:
        missing_sections = [name.title() for name, ok in sections.items() if not ok]
        recommendations.append({
            "title": "Add missing ATS sections",
            "detail": "Missing or unclear sections: " + ", ".join(missing_sections) + ".",
            "priority": "High",
        })
    if len(metric_hits) < 3:
        recommendations.append({
            "title": "Quantify impact",
            "detail": "Add measurable outcomes such as percentages, cost savings, users served, latency reduced, or revenue influenced.",
            "priority": "Medium",
        })
    if not found_actions:
        recommendations.append({
            "title": "Strengthen bullet starts",
            "detail": "Begin bullets with verbs like Built, Led, Optimized, Automated, Deployed, or Improved.",
            "priority": "Medium",
        })
    if not email or not phone:
        recommendations.append({
            "title": "Fix contact details",
            "detail": "Include a clear email and phone number near the top of the resume.",
            "priority": "High",
        })
    if weak_bullets[:3]:
        recommendations.append({
            "title": "Rewrite passive bullets",
            "detail": "Replace weak starts like Responsible for or Worked on with action-plus-impact phrasing.",
            "priority": "Medium",
        })
    if readability_score < 70:
        recommendations.append({
            "title": "Improve scanability",
            "detail": "Shorten long sentences and keep bullets to one clear result each.",
            "priority": "Medium",
        })

    role_line = target_role.strip() or "Target role"
    summary = (
        f"{role_line}: {_score_band(ats_score)} ATS readiness. "
        f"Matched {len(matched_keywords)} of {len(job_keywords)} job keywords."
        if job_keywords else
        f"{role_line}: {_score_band(ats_score)} ATS readiness based on structure, skills, impact, and formatting."
    )

    return {
        "ats_score": ats_score,
        "score_band": _score_band(ats_score),
        "summary": summary,
        "word_count": word_count,
        "model": {
            "backend": MODEL.backend,
            "status": MODEL.status,
            "semantic_similarity": None if semantic_similarity is None else round(semantic_similarity * 100, 1),
        },
        "pdf_status": pdf_status,
        "checks": {
            "contact": {"email": email, "phone": phone, "linkedin": linkedin, "score": contact_score * 10},
            "sections": sections,
            "keyword_coverage": round(keyword_coverage, 1),
            "experience_score": round(experience_score, 1),
            "format_score": max(0, round(format_score, 1)),
            "impact_score": round(impact_score, 1),
            "skill_score": round(skill_score, 1),
            "readability_score": round(readability_score, 1),
            "achievement_score": round(achievement_score, 1),
            "role_fit_score": round(role_fit_score, 1),
        },
        "deep_analysis": {
            "score_breakdown": [
                {"label": "Contact", "score": contact_score * 10, "detail": "Email, phone, and LinkedIn/profile visibility."},
                {"label": "Sections", "score": round(section_score, 1), "detail": "Summary, experience, skills, education, and projects/certifications."},
                {"label": "Keywords", "score": round(keyword_component, 1), "detail": "Exact keyword coverage plus local model similarity."},
                {"label": "Experience", "score": round(experience_score, 1), "detail": "Bullet count, action verbs, and measurable work evidence."},
                {"label": "Formatting", "score": max(0, round(format_score, 1)), "detail": "Length, simple text structure, and parser friendliness."},
                {"label": "Impact", "score": round(impact_score, 1), "detail": "Numbers, scale, savings, speed, users, or other measurable outcomes."},
                {"label": "Skills", "score": round(skill_score, 1), "detail": "Technical and soft skills detected in the resume."},
                {"label": "Readability", "score": round(readability_score, 1), "detail": "Sentence length and scanability."},
                {"label": "Achievement quality", "score": round(achievement_score, 1), "detail": "Action verbs plus quantified bullets."},
                {"label": "Role fit", "score": round(role_fit_score, 1), "detail": "Detected role skills compared with the job description."},
            ],
            "readability": {
                "score": round(readability_score, 1),
                "band": _analysis_band(readability_score),
                "average_sentence_words": avg_sentence_words,
                "long_sentence_count": long_sentence_count,
            },
            "achievement_quality": {
                "score": round(achievement_score, 1),
                "band": _analysis_band(achievement_score),
                "bullet_count": bullet_count,
                "quantified_bullet_count": len(quantified_bullets),
                "weak_bullet_count": len(weak_bullets),
                "weak_bullets": weak_bullets[:5],
            },
            "role_fit": {
                "score": round(role_fit_score, 1),
                "band": _analysis_band(role_fit_score),
                "seniority_signal": seniority,
                "experience_years": years,
                "job_skills_detected": jd_tech,
                "matched_role_skills": matched_role_skills,
                "missing_role_skills": [skill for skill in jd_tech if skill not in matched_role_skills],
            },
            "section_depth": section_depth,
            "ats_risks": ats_risks,
            "top_terms": top_terms,
            "interview_prep": [
                f"Prepare a project story around {skill}." for skill in (missing_keywords[:3] or found_tech[:3])
            ],
        },
        "resume_insights": {
            "recruiter_view": {
                "headline": f"{_score_band(ats_score)} first-pass fit for {role_line}.",
                "first_impression": "Strong signal density" if ats_score >= 72 else "Needs stronger proof and targeting",
                "strong_signals": strong_signals,
                "concerns": recruiter_concerns,
            },
            "section_insights": section_insights,
            "content_audit": {
                "keyword_density": _keyword_density(words, job_keywords or top_terms),
                "repeated_terms": repeated_terms,
                "bullet_rewrites": bullet_rewrites,
                "links": {
                    "linkedin": linkedin,
                    "github": has_github,
                    "portfolio": has_portfolio,
                },
                "certifications": certs,
            },
            "project_review": {
                "has_project_section": sections["projects"],
                "project_line_count": len(project_lines),
                "has_github_or_portfolio": has_github or has_portfolio,
                "insight": "Add project links, tech stack, deployment details, and measurable results." if sections["projects"] else "Add a Projects section for hands-on proof, especially for technical roles.",
            },
            "action_plan": _make_action_plan(missing_keywords, ats_risks, weak_bullets, sections, len(metric_hits)),
        },
        "skills": {
            "technical": found_tech,
            "soft": found_soft,
            "action_verbs": found_actions,
        },
        "keywords": {
            "matched": matched_keywords,
            "missing": missing_keywords,
            "all": job_keywords,
        },
        "recommendations": recommendations,
        "extracted_text": resume_text[:12000],
    }
