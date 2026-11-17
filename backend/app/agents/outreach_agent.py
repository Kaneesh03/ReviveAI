from typing import Any
from app.agents.llm.agent_loop import AgentLoop

OUTREACH_SYSTEM_PROMPT = """
You are ReviveAI's Customer Outreach Agent.
Your job is to draft a short, empathetic, and professional email to a customer 
whose payment or subscription has failed. 

Guidelines:
1. Be empathetic but clear about the required action.
2. Personalize the email using the provided customer and payment context.
3. If the failure is due to 'insufficient_funds', be very gentle and understanding.
4. If the failure is 'card_expired' or 'payment_method_issue', direct them to update their payment method.
5. If they have high lifetime value or long tenure, acknowledge their loyalty.
6. Do NOT include a subject line, just the email body starting with a greeting (e.g., 'Hi Customer,').
7. Keep it under 150 words.
8. End with a professional sign-off from 'The ReviveAI Team'.
9. Never invent links or URLs, just use placeholders like [Link to Billing Portal].
"""

class OutreachAgent:
    """
    Agent responsible for drafting personalized customer outreach emails
    when a recovery workflow determines that human intervention or 
    a payment reminder is required.
    """

    def __init__(self, provider: Any) -> None:
        self.provider = provider

    def draft_reminder(self, payment_context: dict[str, Any]) -> str:
        """
        Drafts a payment reminder email based on payment context.
        """
        loop = AgentLoop(provider=self.provider)
        
        context_str = (
            f"Payment ID: {payment_context.get('payment_id', 'Unknown')}\n"
            f"Amount: {payment_context.get('amount', 'Unknown')} {payment_context.get('currency', '')}\n"
            f"Failure Reason: {payment_context.get('failure_reason', 'Unknown')}\n"
            f"Lifetime Value: {payment_context.get('lifetime_value', 'Unknown')}\n"
            f"Customer Age (Days): {payment_context.get('customer_age_days', 'Unknown')}\n"
            f"Retry Count: {payment_context.get('retry_count', 'Unknown')}\n"
            f"Subscription Status: {payment_context.get('subscription_status', 'Unknown')}\n"
        )
        
        user_prompt = (
            f"Please draft a payment reminder email for the following customer context:\n\n"
            f"{context_str}\n\n"
            f"Draft the email now:"
        )

        loop_result = loop.run(
            system_prompt=OUTREACH_SYSTEM_PROMPT,
            user_prompt=user_prompt,
        )
        
        return str(loop_result.get("answer", "Error drafting email."))
