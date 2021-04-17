from ..Equipment import Equipment


class LiandrySTorment(Equipment):
    description: str = "It's Liandry's torment"
    price: int = 4500

    def __init__(self):
        super(LiandrySTorment, self).__init__(self.LianDry_s_Torment)
