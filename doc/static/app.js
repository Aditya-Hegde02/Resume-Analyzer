const form = document.querySelector("#analyze-form");
const button = document.querySelector("#analyze-button");
const errorBox = document.querySelector("#error-box");
const dial = document.querySelector("#dial-value");
const resumeFileInput = document.querySelector("#resume-pdf");
const pdfPreviewCard = document.querySelector("#pdf-preview-card");
let pdfPreviewUrl = "";

const isReadablePreview = (text) => {
  if (!text || text.trim().length < 80) return false;
  const chars = text.trim();
  const unusual = (chars.match(/[^\p{L}\p{N}\s.,;:!?%&@#$()+\-/'"…–—•|]/gu) || []).length;
  const words = chars.match(/[A-Za-z]+/g) || [];
  const singleLetters = chars.match(/\b[A-Za-z]\b/g) || [];
  return unusual / chars.length < 0.06 &&
    !(words.length >= 50 && singleLetters.length >= 10 && singleLetters.length / words.length > 0.14);
};

resumeFileInput.addEventListener("change", () => {
  const file = resumeFileInput.files?.[0];
  if (pdfPreviewUrl) URL.revokeObjectURL(pdfPreviewUrl);
  pdfPreviewUrl = "";
  if (!file || (file.type !== "application/pdf" && !file.name.toLowerCase().endsWith(".pdf"))) {
    pdfPreviewCard.classList.add("hidden");
    return;
  }
  pdfPreviewUrl = URL.createObjectURL(file);
  document.querySelector("#pdf-preview").src = pdfPreviewUrl;
  document.querySelector("#pdf-open-link").href = pdfPreviewUrl;
  document.querySelector("#pdf-preview-name").textContent = file.name;
  pdfPreviewCard.classList.remove("hidden");
});

const setText = (selector, value) => {
  document.querySelector(selector).textContent = value;
};

const percent = (value) => `${Math.round(Number(value) || 0)}%`;

const scoreLevel = (value) => {
  const score = Number(value) || 0;
  if (score < 40) return "score-low";
  if (score < 60) return "score-developing";
  if (score < 75) return "score-moderate";
  return "score-strong";
};

const renderChips = (selector, values, emptyText = "None found yet") => {
  const node = document.querySelector(selector);
  node.innerHTML = "";
  if (!values || !values.length) {
    const empty = document.createElement("span");
    empty.className = "empty-state";
    empty.textContent = emptyText;
    node.appendChild(empty);
    return;
  }
  values.forEach((value) => {
    const chip = document.createElement("span");
    chip.className = "chip";
    chip.textContent = value;
    node.appendChild(chip);
  });
};

const renderSignals = (checks) => {
  const node = document.querySelector("#contact-list");
  node.innerHTML = "";
  [
    ["Email", checks.email],
    ["Phone", checks.phone],
    ["LinkedIn", checks.linkedin],
  ].forEach(([label, ok]) => {
    const item = document.createElement("div");
    item.className = `signal ${ok ? "good" : "bad"}`;
    item.innerHTML = `<span>${label}</span><strong>${ok ? "Found" : "Missing"}</strong>`;
    node.appendChild(item);
  });
};

const renderSections = (sections) => {
  const node = document.querySelector("#section-checks");
  node.innerHTML = "";
  Object.entries(sections).forEach(([name, ok]) => {
    const item = document.createElement("div");
    item.className = `section-check ${ok ? "good" : "bad"}`;
    item.innerHTML = `<span>${name}</span><strong>${ok ? "Present" : "Missing"}</strong>`;
    node.appendChild(item);
  });
};

const renderRecommendations = (items) => {
  const node = document.querySelector("#recommendations");
  node.innerHTML = "";
  if (!items.length) {
    node.innerHTML = `<section class="panel"><h3>No major issues found</h3><p>Your resume is in a strong ATS shape for this input.</p></section>`;
    return;
  }
  items.forEach((item) => {
    const panel = document.createElement("section");
    panel.className = "panel recommendation";
    panel.innerHTML = `<span>${item.priority}</span><h3>${item.title}</h3><p>${item.detail}</p>`;
    node.appendChild(panel);
  });
};

const renderScoreBreakdown = (items) => {
  const node = document.querySelector("#score-breakdown");
  node.innerHTML = "";
  items.forEach((item) => {
    const row = document.createElement("div");
    row.className = `score-row ${scoreLevel(item.score)}`;
    row.innerHTML = `
      <div class="score-row-head"><span>${item.label}</span><strong>${percent(item.score)}</strong></div>
      <div class="bar"><span style="width: ${Math.max(0, Math.min(100, item.score))}%"></span></div>
      <p>${item.detail}</p>
    `;
    node.appendChild(row);
  });
};

const renderDetailStack = (selector, items) => {
  const node = document.querySelector(selector);
  node.innerHTML = "";
  items.forEach(([label, value]) => {
    const row = document.createElement("div");
    row.className = "detail-row";
    row.innerHTML = `<span>${label}</span><strong>${value}</strong>`;
    node.appendChild(row);
  });
};

const renderRiskList = (items) => {
  const node = document.querySelector("#ats-risks");
  node.innerHTML = "";
  items.forEach((item) => {
    const row = document.createElement("div");
    row.className = `risk ${item.level.toLowerCase()}`;
    row.innerHTML = `<span>${item.level}</span><div><strong>${item.label}</strong><p>${item.detail}</p></div>`;
    node.appendChild(row);
  });
};

const renderSectionDepth = (sections) => {
  const node = document.querySelector("#section-depth");
  node.innerHTML = "";
  Object.entries(sections).forEach(([name, data]) => {
    const row = document.createElement("div");
    row.className = `depth ${data.depth.toLowerCase()}`;
    row.innerHTML = `<span>${name}</span><strong>${data.depth}</strong><em>${data.lines} lines</em>`;
    node.appendChild(row);
  });
};

const renderPrepList = (items) => {
  const node = document.querySelector("#interview-prep");
  node.innerHTML = "";
  items.forEach((item) => {
    const row = document.createElement("div");
    row.className = "prep-item";
    row.textContent = item;
    node.appendChild(row);
  });
};

const renderTextList = (selector, items, emptyText = "No items detected") => {
  const node = document.querySelector(selector);
  node.innerHTML = "";
  if (!items || !items.length) {
    const empty = document.createElement("div");
    empty.className = "empty-card";
    empty.textContent = emptyText;
    node.appendChild(empty);
    return;
  }
  items.forEach((item) => {
    const row = document.createElement("div");
    row.className = "insight-item";
    row.textContent = item;
    node.appendChild(row);
  });
};

const renderRecruiterInsights = (insights) => {
  const recruiter = document.querySelector("#recruiter-view");
  recruiter.innerHTML = "";
  const hero = document.createElement("div");
  hero.className = "insight-hero";
  hero.innerHTML = `<span>${insights.recruiter_view.first_impression}</span><strong>${insights.recruiter_view.headline}</strong>`;
  recruiter.appendChild(hero);

  const strengths = document.createElement("div");
  strengths.className = "mini-section";
  strengths.innerHTML = "<h4>Strong signals</h4>";
  insights.recruiter_view.strong_signals.forEach((item) => {
    const row = document.createElement("p");
    row.textContent = item;
    strengths.appendChild(row);
  });
  recruiter.appendChild(strengths);

  const concerns = document.createElement("div");
  concerns.className = "mini-section warning-section";
  concerns.innerHTML = "<h4>Concerns</h4>";
  insights.recruiter_view.concerns.forEach((item) => {
    const row = document.createElement("p");
    row.textContent = item;
    concerns.appendChild(row);
  });
  recruiter.appendChild(concerns);

  const sectionNode = document.querySelector("#section-insights");
  sectionNode.innerHTML = "";
  insights.section_insights.forEach((item) => {
    const row = document.createElement("div");
    row.className = "section-insight";
    row.innerHTML = `<div><strong>${item.name}</strong><span>${item.status}</span></div><p>${item.insight}</p><em>${item.evidence}</em>`;
    sectionNode.appendChild(row);
  });

  const plan = document.querySelector("#action-plan");
  plan.innerHTML = "";
  [
    ["Quick wins", insights.action_plan.quick_wins],
    ["High-impact edits", insights.action_plan.high_impact_edits],
    ["Next steps", insights.action_plan.next_steps],
  ].forEach(([title, items]) => {
    const group = document.createElement("div");
    group.className = "plan-group";
    group.innerHTML = `<h4>${title}</h4>`;
    items.forEach((item) => {
      const row = document.createElement("p");
      row.textContent = item;
      group.appendChild(row);
    });
    plan.appendChild(group);
  });
};

const renderContentAudit = (insights) => {
  const density = document.querySelector("#keyword-density");
  density.innerHTML = "";
  insights.content_audit.keyword_density.forEach((item) => {
    const row = document.createElement("div");
    row.className = "density-row";
    row.innerHTML = `<span>${item.keyword}</span><strong>${item.count}</strong><em>${item.density}%</em>`;
    density.appendChild(row);
  });

  const proof = document.querySelector("#proof-signals");
  proof.innerHTML = "";
  [
    ["LinkedIn", insights.content_audit.links.linkedin],
    ["GitHub", insights.content_audit.links.github],
    ["Portfolio", insights.content_audit.links.portfolio],
    ["Certifications", insights.content_audit.certifications.length ? insights.content_audit.certifications.join(", ") : false],
  ].forEach(([label, ok]) => {
    const row = document.createElement("div");
    row.className = `signal ${ok ? "good" : "bad"}`;
    row.innerHTML = `<span>${label}</span><strong>${ok === true ? "Found" : ok || "Missing"}</strong>`;
    proof.appendChild(row);
  });

  const rewrites = document.querySelector("#bullet-rewrites");
  rewrites.innerHTML = "";
  if (!insights.content_audit.bullet_rewrites.length) {
    rewrites.innerHTML = `<div class="empty-card">No bullet rewrites available yet.</div>`;
  }
  insights.content_audit.bullet_rewrites.forEach((item) => {
    const row = document.createElement("div");
    row.className = "rewrite-card";
    row.innerHTML = `<span>Original</span><p>${item.original}</p><span>Rewrite direction</span><strong>${item.suggestion}</strong>`;
    rewrites.appendChild(row);
  });

  renderDetailStack("#project-review", [
    ["Project section", insights.project_review.has_project_section ? "Present" : "Missing"],
    ["Project lines", insights.project_review.project_line_count],
    ["GitHub or portfolio", insights.project_review.has_github_or_portfolio ? "Found" : "Missing"],
    ["Insight", insights.project_review.insight],
  ]);
};

const renderDeepAnalysis = (analysis) => {
  renderScoreBreakdown(analysis.score_breakdown);
  renderDetailStack("#role-fit-details", [
    ["Role fit", `${percent(analysis.role_fit.score)} · ${analysis.role_fit.band}`],
    ["Seniority signal", analysis.role_fit.seniority_signal],
    ["Experience years", analysis.role_fit.experience_years ?? "Not stated"],
    ["Role skills matched", `${analysis.role_fit.matched_role_skills.length} of ${analysis.role_fit.job_skills_detected.length || "detected skills"}`],
    ["Missing role skills", analysis.role_fit.missing_role_skills.slice(0, 5).join(", ") || "None detected"],
  ]);
  renderDetailStack("#writing-quality", [
    ["Readability", `${percent(analysis.readability.score)} · ${analysis.readability.band}`],
    ["Avg sentence length", `${analysis.readability.average_sentence_words} words`],
    ["Long sentences", analysis.readability.long_sentence_count],
    ["Achievement quality", `${percent(analysis.achievement_quality.score)} · ${analysis.achievement_quality.band}`],
    ["Quantified bullets", `${analysis.achievement_quality.quantified_bullet_count} of ${analysis.achievement_quality.bullet_count}`],
    ["Weak bullet starts", analysis.achievement_quality.weak_bullet_count],
  ]);
  renderRiskList(analysis.ats_risks);
  renderSectionDepth(analysis.section_depth);
  renderPrepList(analysis.interview_prep);
};

const updateDial = (score) => {
  const radius = 48;
  const circumference = 2 * Math.PI * radius;
  dial.classList.remove("score-low", "score-developing", "score-moderate", "score-strong");
  dial.classList.add(scoreLevel(score));
  dial.style.strokeDasharray = `${circumference}`;
  dial.style.strokeDashoffset = `${circumference - (score / 100) * circumference}`;
};

const renderOverviewCharts = (data) => {
  const scoreChart = document.querySelector("#overview-score-chart");
  scoreChart.innerHTML = "";
  data.deep_analysis.score_breakdown.forEach((item) => {
    const row = document.createElement("div");
    row.className = `chart-row ${scoreLevel(item.score)}`;
    const label = document.createElement("div");
    label.className = "chart-row-label";
    const name = document.createElement("span");
    name.textContent = item.label;
    const value = document.createElement("strong");
    value.textContent = percent(item.score);
    label.append(name, value);
    const track = document.createElement("div");
    track.className = "chart-track";
    const fill = document.createElement("span");
    fill.className = "score-fill";
    fill.style.width = `${Math.max(0, Math.min(100, Number(item.score) || 0))}%`;
    track.appendChild(fill);
    row.append(label, track);
    scoreChart.appendChild(row);
  });

  const matched = data.keywords.matched || [];
  const missing = data.keywords.missing || [];
  const total = matched.length + missing.length;
  const coverage = total ? Math.round((matched.length / total) * 100) : 0;
  const keywordChart = document.querySelector("#keyword-chart");
  keywordChart.innerHTML = "";
  document.querySelector("#keyword-chart-total").textContent = total ? `${total} job keywords` : "No job description";
  if (total) {
    const bar = document.createElement("div");
    bar.className = "stacked-bar";
    const found = document.createElement("span");
    found.className = "stacked-found";
    found.style.width = `${coverage}%`;
    const absent = document.createElement("span");
    absent.className = "stacked-missing";
    absent.style.width = `${100 - coverage}%`;
    bar.append(found, absent);
    const legend = document.createElement("div");
    legend.className = "chart-legend";
    legend.innerHTML = `<span><i class="legend-found"></i>Matched <strong>${matched.length}</strong></span><span><i class="legend-missing"></i>Missing <strong>${missing.length}</strong></span>`;
    const coverageValue = document.createElement("div");
    coverageValue.className = "coverage-value";
    coverageValue.innerHTML = `<strong>${coverage}%</strong><span>keyword coverage</span>`;
    keywordChart.append(coverageValue, bar, legend);
  } else {
    keywordChart.innerHTML = '<div class="chart-empty">Add a job description to compare keywords.</div>';
  }

  const sectionChart = document.querySelector("#section-health-chart");
  sectionChart.innerHTML = "";
  const sections = Object.entries(data.checks.sections || {});
  const present = sections.filter(([, found]) => found).length;
  document.querySelector("#section-chart-summary").textContent = `${present} of ${sections.length} key sections present`;
  sections.forEach(([name, found]) => {
    const item = document.createElement("div");
    item.className = `section-health-item ${found ? "is-present" : "is-missing"}`;
    const icon = document.createElement("span");
    icon.className = "section-health-icon";
    icon.textContent = found ? "✓" : "·";
    const label = document.createElement("span");
    label.className = "section-health-name";
    label.textContent = name;
    const status = document.createElement("strong");
    status.textContent = found ? "Present" : "Missing";
    item.append(icon, label, status);
    sectionChart.appendChild(item);
  });
};

const renderResult = (data) => {
  errorBox.classList.add("hidden");
  updateDial(data.ats_score);
  setText("#score-number", data.ats_score);
  setText("#score-band", data.score_band);
  setText("#headline", data.summary);
  setText("#keyword-coverage", percent(data.checks.keyword_coverage));
  setText("#format-score", percent(data.checks.format_score));
  setText("#impact-score", percent(data.checks.impact_score));
  setText("#role-fit-score", percent(data.checks.role_fit_score));
  setText("#readability-score", percent(data.checks.readability_score));
  setText("#achievement-score", percent(data.checks.achievement_score));
  setText("#word-count", data.word_count.toLocaleString());
  [
    ["#keyword-coverage", data.checks.keyword_coverage],
    ["#format-score", data.checks.format_score],
    ["#impact-score", data.checks.impact_score],
    ["#role-fit-score", data.checks.role_fit_score],
    ["#readability-score", data.checks.readability_score],
    ["#achievement-score", data.checks.achievement_score],
  ].forEach(([selector, score]) => {
    const value = document.querySelector(selector);
    value.classList.remove("score-low", "score-developing", "score-moderate", "score-strong");
    value.classList.add(scoreLevel(score));
  });
  setText("#summary-text", data.summary);
  setText("#model-status", "");

  renderOverviewCharts(data);

  renderSignals(data.checks.contact);
  renderSections(data.checks.sections);
  renderChips("#technical-skills", data.skills.technical);
  renderChips("#soft-skills", data.skills.soft);
  renderChips("#action-verbs", data.skills.action_verbs);
  renderChips("#matched-keywords", data.keywords.matched, "Paste a job description for keyword matching");
  renderChips("#missing-keywords", data.keywords.missing, "No missing keywords detected");
  renderDeepAnalysis(data.deep_analysis);
  renderRecruiterInsights(data.resume_insights);
  renderContentAudit(data.resume_insights);
  renderRecommendations(data.recommendations);
  const pdfStatus = data.pdf_status || {};
  const statusParts = [];
  if (pdfStatus.extractor) statusParts.push(`Extracted with ${pdfStatus.extractor}`);
  else statusParts.push("Using pasted resume text");
  if (pdfStatus.filename) statusParts.push(pdfStatus.filename);
  if (pdfStatus.warnings?.length) statusParts.push(...pdfStatus.warnings);
  if (isReadablePreview(data.extracted_text)) {
    setText("#extracted-text", data.extracted_text);
    setText("#text-status", statusParts.join(" · "));
  } else {
    setText("#extracted-text", "No reliable text could be decoded from this PDF. Use the original PDF preview above, or paste the resume text in the fallback field and analyze again.");
    setText("#text-status", "The extracted text was unreadable, so it has been hidden. The original resume PDF is available in the preview above.");
  }
};

document.querySelectorAll(".tab").forEach((tab) => {
  tab.addEventListener("click", () => {
    document.querySelectorAll(".tab").forEach((node) => node.classList.remove("active"));
    document.querySelectorAll(".tab-panel").forEach((node) => node.classList.remove("active"));
    tab.classList.add("active");
    document.querySelector(`#${tab.dataset.tab}`).classList.add("active");
  });
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  button.disabled = true;
  button.textContent = "Analyzing...";
  errorBox.classList.add("hidden");

  try {
    const response = await fetch("/analyze", {
      method: "POST",
      body: new FormData(form),
    });
    const data = await response.json();
    if (!response.ok) {
      const details = data.pdf_status?.warnings?.join(" ");
      throw new Error([data.error || "Analysis failed.", details].filter(Boolean).join(" "));
    }
    renderResult(data);
  } catch (error) {
    errorBox.textContent = error.message;
    errorBox.classList.remove("hidden");
  } finally {
    button.disabled = false;
    button.innerHTML = `<span class="button-icon">↗</span>Analyze locally`;
  }
});

updateDial(0);
