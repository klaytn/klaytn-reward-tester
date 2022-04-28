from stakingInfo import *
from test_util import *
from validator import *
from pylru import lrucache


class Blockchain:

    def __init__(self, nodeHost):
        self.test_util = Test_Util()
        self.stakingInfoDict = lrucache(200)
        self.proposerListDict = lrucache(400)
        self.configureDict = lrucache(400)
        self.wallet = lrucache(1500)
        self.blockchain = lrucache(1000)
        self.nodeHost = nodeHost

        configure = self.Get_Configure(0)
        self.proposerUpdateInterval = configure['proposerupdateinterval']
        self.stakingUpdateInterval = configure['stakingupdateinterval']

    def Get_Configure(self, blockNumber):
        if blockNumber in self.configureDict:
            return self.configureDict[blockNumber]

        methodName = "governance_itemsAt"
        params = [hex(blockNumber)]
        status_code, resultText, isError = self.test_util.callRPC(self.nodeHost, methodName, params, None)

        configure = {}
        configure['proposerupdateinterval'] = resultText['reward.proposerupdateinterval']
        configure['stakingupdateinterval'] = resultText['reward.stakingupdateinterval']
        configure['epoch'] = resultText['istanbul.epoch']
        configure['policy'] = resultText['istanbul.policy']
        configure['committeesize'] = resultText['istanbul.committeesize']
        configure['useginicoeff'] = resultText['reward.useginicoeff']
        configure['mintingamount'] = int(resultText['reward.mintingamount'])
        ratio = resultText['reward.ratio'].split('/')
        configure['cnRatio'] = int(ratio[0])
        configure['pocRatio'] = int(ratio[1])
        configure['kirRatio'] = int(ratio[2])
        configure['totalRatio'] = configure['cnRatio'] + configure['pocRatio'] + configure['kirRatio']
        configure['unitprice'] = int(resultText['governance.unitprice'])

        self.configureDict[blockNumber] = configure

        return self.configureDict[blockNumber]

    def Get_Snapshot(self, blockNumber):
        methodName = "istanbul_getSnapshot"
        params = [hex(blockNumber)]

        status_code, result, err = self.test_util.callRPC(self.nodeHost, methodName, params, None)

        snapshot = {}

        snapshot['validators'] = result['validators']
        snapshot['weight'] = result['weight']
        snapshot['rewardAddrs'] = result['rewardAddrs']
        snapshot['proposerList'] = result['proposers']
        self.proposerListDict[blockNumber] = snapshot['proposerList']

        return snapshot

    def Get_ProposerList(self, blockNumber):
        if blockNumber in self.proposerListDict:
            return self.proposerListDict[blockNumber]

        self.Get_Snapshot(blockNumber)

        return self.proposerListDict[blockNumber]

    def Get_Council(self, snapshot):
        council = {}
        for i in range(len(snapshot['validators'])):
            validator = Validator()
            validator.address = snapshot['validators'][i].lower()
            validator.rewardAddress_snapshot = snapshot['rewardAddrs'][i].lower()
            validator.weight = int(snapshot['weight'][i])
            council[validator.address] = validator

        return council

    def Get_StakingInfos(self, blockNumber):
        if blockNumber in self.stakingInfoDict:
            return self.stakingInfoDict[blockNumber]

        stakingInfos = self.Get_StakingInfos_From_Addressbook(blockNumber)
        if stakingInfos == None:
            self.stakingInfoDict[blockNumber] = None
            return self.stakingInfoDict[blockNumber]

        stakingInfos = self.Get_StakingAmount(blockNumber, stakingInfos)

        self.stakingInfoDict[blockNumber] = stakingInfos
        return self.stakingInfoDict[blockNumber]

    def Get_StakingInfos_From_Addressbook(self, blockNumber):
        methodName = "klay_call"
        params = [{"to": "0x0000000000000000000000000000000000000400", "gas": "0x100000", "gasPrice": "0x5d21dba00", "value": "0x0", "data": "0x715b208b"}, hex(blockNumber)]

        status_code, result, err = self.test_util.callRPC(self.nodeHost, methodName, params, None)
        result_byte = result[130:]
        type_list = []
        type_len = int(result_byte[:64],16)
        if type_len == 0:
            return None
        for i in range(1,type_len+1):
            type_list.append(int("0x"+result_byte[i*64:(i+1)*64],16))

        result_byte = result_byte[(i+1)*64:]
        address_list = []
        address_len = int(result_byte[:64], 16)
        for i in range(1, address_len + 1):
            address = result_byte[i * 64:(i + 1) * 64]
            address = "0x" + address[24:]
            address_list.append(address)

        stakingInfos = {}

        for i in range(type_len//3):
            address = address_list[i*3].lower()
            stakingAddress = address_list[i*3+1].lower()
            rewardAddress = address_list[i*3+2].lower()

            stakingInfos[address] = StakingInfo(address, stakingAddress, rewardAddress)

        stakingInfos["pocAddress"] = address_list[-2]
        stakingInfos["kirAddress"] = address_list[-1]
        stakingInfos["blockNumber"] = blockNumber

        return stakingInfos

    def Get_StakingAmount(self, blockNumber, stakingInfos):
        if blockNumber in self.stakingInfoDict:
            return self.stakingInfoDict[blockNumber]

        methodName = "klay_getBalance"

        for key, stakingInfo in stakingInfos.items():
            if type(stakingInfo) is str or type(stakingInfo) is int:
                continue
            params = [stakingInfo.stakingAddress, hex(blockNumber)]
            status_code, result, err = self.test_util.callRPC(self.nodeHost, methodName, params, None)

            if not err:
                stakingInfo.stakingAmount = int(result, 16) // self.test_util.PEB

        return stakingInfos

    def Get_Wallet(self, blockNumber, address):
        if blockNumber in self.wallet and address in self.wallet[blockNumber]:
            return self.wallet[blockNumber]

        methodName = "klay_getBalance"
        params = [address, hex(blockNumber)]
        status_code, result, err = self.test_util.callRPC(self.nodeHost, methodName, params, None)

        if blockNumber in self.wallet:
            self.wallet[blockNumber][address] = int(result, 16)
        else:
            wallet = dict()
            wallet[address] = int(result, 16)
            self.wallet[blockNumber] = wallet

        return self.wallet[blockNumber]

    def Get_BlockWithConsensusInfoByNumber(self, blockNumber):
        methodName = "klay_getBlockWithConsensusInfoByNumber"
        params = [hex(blockNumber)]

        status_code, result, err = self.test_util.callRPC(self.nodeHost, methodName, params, None)

        blockInfo = {}

        blockInfo['proposer'] = result['proposer']
        blockInfo['extraData'] = result['extraData']
        blockInfo['round'] = int(result['extraData'][64:66], 16)
        blockInfo['gasUsed'] = int(result['gasUsed'], 16)
        blockInfo['rewardbase'] = result['reward']

        return blockInfo

    def Get_Block(self, blockNumber):
        if blockNumber in self.blockchain:
            return self.blockchain[blockNumber]

        block = self.make_block(blockNumber)

        self.blockchain[blockNumber] = block
        return self.blockchain[blockNumber]

    def make_block(self, blockNumber):
        block = {}
        block['number'] = blockNumber
        block["config"] = self.Get_Configure(blockNumber)
        block['snapshot'] = self.Get_Snapshot(blockNumber)
        proposerblockNum = self.test_util.calcProposerBlockNumber(blockNumber,block['config']['proposerupdateinterval'])
        block['snapshot']['proposerBlockNum'] = proposerblockNum
        block['snapshot']['proposerListOfLastBlock'] = self.Get_ProposerList(blockNumber-1)
        block['snapshot']['proposerListOfInterval'] = self.Get_ProposerList(proposerblockNum)
        block['council'] = self.Get_Council(block['snapshot'])
        if len(block['snapshot']['proposerListOfInterval']) == len(block['snapshot']['validators']):
            block['snapshot']['addressBookActivated'] = False
        else:
            block['snapshot']['addressBookActivated'] = True

        stakingBlockNumber = self.test_util.calcStakingBlockNumber(blockNumber, block['config']['stakingupdateinterval'])
        block['stakingInfos'] = self.Get_StakingInfos(stakingBlockNumber)
        block['blockInfo'] = self.Get_BlockWithConsensusInfoByNumber(blockNumber)

        if block['stakingInfos'] == None:
            block['wallet'] = self.Get_Wallet(blockNumber, block['blockInfo']['rewardbase'])
            block['previousWallet'] = self.Get_Wallet(blockNumber-1, block['blockInfo']['rewardbase'])
        else:
            self.set_stakingInfo_to_validator(block['council'],block['stakingInfos'])

            proposer = block['blockInfo']['proposer']
            self.Get_Wallet(blockNumber, block['blockInfo']['rewardbase'])
            self.Get_Wallet(blockNumber, block['stakingInfos'][proposer].rewardAddress)
            self.Get_Wallet(blockNumber, block['stakingInfos']["pocAddress"])
            block['wallet'] = self.Get_Wallet(blockNumber, block['stakingInfos']["kirAddress"])

            self.Get_Wallet(blockNumber-1, block['blockInfo']['rewardbase'])
            self.Get_Wallet(blockNumber-1, block['stakingInfos'][proposer].rewardAddress)
            self.Get_Wallet(blockNumber-1, block['stakingInfos']["pocAddress"])
            block['previousWallet'] = self.Get_Wallet(blockNumber-1, block['stakingInfos']["kirAddress"])

        return block

    def set_stakingInfo_to_validator(self, council, stakingInfos):
        for address, validator in council.items():
            if not address in stakingInfos:
                continue
            stakingInfo = stakingInfos[address]
            validator.stakingAddress = stakingInfo.stakingAddress
            validator.rewardAddress = stakingInfo.rewardAddress
            validator.stakingAmount = stakingInfo.stakingAmount

        for address, stakingInfo in stakingInfos.items():
            if address in council or type(stakingInfo) is not StakingInfo:
                continue
            for validator in council.values():
                if validator.rewardAddress == stakingInfo.rewardAddress:
                    validator.stakingAmount += stakingInfo.stakingAmount
                    break