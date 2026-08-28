TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "get_payment",
            "description": (
                "Retrieve decision-time information for "
                "a payment. Future recovery outcomes are "
                "never exposed."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "payment_id": {
                        "type": "string",
                        "description": (
                            "Unique payment identifier, "
                            "for example pay_002610."
                        ),
                    }
                },
                "required": [
                    "payment_id"
                ],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_payment_eligibility",
            "description": (
                "Check whether a failed payment is eligible "
                "for recovery under deterministic policy rules."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "payment_id": {
                        "type": "string",
                        "description": (
                            "Unique payment identifier."
                        ),
                    }
                },
                "required": [
                    "payment_id"
                ],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "predict_recovery",
            "description": (
                "Predict the probability that an eligible "
                "failed payment can be recovered."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "payment_id": {
                        "type": "string",
                        "description": (
                            "Unique payment identifier."
                        ),
                    }
                },
                "required": [
                    "payment_id"
                ],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_payment_revenue_risk",
            "description": (
                "Calculate revenue at risk and expected "
                "recovery value for a failed payment."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "payment_id": {
                        "type": "string",
                        "description": (
                            "Unique payment identifier."
                        ),
                    }
                },
                "required": [
                    "payment_id"
                ],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "make_payment_recovery_decision",
            "description": (
                "Produce the final deterministic recovery "
                "decision using eligibility, ML prediction, "
                "revenue risk, and business rules."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "payment_id": {
                        "type": "string",
                        "description": (
                            "Unique payment identifier."
                        ),
                    }
                },
                "required": [
                    "payment_id"
                ],
            },
        },
    },
]