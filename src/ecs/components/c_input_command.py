class CInputCommand:
    def __init__(self, action: str, input_type: str, key: int) -> None:
        self.action = action
        self.input_type = input_type
        self.key = key
        self.active = False
        self.pressed = False
