class FakeEventHandler:
    def __init__(self):
        self.handled_payloads = []
        self.supported_type = "TRANSACTION_CREATED"

    async def handle(self, payload: dict):
        self.handled_payloads.append(payload)

    def supports(self, event_type: str) -> bool:
        return event_type == self.supported_type


class FailingEventHandler:
    def __init__(self):
        self.supported_type = "FAILING_EVENT"

    async def handle(self, payload: dict):
        raise Exception("Simulated handler failure")

    def supports(self, event_type: str) -> bool:
        return event_type == self.supported_type
