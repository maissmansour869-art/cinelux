import time
import uuid
from dataclasses import dataclass
from decimal import Decimal


@dataclass
class ChargeResult:
    status: str
    transaction_id: str | None = None
    decline_reason: str | None = None
    raw: dict | None = None


@dataclass
class RefundResult:
    status: str
    transaction_id: str | None = None
    raw: dict | None = None


class PaymentGateway:
    def charge(self, token: str, amount: Decimal, currency: str, idempotency_key: str) -> ChargeResult:
        if token.startswith("tok_bad_"):
            return ChargeResult("DECLINED", decline_reason="CARD_DECLINED", raw={"idempotencyKey": idempotency_key})
        if token.startswith("tok_slow_"):
            time.sleep(1)
            return ChargeResult("ERROR", raw={"reason": "timeout"})
        if token.startswith("tok_network_"):
            return ChargeResult("ERROR", raw={"reason": "network"})
        if token.startswith("tok_good_"):
            return ChargeResult("SUCCESS", transaction_id=f"PAY-SIM-{uuid.uuid4().hex[:12]}", raw={"amount": str(amount), "currency": currency})
        return ChargeResult("DECLINED", decline_reason="UNKNOWN_TOKEN", raw={})

    def refund(self, transaction_id: str, amount: Decimal, currency: str, idempotency_key: str) -> RefundResult:
        if transaction_id.startswith("PAY-SIM-"):
            return RefundResult("SUCCESS", transaction_id=f"REF-SIM-{uuid.uuid4().hex[:12]}")
        return RefundResult("ERROR")
