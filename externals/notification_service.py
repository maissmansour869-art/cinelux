from dataclasses import dataclass


@dataclass
class SendResult:
    status: str


class NotificationService:
    def send_email(self, to: str, subject: str, body: str, attachments=None) -> SendResult:
        return SendResult("SUCCESS")

    def send_sms(self, to: str, body: str) -> SendResult:
        return SendResult("SUCCESS")
