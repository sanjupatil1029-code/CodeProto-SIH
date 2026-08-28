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
                    # This branch is definitely False, and not due to missing info.
                    # So the entire AND group is definitely False.
                    return False, []
                if missing:
                    group_missing.extend(missing)
            if group_missing:
                # Some fields are missing, but no branch is definitely False.
                # So it is potentially True, pending these missing fields.
                return True, list(set(group_missing))
            return True, []

        # Handle logical OR group
        if "or" in node:
            sub_conditions = node["or"]
            group_missing = []
            for cond in sub_conditions:
                res, missing = RuleEngineService.evaluate_node(cond, context)
                if res and not missing:
                    # One branch is definitely True! So the entire OR group is True.
                    return True, []
                if missing:
                    group_missing.extend(missing)
            # If no branch is definitely True, check if there are missing fields
            if group_missing:
                # Since no branch is definitely True, it is potentially True if one of the missing fields makes a branch True.
                return True, list(set(group_missing))
            return False, []

        # Leaf node: {"field": "...", "operator": "...", "value": ...}
        field = node.get("field")
        operator = node.get("operator")
        target_val = node.get("value")

        if not field or not operator:
            return True, []

        # Retrieve value from business context or flexible_attributes
        val = context.get(field)
        if val is None and "flexible_attributes" in context:
            val = context["flexible_attributes"].get(field)

        if val is None:
            # The field is missing!
            if operator == "is_null":
                return True, []
            return False, [field]

        # Convert target_val to float if field is numeric to ensure accurate comparison
        def to_float(v):
            try:
                return float(v)
            except (ValueError, TypeError):
                return None

        # Comparison logic
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
                return str(val) in [str(v) for v in target_val], []
            return False, []
        elif operator == "not_in":
            if isinstance(target_val, list):
                return str(val) not in [str(v) for v in target_val], []
            return True, []
        elif operator == "is_null":
            return False, []  # Since val is not None, is_null is False

        return False, []

    @classmethod
    async def evaluate_business_approvals(cls, db: AsyncSession, business_id: uuid.UUID) -> List[RuleEvaluationResult]:
        """Runs the rule engine against a specific business profile and returns results."""
        # 1. Fetch Business
        result = await db.execute(select(Business).where(Business.id == business_id))
        business = result.scalars().first()
        if not business:
            return []

        # 2. Get all ACTIVE rules
        rules_result = await db.execute(
            select(ApprovalRule).where(ApprovalRule.status == RuleStatus.ACTIVE)
        )
        active_rules = rules_result.scalars().all()

        # 3. Create context dictionary
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

        # 4. Evaluate each rule
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
        # Check if there is an active rule with the same code
        existing_result = await db.execute(
            select(ApprovalRule)
            .where(ApprovalRule.code == schema.code)
            .where(ApprovalRule.status == RuleStatus.ACTIVE)
        )
        active_rule = existing_result.scalars().first()

        if active_rule:
            # Mark existing rule as SUPERSEDED
            active_rule.status = RuleStatus.SUPERSEDED
            active_rule.effective_to = datetime.utcnow()
            db.add(active_rule)

        # Create new rule version
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
        """Seed default document types and approval rules if none exist."""
        # Seed Document Types
        doc_count_result = await db.execute(select(DocumentType))
        if not doc_count_result.scalars().first():
            logger.info("Seeding default document types...")
            default_docs = [
                DocumentType(code="PAN_CARD", name="PAN Card of Business", description="Permanent Account Number card issued by the Income Tax Department."),
                DocumentType(code="RENT_AGREEMENT", name="Rental / Lease Agreement", description="Registered rental or lease agreement of the business premises."),
                DocumentType(code="GST_IN", name="GST Registration Certificate", description="Goods and Services Tax Registration Certificate."),
                DocumentType(code="FIRE_NOC_APPLICATION", name="Fire NOC Application Form", description="Completed application form along with building plans for Fire Department review."),
                DocumentType(code="WATER_BILL", name="Water Connection/Utility Bill", description="Recent water or utility bill showing the connection details.")
            ]
            db.add_all(default_docs)
            await db.commit()

        # Seed Approval Rules
        rule_count_result = await db.execute(select(ApprovalRule))
        if not rule_count_result.scalars().first():
            logger.info("Seeding default regulatory rules...")
            default_rules = [
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
                        "field": "expected_turnover",
                        "operator": "greater_than",
                        "value": 2000000
                    },
                    required_document_types=["PAN_CARD", "RENT_AGREEMENT"],
                    dependencies=[],
                    explanation="Applicable as the expected turnover exceeds the Central GST registration threshold of Rs. 20 Lakhs.",
                    version="1.0.0",
                    status=RuleStatus.ACTIVE
                ),
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
                        "field": "sector",
                        "operator": "equals",
                        "value": "FOOD_PROCESSING"
                    },
                    required_document_types=["PAN_CARD", "RENT_AGREEMENT", "GST_IN"],
                    dependencies=["GST_REGISTRATION"],
                    explanation="Every business engaged in manufacturing, processing, or packaging of food products in India requires an FSSAI License.",
                    version="1.0.0",
                    status=RuleStatus.ACTIVE
                ),
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
                        "or": [
                            {
                                "field": "employee_count",
                                "operator": "greater_than",
                                "value": 20
                            },
                            {
                                "field": "investment_amount",
                                "operator": "greater_than",
                                "value": 10000000
                            },
                            {
                                "field": "premises_type",
                                "operator": "equals",
                                "value": "MIDC_PLOT"
                            }
                        ]
                    },
                    required_document_types=["RENT_AGREEMENT", "FIRE_NOC_APPLICATION"],
                    dependencies=[],
                    explanation="Required for industrial units with over 20 employees, substantial capital investment (>Rs. 1 Crore), or operating on MIDC plots to ensure fire safety compliance.",
                    version="1.0.0",
                    status=RuleStatus.ACTIVE
                ),
                ApprovalRule(
                    code="WATER_CONSENT",
                    name="Consent to Establish (Water Pollution Control)",
                    category=ApprovalCategory.NOC,
                    jurisdiction=JurisdictionType.STATE,
                    state="Maharashtra",
                    responsible_authority="Maharashtra Pollution Control Board (MPCB)",
                    sla_days=45,
                    inspection_required=True,
                    renewal_required=True,
                    renewal_interval_months=36,
                    conditions={
                        "and": [
                            {
                                "field": "sector",
                                "operator": "equals",
                                "value": "FOOD_PROCESSING"
                            },
                            {
                                "field": "water_discharge_required",
                                "operator": "equals",
                                "value": "true"
                            }
                        ]
                    },
                    required_document_types=["PAN_CARD", "RENT_AGREEMENT", "WATER_BILL"],
                    dependencies=["GST_REGISTRATION"],
                    explanation="Required by the State Pollution Control Board for food processing businesses that discharge wastewater during operations.",
                    version="1.0.0",
                    status=RuleStatus.ACTIVE
                )
            ]
            db.add_all(default_rules)
            await db.commit()
