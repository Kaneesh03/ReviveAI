import pytest

from app.agents.tools.executor import (
    ToolExecutor,
    ToolExecutionError,
)


def test_get_payment_tool():
    executor = ToolExecutor()

    result = executor.execute(
        "get_payment",
        {
            "payment_id": "pay_002610"
        },
    )

    assert result["success"] is True
    assert result["tool"] == "get_payment"
    assert result["result"]["found"] is True


def test_unknown_tool_is_rejected():
    executor = ToolExecutor()

    with pytest.raises(ToolExecutionError):
        executor.execute(
            "delete_database",
            {},
        )


def test_invalid_payment_id_is_rejected():
    executor = ToolExecutor()

    with pytest.raises(ToolExecutionError):
        executor.execute(
            "get_payment",
            {
                "payment_id": "invalid123"
            },
        )


def test_json_arguments_are_supported():
    executor = ToolExecutor()

    result = executor.execute(
        "get_payment",
        '{"payment_id":"pay_002610"}',
    )

    assert result["success"] is True
    assert result["result"]["found"] is True


def test_unknown_payment_returns_not_found():
    executor = ToolExecutor()

    result = executor.execute(
        "get_payment",
        {
            "payment_id": "pay_999999"
        },
    )

    assert result["success"] is True
    assert result["result"]["found"] is False