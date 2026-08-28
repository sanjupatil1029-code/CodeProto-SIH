import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.business import Business
from app.models.rules import ApprovalRule, DocumentType, RuleStatus, JurisdictionType, ApprovalCategory
from app.schemas.rules import ApprovalRuleCreate, ApprovalRuleUpdate, RuleEvaluationResult
from app.core.logging import logger


class RuleEngineService:

    @staticmethod
    def evaluate_node(node: dict, context: dict) -> Tuple[bool, List[str]]:
        """
        Evaluate a single condition node recursively.
        Returns (is_satisfied_or_potential, missing_fields)
        """
        if not node:
            return True, []

        # Handle logical AND group
        if "and" in node:
            sub_conditions = node["and"]
            group_missing = []
            for cond in sub_conditions:
                res, missing = RuleEngineService.evaluate_node(cond, context)
                if not res and not missing:
                    return False, []
                if missing:
                    group_missing.extend(missing)
            if group_missing:
                return True, list(set(group_missing))
            return True, []

        # Handle logical OR group
        if "or" in node:
            sub_conditions = node["or"]
            group_missing = []
            for cond in sub_conditions:
                res, missing = RuleEngineService.evaluate_node(cond, context)
                if res and not missing:
                    return True, []
                if missing:
                    group_missing.extend(missing)
            if group_missing:
                return True, list(set(group_missing))
            return False, []

        # Leaf node: {"field": "...", "operator": "...", "value": ...}
        field = node.get("field")
        operator = node.get("operator")
        target_val = node.get("value")

        if not field or not operator:
            return True, []

        val = context.get(field)
        if val is None and "flexible_attributes" in context:
            val = context["flexible_attributes"].get(field)

        if val is None:
            if operator == "is_null":
                return True, []
            return False, [field]

        def to_float(v):
            try:
                return float(v)
            except (ValueError, TypeError):
                return None

        if operator == "equals":
            return str(val).lower() == str(target_val).lower(), []
        elif operator == "not_equals":
            return str(val).lower() != str(target_val).lower(), []
        elif operator == "greater_than":
            v_f, t_f = to_float(val), to_float(target_val)
            if v_f is not None and t_f is not None:
                return v_f > t_f, []
            return False, []
        elif operator == "greater_than_or_equal":
            v_f, t_f = to_float(val), to_float(target_val)
            if v_f is not None and t_f is not None:
                return v_f >= t_f, []
            return False, []
        elif operator == "less_than":
            v_f, t_f = to_float(val), to_float(target_val)
            if v_f is not None and t_f is not None:
                return v_f < t_f, []
            return False, []
        elif operator == "less_than_or_equal":
            v_f, t_f = to_float(val), to_float(target_val)
            if v_f is not None and t_f is not None:
                return v_f <= t_f, []
            return False, []
        elif operator == "in":
            if isinstance(target_val, list):
                return str(val).lower() in [str(v).lower() for v in target_val], []
            return False, []
        elif operator == "not_in":
            if isinstance(target_val, list):
                return str(val).lower() not in [str(v).lower() for v in target_val], []
            return True, []
        elif operator == "is_null":
            return False, []

        return False, []

    @classmethod
    async def evaluate_business_approvals(cls, db: AsyncSession, business_id: uuid.UUID) -> List[RuleEvaluationResult]:
        """Runs the rule engine against a specific business profile and returns results."""
        result = await db.execute(select(Business).where(Business.id == business_id))
        business = result.scalars().first()
        if not business:
            return []

        rules_result = await db.execute(
            select(ApprovalRule).where(ApprovalRule.status == RuleStatus.ACTIVE)
        )
        active_rules = rules_result.scalars().all()

        context = {
            "name": business.name,
            "sector": business.sector,
            "sub_sector": business.sub_sector,
            "state": business.state,
            "district": business.district,
            "city": business.city,
            "investment_amount": float(business.investment_amount),
            "employee_count": business.employee_count,
            "expected_turnover": float(business.expected_turnover),
            "operational_stage": business.operational_stage,
            "ownership_type": business.ownership_type,
            "premises_type": business.premises_type,
            "flexible_attributes": business.flexible_attributes
        }

        eval_results = []
        for rule in active_rules:
            is_satisfied, missing_fields = cls.evaluate_node(rule.conditions, context)
            
            if missing_fields:
                status = "NEEDS_MORE_INFO"
            elif is_satisfied:
                status = "APPLICABLE"
            else:
                status = "NOT_APPLICABLE"

            eval_results.append(
                RuleEvaluationResult(
                    rule_code=rule.code,
                    name=rule.name,
                    category=rule.category,
                    responsible_authority=rule.responsible_authority,
                    status=status,
                    explanation=rule.explanation or f"Rule evaluation determined status: {status}",
                    sla_days=rule.sla_days,
                    inspection_required=rule.inspection_required,
                    required_document_types=rule.required_document_types,
                    dependencies=rule.dependencies,
                    missing_fields=missing_fields
                )
            )

        return eval_results

    @classmethod
    async def create_rule(cls, db: AsyncSession, schema: ApprovalRuleCreate) -> ApprovalRule:
        """Create a new rule. If code already exists, supersede the old version."""
        existing_result = await db.execute(
            select(ApprovalRule)
            .where(ApprovalRule.code == schema.code)
            .where(ApprovalRule.status == RuleStatus.ACTIVE)
        )
        active_rule = existing_result.scalars().first()

        if active_rule:
            active_rule.status = RuleStatus.SUPERSEDED
            active_rule.effective_to = datetime.utcnow()
            db.add(active_rule)

        new_rule = ApprovalRule(
            code=schema.code,
            name=schema.name,
            category=schema.category,
            jurisdiction=schema.jurisdiction,
            state=schema.state,
            responsible_authority=schema.responsible_authority,
            sla_days=schema.sla_days,
            inspection_required=schema.inspection_required,
            renewal_required=schema.renewal_required,
            renewal_interval_months=schema.renewal_interval_months,
            conditions=schema.conditions,
            required_document_types=schema.required_document_types,
            dependencies=schema.dependencies,
            explanation=schema.explanation,
            version=schema.version,
            status=RuleStatus.ACTIVE,
            effective_from=datetime.utcnow()
        )
        db.add(new_rule)
        await db.commit()
        await db.refresh(new_rule)
        logger.info(f"Published rule '{new_rule.name}' code: {new_rule.code} version: {new_rule.version}")
        return new_rule

    @classmethod
    async def get_all_rules(cls, db: AsyncSession) -> List[ApprovalRule]:
        """List all active approval rules."""
        result = await db.execute(
            select(ApprovalRule).where(ApprovalRule.status == RuleStatus.ACTIVE)
        )
        return list(result.scalars().all())

    @classmethod
    async def seed_default_rules(cls, db: AsyncSession):
        """Seed document types and approval rules for all trained sectors if missing."""
        # Update existing generic rules if present to exclude trained sectors
        all_rules_res = await db.execute(select(ApprovalRule))
        all_existing_rules = all_rules_res.scalars().all()
        existing_codes = set(r.code for r in all_existing_rules)
        
        for r in all_existing_rules:
            if r.code in ["GST_REGISTRATION", "FIRE_NOC"]:
                r.conditions = {
                    "and": [
                        {"field": "expected_turnover", "operator": "greater_than", "value": 2000000},
                        {"field": "sector", "operator": "not_in", "value": ["SUGAR_FACTORY", "JEWELLERY_SHOP"]}
                    ]
                }
                db.add(r)
            elif r.code == "FSSAI_LICENSE":
                r.conditions = {
                    "and": [
                        {"field": "sector", "operator": "equals", "value": "FOOD_PROCESSING"},
                        {"field": "sector", "operator": "not_in", "value": ["SUGAR_FACTORY", "JEWELLERY_SHOP"]}
                    ]
                }
                db.add(r)
        await db.commit()

        new_rules: List[ApprovalRule] = []

        # Default Generic & Food Processing Rules
        if "GST_REGISTRATION" not in existing_codes:
            new_rules.append(
                ApprovalRule(
                    code="GST_REGISTRATION",
                    name="GST Registration Certificate",
                    category=ApprovalCategory.REGISTRATION,
                    jurisdiction=JurisdictionType.CENTRAL,
                    responsible_authority="Department of Revenue, Ministry of Finance",
                    sla_days=7,
                    inspection_required=False,
                    renewal_required=False,
                    conditions={
                        "and": [
                            {"field": "expected_turnover", "operator": "greater_than", "value": 2000000},
                            {"field": "sector", "operator": "not_in", "value": ["SUGAR_FACTORY", "JEWELLERY_SHOP"]}
                        ]
                    },
                    required_document_types=["PAN_CARD", "RENT_AGREEMENT"],
                    dependencies=[],
                    explanation="Applicable as expected turnover exceeds GST registration threshold of Rs. 20 Lakhs.",
                    version="1.0.0",
                    status=RuleStatus.ACTIVE
                )
            )

        if "FSSAI_LICENSE" not in existing_codes:
            new_rules.append(
                ApprovalRule(
                    code="FSSAI_LICENSE",
                    name="FSSAI Food Business License",
                    category=ApprovalCategory.LICENSE,
                    jurisdiction=JurisdictionType.CENTRAL,
                    responsible_authority="Food Safety and Standards Authority of India (FSSAI)",
                    sla_days=30,
                    inspection_required=True,
                    renewal_required=True,
                    renewal_interval_months=12,
                    conditions={
                        "and": [
                            {"field": "sector", "operator": "equals", "value": "FOOD_PROCESSING"},
                            {"field": "sector", "operator": "not_in", "value": ["SUGAR_FACTORY"]}
                        ]
                    },
                    required_document_types=["PAN_CARD", "RENT_AGREEMENT", "GST_IN"],
                    dependencies=["GST_REGISTRATION"],
                    explanation="Every food processing business in India requires an FSSAI License.",
                    version="1.0.0",
                    status=RuleStatus.ACTIVE
                )
            )

        if "FIRE_NOC" not in existing_codes:
            new_rules.append(
                ApprovalRule(
                    code="FIRE_NOC",
                    name="Fire Safety NOC",
                    category=ApprovalCategory.NOC,
                    jurisdiction=JurisdictionType.STATE,
                    state="Maharashtra",
                    responsible_authority="Maharashtra Fire Services Bureau",
                    sla_days=15,
                    inspection_required=True,
                    renewal_required=True,
                    renewal_interval_months=12,
                    conditions={
                        "and": [
                            {
                                "or": [
                                    {"field": "employee_count", "operator": "greater_than", "value": 20},
                                    {"field": "investment_amount", "operator": "greater_than", "value": 10000000},
                                    {"field": "premises_type", "operator": "equals", "value": "MIDC_PLOT"}
                                ]
                            },
                            {"field": "sector", "operator": "not_in", "value": ["SUGAR_FACTORY", "JEWELLERY_SHOP"]}
                        ]
                    },
                    required_document_types=["RENT_AGREEMENT", "FIRE_NOC_APPLICATION"],
                    dependencies=[],
                    explanation="Required for industrial units with >20 employees, substantial capital, or operating on MIDC plots.",
                    version="1.0.0",
                    status=RuleStatus.ACTIVE
                )
            )

        # ----------------------------------------------------
        # SECTOR 1: SUGAR FACTORY (19 Statutory Steps)
        # ----------------------------------------------------
        sugar_rules = [
            ("SUGAR_PAN_TAN", "Business & Entity Registration + PAN/TAN", ApprovalCategory.REGISTRATION, JurisdictionType.CENTRAL, "Ministry of Corporate Affairs / Income Tax Department", 7, False, False, None, {"field": "sector", "operator": "equals", "value": "SUGAR_FACTORY"}, ["PAN_CARD"], [], "Step 1: Entity formation and PAN/TAN registration."),
            ("SUGAR_NA_LAND", "Industrial/NA Land Conversion & Title Clear", ApprovalCategory.NOC, JurisdictionType.STATE, "District Collectorate / Land Revenue Dept", 45, True, False, None, {"field": "sector", "operator": "equals", "value": "SUGAR_FACTORY"}, ["RENT_AGREEMENT"], ["SUGAR_PAN_TAN"], "Step 2: Non-Agricultural land conversion and title clearance."),
            ("SUGAR_IEM", "Industrial Entrepreneur Memorandum (IEM)", ApprovalCategory.REGISTRATION, JurisdictionType.CENTRAL, "DPIIT, Ministry of Commerce & Industry", 15, False, False, None, {"field": "sector", "operator": "equals", "value": "SUGAR_FACTORY"}, ["PAN_CARD"], ["SUGAR_PAN_TAN"], "Step 3: IEM Registration for sugar manufacturing."),
            ("SUGAR_DISTANCE_CERT", "Distance Certificate & Cane-Zone Allocation", ApprovalCategory.NOC, JurisdictionType.STATE, "Commissioner of Sugar / Sugarcane Directorate", 30, True, False, None, {"field": "sector", "operator": "equals", "value": "SUGAR_FACTORY"}, ["RENT_AGREEMENT"], ["SUGAR_NA_LAND", "SUGAR_IEM"], "Step 4: Statutory 15km distance certificate & sugarcane zone allocation."),
            ("SUGAR_STATE_APPROVAL", "State High-Power Committee Sector Approval", ApprovalCategory.NOC, JurisdictionType.STATE, "State Industries Department / Cabinet Committee", 60, False, False, None, {"field": "sector", "operator": "equals", "value": "SUGAR_FACTORY"}, ["PAN_CARD"], ["SUGAR_DISTANCE_CERT"], "Step 5: High-Power Committee approval for new sugar unit."),
            ("SUGAR_BUILDING_PLAN", "Factory Site & Building Plan Approval", ApprovalCategory.NOC, JurisdictionType.LOCAL, "Directorate of Industrial Safety & Health (DISH)", 30, True, False, None, {"field": "sector", "operator": "equals", "value": "SUGAR_FACTORY"}, ["RENT_AGREEMENT"], ["SUGAR_STATE_APPROVAL"], "Step 6: Factory layout and structural building approval."),
            ("SUGAR_EC_CLEARANCE", "Environmental Clearance (EC)", ApprovalCategory.NOC, JurisdictionType.CENTRAL, "Ministry of Environment, Forest & Climate Change (MoEFCC) / SEIAA", 90, True, True, 60, {"field": "sector", "operator": "equals", "value": "SUGAR_FACTORY"}, ["PAN_CARD"], ["SUGAR_BUILDING_PLAN"], "Step 7: Environmental Clearance for sugar processing plant."),
            ("SUGAR_KSPCB_CTE", "State Pollution Control Board Consent to Establish (CTE)", ApprovalCategory.NOC, JurisdictionType.STATE, "State Pollution Control Board (KSPCB / MPCB)", 45, True, False, None, {"field": "sector", "operator": "equals", "value": "SUGAR_FACTORY"}, ["RENT_AGREEMENT"], ["SUGAR_EC_CLEARANCE"], "Step 8: Water and Air Pollution Consent to Establish (CTE)."),
            ("SUGAR_FIRE_WATER_NOC", "Fire NOC & Ground Water Abstraction Permission", ApprovalCategory.NOC, JurisdictionType.STATE, "State Fire Services & Central Ground Water Authority (CGWA)", 30, True, True, 12, {"field": "sector", "operator": "equals", "value": "SUGAR_FACTORY"}, ["FIRE_NOC_APPLICATION"], ["SUGAR_KSPCB_CTE"], "Step 9: Fire NOC and industrial water extraction permission."),
            ("SUGAR_FACTORY_LICENSE", "Factory License (Factories Act 1948)", ApprovalCategory.LICENSE, JurisdictionType.STATE, "Department of Factories & Boilers / DISH", 30, True, True, 12, {"field": "sector", "operator": "equals", "value": "SUGAR_FACTORY"}, ["RENT_AGREEMENT"], ["SUGAR_BUILDING_PLAN", "SUGAR_FIRE_WATER_NOC"], "Step 10: Factory operating license."),
            ("SUGAR_BOILER_REGISTRATION", "High-Pressure Industrial Boiler Registration", ApprovalCategory.REGISTRATION, JurisdictionType.STATE, "Chief Inspector of Boilers", 21, True, True, 12, {"field": "sector", "operator": "equals", "value": "SUGAR_FACTORY"}, ["PAN_CARD"], ["SUGAR_FACTORY_LICENSE"], "Step 11: Registration & inspection of steam boilers."),
            ("SUGAR_ELECTRICAL_SAFETY", "Electrical Inspectorate Safety Approval", ApprovalCategory.NOC, JurisdictionType.STATE, "Chief Electrical Inspectorate", 15, True, True, 36, {"field": "sector", "operator": "equals", "value": "SUGAR_FACTORY"}, ["RENT_AGREEMENT"], ["SUGAR_BUILDING_PLAN"], "Step 12: High-voltage electrical installation safety cert."),
            ("SUGAR_GST_BANK", "GST Registration & Bank Account Setup", ApprovalCategory.REGISTRATION, JurisdictionType.CENTRAL, "Department of Revenue, Ministry of Finance", 7, False, False, None, {"field": "sector", "operator": "equals", "value": "SUGAR_FACTORY"}, ["PAN_CARD", "GST_IN"], ["SUGAR_PAN_TAN"], "Step 13: GSTIN registration and commercial bank account."),
            ("SUGAR_LABOUR_EPFO", "Labour, EPFO & ESIC Registrations", ApprovalCategory.REGISTRATION, JurisdictionType.CENTRAL, "Ministry of Labour & Employment / EPFO / ESIC", 10, False, False, None, {"field": "sector", "operator": "equals", "value": "SUGAR_FACTORY"}, ["PAN_CARD"], ["SUGAR_FACTORY_LICENSE"], "Step 14: Employee Provident Fund and ESIC registration."),
            ("SUGAR_FSSAI_LICENSE", "Central FSSAI Sugar Processing License", ApprovalCategory.LICENSE, JurisdictionType.CENTRAL, "Food Safety and Standards Authority of India (FSSAI)", 30, True, True, 12, {"field": "sector", "operator": "equals", "value": "SUGAR_FACTORY"}, ["PAN_CARD", "GST_IN"], ["SUGAR_GST_BANK", "SUGAR_KSPCB_CTE"], "Step 15: FSSAI Central License for sugar manufacturing."),
            ("SUGAR_CRUSHING_LICENSE", "Sugarcane Crushing & Production Permit", ApprovalCategory.LICENSE, JurisdictionType.STATE, "Directorate of Sugar / Agriculture Dept", 15, True, True, 12, {"field": "sector", "operator": "equals", "value": "SUGAR_FACTORY"}, ["PAN_CARD"], ["SUGAR_BOILER_REGISTRATION", "SUGAR_FSSAI_LICENSE"], "Step 16: Annual sugar crushing season permit."),
            ("SUGAR_LEGAL_METROLOGY", "Legal Metrology Weights & Measures Cert", ApprovalCategory.REGISTRATION, JurisdictionType.STATE, "Department of Legal Metrology", 15, True, True, 12, {"field": "sector", "operator": "equals", "value": "SUGAR_FACTORY"}, ["PAN_CARD"], ["SUGAR_FACTORY_LICENSE"], "Step 17: Weighbridge & electronic scale verification cert."),
            ("SUGAR_KSPCB_CTO", "State Pollution Board Consent to Operate (CTO)", ApprovalCategory.NOC, JurisdictionType.STATE, "State Pollution Control Board (KSPCB / MPCB)", 30, True, True, 36, {"field": "sector", "operator": "equals", "value": "SUGAR_FACTORY"}, ["RENT_AGREEMENT"], ["SUGAR_KSPCB_CTE", "SUGAR_CRUSHING_LICENSE"], "Step 18: Consent to Operate (CTO) prior to plant startup."),
            ("SUGAR_RELEASE_ORDER", "Government Sugar Release & Quota Order", ApprovalCategory.REGISTRATION, JurisdictionType.CENTRAL, "Directorate of Sugar & Vegetable Oils, MoFPD", 7, False, False, None, {"field": "sector", "operator": "equals", "value": "SUGAR_FACTORY"}, ["PAN_CARD"], ["SUGAR_CRUSHING_LICENSE", "SUGAR_KSPCB_CTO"], "Step 19: Monthly sugar release quota & dispatch permit.")
        ]

        for code, name, cat, juris, auth, sla, insp, ren, interval, conds, docs, deps, exp in sugar_rules:
            if code not in existing_codes:
                new_rules.append(
                    ApprovalRule(
                        code=code,
                        name=name,
                        category=cat,
                        jurisdiction=juris,
                        responsible_authority=auth,
                        sla_days=sla,
                        inspection_required=insp,
                        renewal_required=ren,
                        renewal_interval_months=interval,
                        conditions=conds,
                        required_document_types=docs,
                        dependencies=deps,
                        explanation=exp,
                        version="1.0.0",
                        status=RuleStatus.ACTIVE
                    )
                )

        # ----------------------------------------------------
        # SECTOR 2: JEWELLERY SHOP (12 Statutory Steps)
        # ----------------------------------------------------
        jewellery_rules = [
            ("JEWELLERY_ENTITY_REG", "Business & Entity Registration (Prop/LLP/Pvt Ltd)", ApprovalCategory.REGISTRATION, JurisdictionType.CENTRAL, "Ministry of Corporate Affairs / Registrar of Firms", 7, False, False, None, {"field": "sector", "operator": "equals", "value": "JEWELLERY_SHOP"}, ["PAN_CARD"], [], "Step 1: Constitution of jewellery business entity."),
            ("JEWELLERY_PAN_BANK", "PAN/TAN & Current Bank Account Setup", ApprovalCategory.REGISTRATION, JurisdictionType.CENTRAL, "Income Tax Department / Scheduled Commercial Bank", 5, False, False, None, {"field": "sector", "operator": "equals", "value": "JEWELLERY_SHOP"}, ["PAN_CARD"], ["JEWELLERY_ENTITY_REG"], "Step 2: PAN/TAN and current account for bullion trade."),
            ("JEWELLERY_RENT_PROOF", "Rent Agreement / Commercial Premises Ownership Proof", ApprovalCategory.OTHER, JurisdictionType.LOCAL, "Sub-Registrar Office / Municipal Corporation", 3, False, False, None, {"field": "sector", "operator": "equals", "value": "JEWELLERY_SHOP"}, ["RENT_AGREEMENT"], ["JEWELLERY_ENTITY_REG"], "Step 3: Premises proof for retail jewellery showroom."),
            ("JEWELLERY_MUNICIPAL_LIC", "Municipality / Local Authority License", ApprovalCategory.LICENSE, JurisdictionType.LOCAL, "Municipal Corporation / City Nagar Nigam", 15, True, True, 12, {"field": "sector", "operator": "equals", "value": "JEWELLERY_SHOP"}, ["RENT_AGREEMENT"], ["JEWELLERY_RENT_PROOF"], "Step 4: Local authority commercial premises license."),
            ("JEWELLERY_SHOP_EST", "Shop & Establishment Registration (Gumasta)", ApprovalCategory.REGISTRATION, JurisdictionType.STATE, "State Department of Labour", 7, False, True, 12, {"field": "sector", "operator": "equals", "value": "JEWELLERY_SHOP"}, ["RENT_AGREEMENT", "PAN_CARD"], ["JEWELLERY_RENT_PROOF"], "Step 5: Shop & Establishment License (Gumasta)."),
            ("JEWELLERY_TRADE_LIC", "Municipal Corporation Trade License", ApprovalCategory.LICENSE, JurisdictionType.LOCAL, "Municipal Trade Licensing Authority", 15, True, True, 12, {"field": "sector", "operator": "equals", "value": "JEWELLERY_SHOP"}, ["RENT_AGREEMENT"], ["JEWELLERY_MUNICIPAL_LIC"], "Step 6: Trade license for gold & precious stone dealing."),
            ("JEWELLERY_GST_REG", "GST Registration (Jewellery & HSN Code 7113)", ApprovalCategory.REGISTRATION, JurisdictionType.CENTRAL, "Department of Revenue, Ministry of Finance", 7, False, False, None, {"field": "sector", "operator": "equals", "value": "JEWELLERY_SHOP"}, ["PAN_CARD", "GST_IN"], ["JEWELLERY_PAN_BANK", "JEWELLERY_RENT_PROOF"], "Step 7: GST registration under gold & jewellery HSN 7113."),
            ("JEWELLERY_BIS_REG", "BIS Jeweller Registration Certificate", ApprovalCategory.REGISTRATION, JurisdictionType.CENTRAL, "Bureau of Indian Standards (BIS)", 14, False, True, 60, {"field": "sector", "operator": "equals", "value": "JEWELLERY_SHOP"}, ["PAN_CARD", "GST_IN"], ["JEWELLERY_GST_REG", "JEWELLERY_SHOP_EST"], "Step 8: BIS Hallmarking Jeweller Registration."),
            ("JEWELLERY_HALLMARKING_CERT", "Hallmarking Agreement with Recognised A&H Centre", ApprovalCategory.LICENSE, JurisdictionType.CENTRAL, "BIS Recognised Assaying & Hallmarking Centre", 7, True, True, 12, {"field": "sector", "operator": "equals", "value": "JEWELLERY_SHOP"}, ["PAN_CARD"], ["JEWELLERY_BIS_REG"], "Step 9: Agreement for mandatory gold 6-digit HUID hallmarking."),
            ("JEWELLERY_LEGAL_METROLOGY", "Legal Metrology Weights & Carat Scale Verification", ApprovalCategory.REGISTRATION, JurisdictionType.STATE, "Department of Legal Metrology", 10, True, True, 12, {"field": "sector", "operator": "equals", "value": "JEWELLERY_SHOP"}, ["PAN_CARD"], ["JEWELLERY_SHOP_EST"], "Step 10: Verification and stamping of precision jewellery scales."),
            ("JEWELLERY_LABOUR_EPFO", "Labour, EPFO & ESIC Registrations", ApprovalCategory.REGISTRATION, JurisdictionType.CENTRAL, "Ministry of Labour & Employment", 7, False, False, None, {"field": "sector", "operator": "equals", "value": "JEWELLERY_SHOP"}, ["PAN_CARD"], ["JEWELLERY_SHOP_EST"], "Step 11: Labour and social security compliance."),
            ("JEWELLERY_BILLING_COMPLIANCE", "Hallmarked Jewellery Invoicing & PAN Threshold Compliance", ApprovalCategory.OTHER, JurisdictionType.CENTRAL, "Central Board of Direct Taxes (CBDT)", 3, False, False, None, {"field": "sector", "operator": "equals", "value": "JEWELLERY_SHOP"}, ["PAN_CARD", "GST_IN"], ["JEWELLERY_BIS_REG", "JEWELLERY_GST_REG"], "Step 12: Statutory billing compliance (HUID 6-digit invoice & PAN logging for transactions >Rs. 2 Lakhs).")
        ]

        for code, name, cat, juris, auth, sla, insp, ren, interval, conds, docs, deps, exp in jewellery_rules:
            if code not in existing_codes:
                new_rules.append(
                    ApprovalRule(
                        code=code,
                        name=name,
                        category=cat,
                        jurisdiction=juris,
                        responsible_authority=auth,
                        sla_days=sla,
                        inspection_required=insp,
                        renewal_required=ren,
                        renewal_interval_months=interval,
                        conditions=conds,
                        required_document_types=docs,
                        dependencies=deps,
                        explanation=exp,
                        version="1.0.0",
                        status=RuleStatus.ACTIVE
                    )
                )

        if new_rules:
            db.add_all(new_rules)
            await db.commit()
            logger.info(f"Seeded {len(new_rules)} new regulatory rules for trained sectors (Sugar Factory & Jewellery Shop).")
