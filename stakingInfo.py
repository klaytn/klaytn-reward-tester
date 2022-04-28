
import json

class StakingInfo:

    def __init__(self, nodeAddress, stakingAddress, rewardAddress):
        self.nodeAddress = nodeAddress
        self.stakingAddress = stakingAddress
        self.rewardAddress = rewardAddress
        self.stakingAmount = 0
        self.weight = 0

    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__,
            sort_keys=True, indent=4)