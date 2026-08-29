import type { ProjectProfile, SchemeMatchRecord } from "../types";

const GEMINI_API_KEY = "AIzaSyBwMoaDQyg1Xxa8wIaqUjfq2J1frflNk84";

export async function evaluateSchemesWithGemini(profile: ProjectProfile): Promise<SchemeMatchRecord[]> {
  const prompt = `
You are NIRVAAN, an expert AI for Indian Government Subsidies, MSME Incentives & Central/State Capital Schemes.
Evaluate the following business profile and return ALL applicable real government schemes:

BUSINESS DETAILS:
- Company Name: ${profile.companyName}
- Business Type / Sector: ${profile.sector || profile.businessTypeId}
- Location: ${profile.state}, District: ${profile.district}, City/Taluk: ${profile.cityTaluk}
- Scale: ${profile.size} Size (${profile.employees} Employees)
- Investment Amount: ₹${profile.investmentAmount || 10000000} INR
- Expected Turnover: ₹${profile.expectedTurnover || 25000000} INR
- Project Type: ${profile.projectType}
- Premises Type: ${profile.premisesType || "MIDC_PLOT"}
- Manufacturing/Business Activity: ${profile.activity}

INSTRUCTIONS:
Provide 3 to 5 REAL Indian Central or State Government schemes applicable for this specific business profile.
Return ONLY valid JSON matching this schema:
{
  "schemes": [
    {
      "id": "sch-1",
      "code": "PMFME_SCHEME",
      "name": "Full Government Scheme Name",
      "department": "Ministry or Department Name",
      "category": "CAPITAL_SUBSIDY",
      "matchStatus": "MATCHED",
      "estimatedBenefit": 3500000,
      "benefitSummary": "35% Credit-Linked Capital Subsidy up to ₹35 Lakhs for modernizing unit.",
      "reasons": [
        "Sector qualifies under state/central mandate",
        "Investment amount is within eligible bracket"
      ],
      "documents": ["PAN_CARD", "UDYAM_REGISTRATION", "PROJECT_REPORT", "GST_IN"],
      "portalUrl": "https://official-portal.gov.in"
    }
  ]
}
`;

  try {
    const url = `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=${GEMINI_API_KEY}`;
    const resp = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        contents: [{ parts: [{ text: prompt }] }],
        generationConfig: {
          temperature: 0.2,
          response_mime_type: "application/json",
        },
      }),
    });

    if (resp.ok) {
      const data = await resp.json();
      const text = data?.candidates?.[0]?.content?.parts?.[0]?.text;
      if (text) {
        const clean = text.replace(/```json\s*|\s*```/g, "").trim();
        const parsed = JSON.parse(clean);
        if (Array.isArray(parsed?.schemes) && parsed.schemes.length > 0) {
          return parsed.schemes.map((s: any, idx: number) => ({
            id: s.id || `gemini-sch-${idx + 1}`,
            code: s.code || `SCHEME_${idx + 1}`,
            name: s.name || "Government Incentive Scheme",
            department: s.department || "Government Department",
            category: s.category || "CAPITAL_SUBSIDY",
            matchStatus: s.matchStatus || "MATCHED",
            estimatedBenefit: Number(s.estimatedBenefit) || 2500000,
            benefitSummary: s.benefitSummary || "Capital Subsidy & Interest Subvention",
            reasons: Array.isArray(s.reasons) ? s.reasons : ["Qualifies under state/central mandate"],
            documents: Array.isArray(s.documents) ? s.documents : ["PAN_CARD", "PROJECT_REPORT"],
            portalUrl: s.portalUrl || "https://india.gov.in",
          }));
        }
      }
    }
  } catch (err) {
    console.warn("Gemini API call warning in frontend, using dynamic rule generator fallback:", err);
  }

  // Dynamic rule-based fallback based on exact user inputs if Gemini endpoint is unreachable
  return generateDynamicSchemesForProfile(profile);
}

function generateDynamicSchemesForProfile(p: ProjectProfile): SchemeMatchRecord[] {
  const isFood = (p.sector || p.businessTypeId || "").toLowerCase().includes("food");
  const isMaha = (p.state || "").toLowerCase().includes("maharashtra");
  const invLakhs = ((p.investmentAmount || 10000000) / 100000).toFixed(0);

  const results: SchemeMatchRecord[] = [];

  if (isFood) {
    results.push({
      id: "sch-gem-1",
      code: "PMFME_CAPITAL_SUBSIDY",
      name: "PM Formalisation of Micro Food Processing Enterprises (PMFME) Scheme",
      department: "Ministry of Food Processing Industries (MoFPI)",
      category: "CAPITAL_SUBSIDY",
      matchStatus: "MATCHED",
      estimatedBenefit: Math.min(1000000, (p.investmentAmount || 10000000) * 0.35),
      benefitSummary: `35% Credit-Linked Capital Subsidy up to ₹10 Lakhs for ${p.companyName}.`,
      reasons: [
        `Food processing activity '${p.activity || p.businessTypeId}' qualifies under MoFPI central mandate.`,
        `Investment of ₹${invLakhs} Lakhs meets micro-enterprise subsidy guidelines.`,
      ],
      documents: ["PAN_CARD", "RENT_AGREEMENT", "BANK_SANCTION_LETTER", "PROJECT_REPORT"],
      portalUrl: "https://pmfme.mofpi.gov.in",
    });
  }

  if (isMaha) {
    results.push({
      id: "sch-gem-2",
      code: "MAHA_PSI_INCENTIVE_2026",
      name: `Maharashtra Package Scheme of Incentives (PSI 2026) - ${p.district} Zone`,
      department: "Industries Department, Government of Maharashtra / MAITRI",
      category: "INTEREST_SUBVENTION",
      matchStatus: "MATCHED",
      estimatedBenefit: Math.min(3000000, (p.investmentAmount || 10000000) * 0.2),
      benefitSummary: `5% Interest Subvention for 5 years + Electricity Duty Exemption for units in ${p.district}.`,
      reasons: [
        `Registered entity '${p.companyName}' located in ${p.district}, ${p.state}.`,
        `Premises type '${p.premisesType || "Industrial Zone"}' qualifies for regional incentive bonus.`,
      ],
      documents: ["PAN_CARD", "RENT_AGREEMENT", "ELECTRICITY_BILL", "MAITRI_REGISTRATION_CERT"],
      portalUrl: "https://maitri.mahaonline.gov.in",
    });
  }

  results.push({
    id: "sch-gem-3",
    code: "CENTRAL_MSME_CREDIT_SCHEME",
    name: "Central MSME Credit Guarantee & Interest Subvention Scheme",
    department: "Ministry of Micro, Small & Medium Enterprises (MSME)",
    category: "INTEREST_SUBVENTION",
    matchStatus: "MATCHED",
    estimatedBenefit: Math.min(1500000, (p.investmentAmount || 10000000) * 0.1),
    benefitSummary: `2% Interest Subvention on working capital + Collateral-free CGTMSE credit cover for ${p.employees} employees unit.`,
    reasons: [
      `Employee count of ${p.employees} and investment fit MSME threshold.`,
      `Activity '${p.activity}' approved under MSME Udyam classification.`,
    ],
    documents: ["PAN_CARD", "UDYAM_REGISTRATION", "BANK_LOAN_SANCTION"],
    portalUrl: "https://udyamregistration.gov.in",
  });

  return results;
}
