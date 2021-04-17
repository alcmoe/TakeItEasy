from .EquipmentIds import EquipmentIds


class Equipment(EquipmentIds):

    description: str = 'EQUIPMENT'
    price: int = 0

    def __init__(self, equipment_id: int, meta:int = 0):
        self.equipment_id = equipment_id
        self.meta = meta

    def getDescription(self):
        return self.description

    def getId(self):
        return self.equipment_id
