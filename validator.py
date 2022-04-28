import json

class Validator:

    def __init__(self):
        self.address = ""
        self.stakingAddress = ""
        self.rewardAddress = ""
        self.stakingAmount = 0
        self.weight = 0

    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__,
                          sort_keys=True, indent=4)