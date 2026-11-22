class CPlayerBullet:
   
    def __init__(self, owner: int, kind: str = "normal") -> None:
        self.owner = owner
        self.kind = kind