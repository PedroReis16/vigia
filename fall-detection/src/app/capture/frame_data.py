class BodyData:
    def __init__(self, label: str, x: float, y: float, conf: float):
        self.label = label
        self.x = x
        self.y = y
        self.conf = conf

class PersonData:
    def __init__(self, person_id: int, body_data: list[BodyData]):
        self.person_id = person_id
        self.body_data = body_data