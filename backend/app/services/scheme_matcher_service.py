import os
import re
import json
import uuid
import httpx
from typing import List, Dict, Any, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.models.business import Business
from app.models.scheme import Scheme, SchemeCategory
from app.schemas.scheme import (
    SchemeMatchResultOut,
    BusinessSchemeMatchesResponse,
)
from app.core.config import settings
from app.core.logging import logger


class SchemeMatcherService:
    """
    Module 14: Government Scheme Matcher Service.
    Matches business profiles against government incentive schemes, evaluates eligibility,
    calculates estimated subsidy benefits, and generates required document checklists.
    """

    DEFAULT_SCHEMES = [
        {
            "code": "PMFME_CAPITAL_SUBSIDY",
            "name": "PM Formalisation of Micro Food Processing Enterprises (PMFME) Scheme",
            "department": "Ministry of Food Processing Industries (MoFPI)",
            "category": SchemeCategory.CAPITAL_SUBSIDY,
            "benefit_summary": "35% Credit-Linked Capital Subsidy up to ₹10 Lakhs for modernizing micro food processing units.",
            "max_benefit_amount": 1000000.0,
            "eligibility_conditions": {
                "sectors": ["FOOD_PROCESSING"],
                "max_investment": 10000000.0,
                "states": ["ALL"]
            },
            "required_documents": ["PAN_CARD", "RENT_AGREEMENT", "BANK_SANCTION_LETTER", "PROJECT_REPORT"],
            "official_portal_url": "https://pmfme.mofpi.gov.in"
        },
        {
            "code": "PMKSY_INFRASTRUCTURE_GRANT",
            "name": "Pradhan Mantri Kisan SAMPADA Yojana (PMKSY) Infrastructure Grant",
            "department": "Ministry of Food Processing Industries (MoFPI)",
            "category": SchemeCategory.INFRASTRUCTURE_GRANT,
            "benefit_summary": "35% to 50% Capital Grant up to ₹50 Lakhs for creation of cold chain & food processing clusters.",
            "max_benefit_amount": 5000000.0,
            "eligibility_conditions": {
                "sectors": ["FOOD_PROCESSING"],
                "min_investment": 20000000.0,
                "states": ["ALL"]
            },
            "required_documents": ["PAN_CARD", "GST_IN", "RENT_AGREEMENT", "CHARTERED_ACCOUNTANT_CERTIFICATE", "DETAILED_PROJECT_REPORT"],
            "official_portal_url": "https://mofpi.gov.in/pmksy"
        },
        {
            "code": "MAHA_PSI_CAPITAL_INCENTIVE",
            "name": "Maharashtra Package Scheme of Incentives (PSI 2026) - Food Processing",
            "department": "Industries Department, Government of Maharashtra / MAITRI",
            "category": SchemeCategory.INTEREST_SUBVENTION,
            "benefit_summary": "5% Interest Subvention for 5 years + Electricity Duty Exemption for MIDC/Industrial area units.",
            "max_benefit_amount": 2500000.0,
            "eligibility_conditions": {
                "sectors": ["FOOD_PROCESSING"],
                "states": ["MAHARASHTRA"],
                "premises_types": ["MIDC_PLOT", "INDUSTRIAL_AREA"]
            },
            "required_documents": ["PAN_CARD", "RENT_AGREEMENT", "ELECTRICITY_BILL", "MAITRI_REGISTRATION_CERT"],
            "official_portal_url": "https://maitri.mahaonline.gov.in"
        },
        {
            "code": "MSME_INTEREST_SUBVENTION",
            "name": "Central MSME Credit & Interest Subvention Scheme",
            "department": "Ministry of Micro, Small & Medium Enterprises (MSME)",
            "category": SchemeCategory.INTEREST_SUBVENTION,
            "benefit_summary": "2% Interest Subvention on fresh or incremental working capital loans up to ₹1 Crore.",
            "max_benefit_amount": 500000.0,
            "eligibility_conditions": {
                "sectors": ["FOOD_PROCESSING", "MANUFACTURING"],
                "max_turnover": 50000000.0,
                "states": ["ALL"]
            },
            "required_documents": ["PAN_CARD", "UDYAM_REGISTRATION", "BANK_LOAN_SANCTION"],
            "official_portal_url": "https://udyamregistration.gov.in"
        }
    ]

    @classmethod
    async def seed_default_schemes(cls, db: AsyncSession):
        """Seed default government incentive schemes into database if empty."""
        res = await db.execute(select(Scheme))
        existing = res.scalars().all()
        if not existing:
            for item in cls.DEFAULT_SCHEMES:
                scheme = Scheme(
                    code=item["code"],
                    name=item["name"],
                    department=item["department"],
                    category=item["category"],
                    benefit_summary=item["benefit_summary"],
                    max_benefit_amount=item["max_benefit_amount"],
                    eligibility_conditions=item["eligibility_conditions"],
                    required_documents=item["required_documents"],
                    official_portal_url=item["official_portal_url"],
                    is_active=True
                )
                db.add(scheme)
            await db.commit()
            logger.info("Default government incentive schemes seeded successfully.")

    @classmethod
    async def _evaluate_schemes_with_gemini(
        cls,
        api_key: str,
        business: Business
    ) -> Optional[BusinessSchemeMatchesResponse]:
        """Query Gemini 2.0 Flash AI API for real, tailored government schemes."""
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"

        prompt = f"""
You are NIRVAAN, an expert Indian Government Incentive & Scheme Matcher AI.
Analyze the following business profile and return ALL applicable real Indian Central & State Government incentive, subsidy, and capital grant schemes tailored specifically to this business:

BUSINESS PROFILE:
- Business Name: {business.name}
- Sector / Business Type: {business.sector} ({business.sub_sector})
- Location: State: {business.state}, District: {business.district}, City: {business.city}
- Scale: Investment Amount: ₹{business.investment_amount:,.2f}, Employee Count: {business.employee_count}, Expected Turnover: ₹{business.expected_turnover:,.2f}
- Premises Type: {business.premises_type}
- Operational Stage: {business.operational_stage}
- Activity / Description: {json.dumps(business.flexible_attributes)}

INSTRUCTIONS:
1. Identify 3 to 5 REAL Indian Central or State Government schemes applicable for this specific sector ({business.sector}), location ({business.state}), and investment size.
2. For each scheme, calculate the realistic estimated benefit amount in INR based on scheme guidelines (e.g. 35% capital subsidy, interest subvention, infrastructure grants).
3. List 2 to 3 specific eligibility reasons explaining why this business profile qualifies.
4. List required documents for application (e.g., PAN_CARD, GST_IN, UDYAM_REGISTRATION, PROJECT_REPORT, RENT_AGREEMENT).
5. Provide official government portal URL.

Return ONLY a valid JSON object matching this structure:
{{
  "total_potential_benefit": 7500000.00,
  "matches": [
    {{
      "code": "SCHEME_CODE",
      "name": "Full Government Scheme Name",
      "department": "Ministry or Department Name",
      "category": "CAPITAL_SUBSIDY",
      "match_status": "MATCHED",
      "estimated_benefit_amount": 3500000.00,
      "benefit_summary": "35% Credit-Linked Capital Subsidy up to ₹35 Lakhs...",
      "eligibility_reasons": ["Sector qualifies under MoFPI central mandate", "Investment amount is within ceiling"],
      "ineligibility_reasons": [],
      "required_documents": ["PAN_CARD", "GST_IN", "UDYAM_REGISTRATION"],
      "official_portal_url": "https://official-portal-url.gov.in"
    }}
  ]
}}
"""

        payload = {
            "contents": [
                {
                    "parts": [{"text": prompt}]
                }
            ],
            "generationConfig": {
                "temperature": 0.2,
                "response_mime_type": "application/json"
            }
        }

        async with httpx.AsyncClient(timeout=25.0) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                text_resp = data["candidates"][0]["content"]["parts"][0]["text"]
                clean_json = re.sub(r'```json\s*|\s*```', '', text_resp).strip()
                res_obj = json.loads(clean_json)

                matched_count = 0
                conditional_count = 0
                total_benefit = float(res_obj.get("total_potential_benefit", 0.0))
                matches_out: List[SchemeMatchResultOut] = []

                for m in res_obj.get("matches", []):
                    status_str = (m.get("match_status") or "MATCHED").upper()
                    if status_str == "MATCHED":
                        matched_count += 1
                    elif status_str == "CONDITIONAL":
                        conditional_count += 1

                    cat_val = (m.get("category") or "CAPITAL_SUBSIDY").upper()
                    if cat_val not in ["CAPITAL_SUBSIDY", "INTEREST_SUBVENTION", "INFRASTRUCTURE_GRANT"]:
                        cat_val = "CAPITAL_SUBSIDY"

                    matches_out.append(
                        SchemeMatchResultOut(
                            scheme_id=uuid.uuid4(),
                            code=m.get("code", "SCHEME_CODE"),
                            name=m.get("name", "Government Incentive Scheme"),
                            department=m.get("department", "Government Ministry"),
                            category=cat_val,
                            match_status=status_str,
                            eligibility_reasons=m.get("eligibility_reasons", []),
                            ineligibility_reasons=m.get("ineligibility_reasons", []),
                            estimated_benefit_amount=float(m.get("estimated_benefit_amount", 0.0)),
                            benefit_summary=m.get("benefit_summary", ""),
                            required_documents=m.get("required_documents", []),
                            official_portal_url=m.get("official_portal_url", "https://india.gov.in")
                        )
                    )

                logger.info(f"Gemini 2.0 Flash AI successfully evaluated {len(matches_out)} real schemes for business {business.id}")
                return BusinessSchemeMatchesResponse(
                    business_id=business.id,
                    total_schemes_evaluated=len(matches_out),
                    matched_count=matched_count,
                    conditional_count=conditional_count,
                    total_potential_benefit=round(total_benefit, 2),
                    matches=matches_out
                )
        return None

    @classmethod
    async def match_schemes_for_business(
        cls,
        db: AsyncSession,
        business_id: uuid.UUID
    ) -> BusinessSchemeMatchesResponse:
        """
        Evaluate all active government schemes against a business profile,
        returning eligibility matches, reasons, estimated subsidy benefit amounts, and document checklists.
        Uses Gemini 2.0 Flash AI model when API key is available.
        """
        # Ensure default schemes are seeded
        await cls.seed_default_schemes(db)

        res = await db.execute(select(Business).where(Business.id == business_id))
        business = res.scalars().first()
        if not business:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Business profile not found"
            )

        # 1. Attempt Gemini 2.0 Flash AI evaluation
        raw_key = settings.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY", "")
        api_key = raw_key.split(",")[0].strip() if raw_key else ""
        if api_key:
            try:
                gemini_res = await cls._evaluate_schemes_with_gemini(api_key, business)
                if gemini_res and len(gemini_res.matches) > 0:
                    return gemini_res
            except Exception as e:
                logger.warning(f"Gemini AI scheme evaluation fallback to rule engine: {str(e)}")

        schemes_res = await db.execute(select(Scheme).where(Scheme.is_active == True))
        schemes = list(schemes_res.scalars().all())

        matched_count = 0
        conditional_count = 0
        total_potential_benefit = 0.0
        match_results: List[SchemeMatchResultOut] = []

        biz_sector = (business.sector or "").upper()
        biz_state = (business.state or "").upper()
        biz_turnover = float(business.expected_turnover or 0.0)
        biz_investment = float(business.investment_amount or 0.0)
        biz_premises = (business.premises_type or "").upper()

        for s in schemes:
            conds = s.eligibility_conditions or {}
            reasons: List[str] = []
            ineligibility: List[str] = []

            # 1. Sector Matching
            allowed_sectors = [sec.upper() for sec in conds.get("sectors", ["ALL"])]
            if "ALL" in allowed_sectors or biz_sector in allowed_sectors:
                reasons.append(f"Sector '{business.sector}' qualifies under scheme mandate.")
            else:
                ineligibility.append(f"Scheme requires sector in {allowed_sectors}, but business is '{business.sector}'.")

            # 2. State Jurisdiction Matching
            allowed_states = [st.upper() for st in conds.get("states", ["ALL"])]
            if "ALL" in allowed_states or biz_state in allowed_states:
                reasons.append(f"State '{business.state}' qualifies under scheme jurisdiction.")
            else:
                ineligibility.append(f"Scheme restricted to states {allowed_states}, but business is located in '{business.state}'.")

            # 3. Investment & Turnover Thresholds
            max_inv = float(conds.get("max_investment", 0.0))
            if max_inv > 0 and biz_investment > max_inv:
                ineligibility.append(f"Investment ₹{biz_investment:,.0f} exceeds maximum ceiling of ₹{max_inv:,.0f}.")
            elif max_inv > 0:
                reasons.append(f"Investment ₹{biz_investment:,.0f} is within ceiling ₹{max_inv:,.0f}.")

            min_inv = float(conds.get("min_investment", 0.0))
            if min_inv > 0 and biz_investment < min_inv:
                ineligibility.append(f"Investment ₹{biz_investment:,.0f} is below minimum threshold of ₹{min_inv:,.0f}.")
            elif min_inv > 0:
                reasons.append(f"Investment ₹{biz_investment:,.0f} meets minimum requirement ₹{min_inv:,.0f}.")

            # 4. Premises Type Check
            allowed_premises = [p.upper() for p in conds.get("premises_types", [])]
            if allowed_premises and biz_premises in allowed_premises:
                reasons.append(f"Premises type '{business.premises_type}' qualifies for location bonus.")
            elif allowed_premises:
                reasons.append(f"Note: Preferential benefits for units located in {allowed_premises}.")

            # Determine Match Status & Benefit Estimate
            if not ineligibility:
                match_status = "MATCHED"
                matched_count += 1
                # Estimate subsidy as min(max_benefit_amount, 35% of investment)
                estimated_benefit = min(s.max_benefit_amount, max(200000.0, biz_investment * 0.35))
                total_potential_benefit += estimated_benefit
            elif len(ineligibility) == 1 and "Investment" in ineligibility[0]:
                match_status = "CONDITIONAL"
                conditional_count += 1
                estimated_benefit = s.max_benefit_amount * 0.5
                total_potential_benefit += estimated_benefit
            else:
                match_status = "INELIGIBLE"
                estimated_benefit = 0.0

            match_results.append(
                SchemeMatchResultOut(
                    scheme_id=s.id,
                    code=s.code,
                    name=s.name,
                    department=s.department,
                    category=s.category.value,
                    match_status=match_status,
                    eligibility_reasons=reasons,
                    ineligibility_reasons=ineligibility,
                    estimated_benefit_amount=round(estimated_benefit, 2),
                    benefit_summary=s.benefit_summary,
                    required_documents=s.required_documents or [],
                    official_portal_url=s.official_portal_url
                )
            )

        logger.info(f"Scheme matching for business {business_id}: {matched_count} matched, {conditional_count} conditional. Total Benefit: ₹{total_potential_benefit:,.2f}")

        return BusinessSchemeMatchesResponse(
            business_id=business_id,
            total_schemes_evaluated=len(schemes),
            matched_count=matched_count,
            conditional_count=conditional_count,
            total_potential_benefit=round(total_potential_benefit, 2),
            matches=match_results
        )
