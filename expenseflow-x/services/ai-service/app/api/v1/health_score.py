"""
AI Service - Financial Health Scoring Engine
Advanced weighted scoring model for overall financial wellness (0-100)
"""
from typing import Optional, Dict
from datetime import datetime

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter()


# ── Schemas ─────────────────────────────────────────────────────────────────────

class HealthScoreInput(BaseModel):
    user_id: str

    # Financial data inputs
    monthly_income: float = Field(..., gt=0)
    monthly_expenses: float = Field(..., ge=0)
    monthly_savings: float = Field(default=0, ge=0)
    total_savings: float = Field(default=0, ge=0)
    total_debt: float = Field(default=0, ge=0)
    monthly_debt_payment: float = Field(default=0, ge=0)
    emergency_fund: float = Field(default=0, ge=0)
    monthly_investments: float = Field(default=0, ge=0)
    total_investments: float = Field(default=0, ge=0)

    # Behavioral metrics (0-100)
    budget_adherence_pct: float = Field(default=50, ge=0, le=100)
    savings_consistency_pct: float = Field(default=50, ge=0, le=100)

    # Time-based
    age: Optional[int] = None
    dependents: int = 0


class ScoreBreakdown(BaseModel):
    score: float = Field(..., ge=0, le=100)
    grade: str  # A+, A, B+, B, C, D, F
    description: str
    insight: str
    weight: float


class HealthScoreResponse(BaseModel):
    user_id: str
    overall_score: float
    overall_grade: str
    overall_interpretation: str

    # Component scores
    savings_stability: ScoreBreakdown
    debt_management: ScoreBreakdown
    budget_consistency: ScoreBreakdown
    investment_readiness: ScoreBreakdown
    emergency_fund: ScoreBreakdown
    cash_flow: ScoreBreakdown

    # Recommendations
    top_recommendations: list
    strengths: list
    areas_to_improve: list

    calculated_at: datetime


# ── Scoring Engine ───────────────────────────────────────────────────────────────

class FinancialHealthScorer:
    """
    Weighted financial health scoring model.
    Each component is scored 0-100 and combined into an overall score.
    """

    WEIGHTS = {
        "savings_stability": 0.20,
        "debt_management": 0.22,
        "budget_consistency": 0.18,
        "investment_readiness": 0.17,
        "emergency_fund": 0.15,
        "cash_flow": 0.08,
    }

    @staticmethod
    def _grade(score: float) -> str:
        if score >= 90: return "A+"
        if score >= 80: return "A"
        if score >= 70: return "B+"
        if score >= 60: return "B"
        if score >= 50: return "C"
        if score >= 35: return "D"
        return "F"

    def score_savings_stability(self, data: HealthScoreInput) -> ScoreBreakdown:
        """Score: savings rate relative to income"""
        savings_rate = (data.monthly_savings / data.monthly_income) * 100 if data.monthly_income > 0 else 0

        # Benchmark: 20%+ savings rate = excellent
        if savings_rate >= 30:
            score = 100
        elif savings_rate >= 20:
            score = 80 + (savings_rate - 20) * 2
        elif savings_rate >= 10:
            score = 50 + (savings_rate - 10) * 3
        elif savings_rate >= 5:
            score = 25 + (savings_rate - 5) * 5
        else:
            score = savings_rate * 5

        score = min(100.0, max(0.0, score))
        grade = self._grade(score)

        return ScoreBreakdown(
            score=round(score, 1),
            grade=grade,
            description=f"You save {savings_rate:.1f}% of your income monthly",
            insight=f"Monthly savings: ₹{data.monthly_savings:,.0f} | Savings rate: {savings_rate:.1f}%",
            weight=self.WEIGHTS["savings_stability"],
        )

    def score_debt_management(self, data: HealthScoreInput) -> ScoreBreakdown:
        """Score: debt-to-income ratio and debt burden"""
        if data.monthly_income == 0:
            score = 50.0
        else:
            # Debt-to-income ratio (monthly debt payments / income)
            dti = (data.monthly_debt_payment / data.monthly_income) * 100

            if dti == 0:
                score = 100
            elif dti <= 10:
                score = 90
            elif dti <= 20:
                score = 75
            elif dti <= 35:
                score = 55
            elif dti <= 50:
                score = 30
            else:
                score = max(0, 30 - (dti - 50))

        score = min(100.0, max(0.0, score))
        dti_val = (data.monthly_debt_payment / data.monthly_income * 100) if data.monthly_income > 0 else 0
        return ScoreBreakdown(
            score=round(score, 1),
            grade=self._grade(score),
            description=f"Debt-to-income ratio: {dti_val:.1f}%",
            insight=f"Monthly debt payments: ₹{data.monthly_debt_payment:,.0f} | Total debt: ₹{data.total_debt:,.0f}",
            weight=self.WEIGHTS["debt_management"],
        )

    def score_budget_consistency(self, data: HealthScoreInput) -> ScoreBreakdown:
        """Score based on budget adherence history"""
        score = data.budget_adherence_pct
        return ScoreBreakdown(
            score=round(score, 1),
            grade=self._grade(score),
            description=f"You stayed within budget {data.budget_adherence_pct:.0f}% of the time",
            insight="Budget consistency reflects financial discipline",
            weight=self.WEIGHTS["budget_consistency"],
        )

    def score_investment_readiness(self, data: HealthScoreInput) -> ScoreBreakdown:
        """Score: investment as % of income + diversification"""
        if data.monthly_income == 0:
            score = 20.0
        else:
            investment_rate = (data.monthly_investments / data.monthly_income) * 100
            if investment_rate >= 20:
                score = 100
            elif investment_rate >= 15:
                score = 85
            elif investment_rate >= 10:
                score = 70
            elif investment_rate >= 5:
                score = 50
            elif investment_rate > 0:
                score = 30
            else:
                score = 10  # No investments at all

        score = min(100.0, max(0.0, score))
        inv_rate = (data.monthly_investments / data.monthly_income * 100) if data.monthly_income > 0 else 0
        return ScoreBreakdown(
            score=round(score, 1),
            grade=self._grade(score),
            description=f"Investing {inv_rate:.1f}% of income monthly",
            insight=f"Monthly investments: ₹{data.monthly_investments:,.0f} | Total portfolio: ₹{data.total_investments:,.0f}",
            weight=self.WEIGHTS["investment_readiness"],
        )

    def score_emergency_fund(self, data: HealthScoreInput) -> ScoreBreakdown:
        """Score: emergency fund coverage (months of expenses)"""
        months_covered = (data.emergency_fund / data.monthly_expenses) if data.monthly_expenses > 0 else 0

        # Target: 6 months of expenses
        if months_covered >= 6:
            score = 100
        elif months_covered >= 4:
            score = 80
        elif months_covered >= 3:
            score = 65
        elif months_covered >= 1:
            score = 40
        elif months_covered > 0:
            score = 20
        else:
            score = 0

        return ScoreBreakdown(
            score=round(score, 1),
            grade=self._grade(score),
            description=f"Emergency fund covers {months_covered:.1f} months of expenses",
            insight=f"Emergency fund: ₹{data.emergency_fund:,.0f} | Target (6 months): ₹{data.monthly_expenses * 6:,.0f}",
            weight=self.WEIGHTS["emergency_fund"],
        )

    def score_cash_flow(self, data: HealthScoreInput) -> ScoreBreakdown:
        """Score: income - expenses (net cash flow health)"""
        net_flow = data.monthly_income - data.monthly_expenses
        flow_pct = (net_flow / data.monthly_income * 100) if data.monthly_income > 0 else 0

        if flow_pct >= 30:
            score = 100
        elif flow_pct >= 20:
            score = 85
        elif flow_pct >= 10:
            score = 65
        elif flow_pct >= 0:
            score = 40
        else:
            score = max(0, 40 + flow_pct * 2)

        return ScoreBreakdown(
            score=round(score, 1),
            grade=self._grade(score),
            description=f"Net monthly cash flow: ₹{net_flow:,.0f}",
            insight=f"Income: ₹{data.monthly_income:,.0f} | Expenses: ₹{data.monthly_expenses:,.0f}",
            weight=self.WEIGHTS["cash_flow"],
        )

    def _get_recommendations(self, scores: Dict) -> tuple:
        recommendations = []
        strengths = []
        improvements = []

        for name, breakdown in scores.items():
            label = name.replace("_", " ").title()
            if breakdown.score >= 80:
                strengths.append(f"✅ {label}: Excellent ({breakdown.score:.0f}/100)")
            elif breakdown.score >= 60:
                pass  # Good, no action needed
            elif breakdown.score >= 40:
                improvements.append(f"⚠️ {label}: Needs attention ({breakdown.score:.0f}/100)")
            else:
                improvements.append(f"🚨 {label}: Critical improvement needed ({breakdown.score:.0f}/100)")

        # Generate actionable recommendations
        if scores["emergency_fund"].score < 60:
            recommendations.append("🎯 Build your emergency fund to cover 6 months of expenses")
        if scores["investment_readiness"].score < 60:
            recommendations.append("📈 Start investing at least 10% of your income (try SIPs)")
        if scores["debt_management"].score < 60:
            recommendations.append("💳 Focus on debt reduction — use the avalanche or snowball method")
        if scores["savings_stability"].score < 60:
            recommendations.append("💰 Aim to save at least 20% of your monthly income")
        if scores["budget_consistency"].score < 60:
            recommendations.append("📊 Set up category budgets and track spending weekly")

        return recommendations, strengths, improvements

    def calculate(self, data: HealthScoreInput) -> HealthScoreResponse:
        """Calculate complete financial health score"""
        savings = self.score_savings_stability(data)
        debt = self.score_debt_management(data)
        budget = self.score_budget_consistency(data)
        investment = self.score_investment_readiness(data)
        emergency = self.score_emergency_fund(data)
        cashflow = self.score_cash_flow(data)

        component_scores = {
            "savings_stability": savings,
            "debt_management": debt,
            "budget_consistency": budget,
            "investment_readiness": investment,
            "emergency_fund": emergency,
            "cash_flow": cashflow,
        }

        overall = sum(
            getattr(component_scores[k], "score") * self.WEIGHTS[k]
            for k in self.WEIGHTS
        )
        overall = round(min(100.0, max(0.0, overall)), 1)
        grade = self._grade(overall)

        if overall >= 85:
            interpretation = "🏆 Outstanding! Your finances are in excellent health."
        elif overall >= 70:
            interpretation = "✅ Good financial health with room for optimization."
        elif overall >= 55:
            interpretation = "⚠️ Moderate financial health. Focus on key improvement areas."
        elif overall >= 40:
            interpretation = "🚨 Financial health needs attention. Take action now."
        else:
            interpretation = "🆘 Critical financial situation. Immediate action required."

        recommendations, strengths, improvements = self._get_recommendations(component_scores)

        return HealthScoreResponse(
            user_id=data.user_id,
            overall_score=overall,
            overall_grade=grade,
            overall_interpretation=interpretation,
            savings_stability=savings,
            debt_management=debt,
            budget_consistency=budget,
            investment_readiness=investment,
            emergency_fund=emergency,
            cash_flow=cashflow,
            top_recommendations=recommendations,
            strengths=strengths,
            areas_to_improve=improvements,
            calculated_at=datetime.utcnow(),
        )


scorer = FinancialHealthScorer()


# ── Routes ───────────────────────────────────────────────────────────────────────

@router.post("/calculate", response_model=HealthScoreResponse)
async def calculate_health_score(payload: HealthScoreInput):
    """Calculate financial health score (0-100) with component breakdown"""
    return scorer.calculate(payload)


@router.get("/demo")
async def health_score_demo():
    """Demo health score with sample data"""
    sample = HealthScoreInput(
        user_id="demo",
        monthly_income=80000,
        monthly_expenses=55000,
        monthly_savings=15000,
        total_savings=120000,
        total_debt=200000,
        monthly_debt_payment=8000,
        emergency_fund=180000,
        monthly_investments=7000,
        total_investments=350000,
        budget_adherence_pct=72,
        savings_consistency_pct=68,
        age=28,
    )
    return scorer.calculate(sample)
