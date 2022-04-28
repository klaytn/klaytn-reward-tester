import time
import math
import datetime
import decimal
import os

from blockchain import *

class Reward_Tester:

    def __init__(self, configure):
        self.test_util = Test_Util()
        self.configure = configure
        if self.configure["target_node"] == "klaytn_deploy":
            base_dir = os.path.dirname(os.path.abspath(__file__))
            with open(os.path.join(base_dir, '../../upload/EN0/publicip')) as en_publicip:
                self.nodeip = en_publicip.readline().strip()
        else:
            self.nodeip = self.configure["target_node"]
        self.blockchain = Blockchain(self.nodeip)

        dt = datetime.datetime.now()
        self.logfile = dt.strftime("%Y%m%d_%H%M.out")

    def start(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(base_dir, "logs", self.logfile), "a") as logfile:
            logfile.write("reward test start!")

        blockNumber = self.configure["startBlockNumber"]
        targetBlockNumber = self.configure["endBlockNumber"]
        errBlockNumber = []

        while blockNumber <= targetBlockNumber:
            while blockNumber >= self.Get_BlockNumber():
                time.sleep(1)
            print("========= blockNumber", blockNumber, hex(blockNumber))
            block = self.blockchain.Get_Block(blockNumber)
            proposerlist_result, proposerlist_log = self.Test_CheckProposerUpdateInterval(block)
            weight_result = True
            weight_log = ""
            if blockNumber % self.blockchain.proposerUpdateInterval == 0:
                weight_result, weight_log = self.Test_CheckWeight(block)
            validator_result, validator_log = self.Test_CheckValidator(block)
            reward_result, reward_log = self.Test_CheckReward(block)
            if (proposerlist_result and weight_result and validator_result and reward_result) == False:
                errBlockNumber.append(blockNumber)
                with open(os.path.join(base_dir, "logs", self.logfile),"a") as logfile:
                    log = f"========= blockNumber {blockNumber}, {hex(blockNumber)} \n"
                    if not proposerlist_result:
                        log += proposerlist_log
                    if not weight_result:
                        log += weight_log
                    if not validator_result:
                        log += validator_log
                    if not reward_result:
                        log += reward_log
                    log += "\n"
                    logfile.write(log)
            blockNumber += 1

        with open(os.path.join(base_dir, "logs", self.logfile), "a") as logfile:
            log = "reward test finished\n"
            if len(errBlockNumber) == 0:
                log += "pass\n"
            else:
                log += f"fail {errBlockNumber}\n"
            print(log)
            logfile.write(log)

    def Test_CheckProposerUpdateInterval(self, block):
        log = ''
        if block['number'] % block['config']['proposerupdateinterval'] == 0:
            if not block['snapshot']['proposerListOfLastBlock'] == block['snapshot']['proposerList']:
                result = True
                print("proposer update ok")
            else:
                result = False
                print("proposer update interval error it should be updated", "current block number", block['number'], "proposer interval",
                      block['config']['proposerupdateinterval'])
                log += f"proposer interval error. proposer list should be updated \n"
                log += f"proposer interval : {block['config']['proposerupdateinterval']} \n"
                log += f"proposer block number : {block['snapshot']['proposerBlockNum']} \n"
                log += f"proposer list : {block['snapshot']['proposerList']} \n"
                log += f"proposer list of last block : {block['snapshot']['proposerListOfLastBlock']} \n"
                log += f"proposer list of interval : {block['snapshot']['proposerListOfInterval']} \n"
                log += f"validators in snapshot : {block['snapshot']['validators']} \n"
        else:
            if not block['snapshot']['proposerListOfLastBlock'] == block['snapshot']['proposerList']:
                result = False
                print("proposer update interval error it should not be updated", "current block number", block['number'], "proposer interval",
                      block['config']['proposerupdateinterval'])
                print("previousProposerList len", len(block['snapshot']['proposerListOfInterval']), "result len", len(block['snapshot']['proposerList']))
                log += f"proposer interval error. proposer list should not be updated \n"
                log += f"proposer interval : {block['config']['proposerupdateinterval']} \n"
                log += f"proposer block number : {block['snapshot']['proposerBlockNum']} \n"
                log += f"proposer list : {block['snapshot']['proposerList']} \n"
                log += f"proposer list of last block : {block['snapshot']['proposerListOfLastBlock']} \n"
                log += f"proposer list of interval : {block['snapshot']['proposerListOfInterval']} \n"
                log += f"validators in snapshot : {block['snapshot']['validators']} \n"
            else:
                result = True
        log += f"\n"
        return result, log

    def Test_CheckValidator(self, block):
        proposerBlockNumber = block['snapshot']['proposerBlockNum']
        round = block['blockInfo']['round']
        picker = (block['number'] - 1 - proposerBlockNumber + round) % len(block['snapshot']['proposerListOfLastBlock'])
        expectedProposer = block['snapshot']['proposerListOfLastBlock'][picker]

        log = ""
        if round != 0:
            print("round change has been occured.", round)

        if expectedProposer != block['blockInfo']['proposer']:
            result = False
            print("blockNumber:", block['number'], "proposer", block['blockInfo']['proposer'], "expected proposer :", expectedProposer, "round",round)
            log += f"validator error \n"
            log += f"proposerBlockNumber : {block['snapshot']['proposerBlockNum']} \n"
            log += f"propost list of last block : {block['snapshot']['proposerListOfLastBlock']} \n"
            log += f"len of propost list of last block : {len(block['snapshot']['proposerListOfLastBlock'])} \n"
            log += f"picker : {picker} \n"
            log += f"round : {round} \n"
            log += f"expectedProposer : {block['snapshot']['proposerListOfLastBlock'][picker]} \n"
            log += f"resultProposer : {block['blockInfo']['proposer']} \n"

        else:
            result = True
            print("blockNumber",block['number'],"validator is ok")

        return result, log

    def Test_CheckWeight(self, block):
        result = False
        stakingInfos = block['stakingInfos']
        proposer_dict = {}

        if stakingInfos == None:
            for address, validator in block['council'].items():
                validator.expectedWeight = 0
        else:
            totalAmount = 0

            if block["config"]['useginicoeff'] == True:
                validatorStakingAmounts = []
                for address, validator in block['council'].items():
                    validatorStakingAmounts.append(validator.stakingAmount)
                stakingInfos['gini'] = float(decimal.Decimal(self.test_util.gini(validatorStakingAmounts)).quantize(decimal.Decimal('0.01'),rounding=decimal.ROUND_HALF_UP))
                for address, validator in block['council'].items():
                    validator.giniReflectedAmount = int(math.pow(validator.stakingAmount,(1/(1+stakingInfos['gini'])))+0.5)
                    totalAmount += validator.giniReflectedAmount
            else:
                for address, validator in block['council'].items():
                    totalAmount += validator.stakingAmount

            for address, validator in block['council'].items():
                if block["config"]['useginicoeff'] == True:
                    validator.expectedWeight = int(validator.giniReflectedAmount * 100.0 / totalAmount + 0.5) if totalAmount != 0 else 1
                else:
                    validator.expectedWeight = int(validator.stakingAmount * 100.0 / totalAmount + 0.5) if totalAmount != 0 else 1

                if validator.expectedWeight == 0:
                    validator.expectedWeight = 1

        for proposer in block['snapshot']['proposerList']:
            if not proposer in proposer_dict:
                proposer_dict[proposer] = 1
            else:
                proposer_dict[proposer] += 1

        log = f"weight error \n"
        if stakingInfos == None:
            log += f"error occurred before weightedRandom start"
            for address, validator in block['council'].items():
                #if proposer_dict[validator.address] != 1 or validator.weight != 0:
                if proposer_dict[validator.address] != 1:
                    result = False
                    #print("weight error", validator.address[:9], "result weight of list", proposer_dict[validator.address], "weight from snap", validator.weight)
                    print("weight error", validator.address[:9], "result weight of list", proposer_dict[validator.address])

                    log += f"validator : {validator.address} \n"
                    log += f"weight of list : {proposer_dict[validator.address]} \n"
                    log += f"weight from snap: {validator.weight} \n"
                    log += f"staking amount : {validator.stakingAmount} \n\n"

                else:
                    result = True
                    print("weight for", validator.address[:9], proposer_dict[validator.address], "ok")
        else:
            log += f"error occurred after weightedRandom start"
            for address, validator in block['council'].items():
                #if proposer_dict[validator.address] != validator.expectedWeight or validator.expectedWeight != validator.weight:
                if proposer_dict[validator.address] != validator.expectedWeight:
                    result = False
                    #print("weight error", validator.address[:9], "result weight of list", proposer_dict[validator.address], "expected weight", validator.expectedWeight, "weight from snap", validator.weight)
                    print("weight error", validator.address[:9], "result weight of list", proposer_dict[validator.address], "expected weight", validator.expectedWeight, "stakingAmount", validator.stakingAmount)

                    log += f"validator : {validator.address} \n"
                    log += f"weight of list : {proposer_dict[validator.address]} \n"
                    log += f"expected weight : {validator.expectedWeight} \n"
                    log += f"weight from snap : {validator.weight} \n"
                    log += f"staking amount : {validator.stakingAmount} \n\n"
                else:
                    result = True
                    print("weight for", validator.address[:9], proposer_dict[validator.address], validator.stakingAmount, "ok")

        if not result:
            log += f"proposer interval : {block['config']['proposerupdateinterval']} \n"
            log += f"proposer list : {block['snapshot']['proposerList']} \n"
            log += f"all weight from snapshot : {block['snapshot']['weight']} \n"
            for address, validator in block['council'].items():
                log += f'{address} : {validator.stakingAmount}\n'

        return result, log

    def Test_CheckReward(self, block):
        result = True
        previouswallet = block['previousWallet']
        currentwallet = block['wallet']

        mintingAmount = block["config"]['mintingamount']
        unitPrice = block['config']['unitprice']
        gasUsed = block['blockInfo']['gasUsed']
        log = ""

        if not block['snapshot']['addressBookActivated']:
            reward_base = block['blockInfo']['rewardbase']

            if not currentwallet[reward_base] - previouswallet[reward_base] >= mintingAmount:
                result = False
                print("cn reward error", "current balance", int(currentwallet[reward_base]), "previous balance", int(previouswallet[reward_base]), "difference", int(currentwallet[reward_base]) - int(previouswallet[reward_base]), "mintingAmount", mintingAmount / float(self.test_util.PEB))
            if not currentwallet[reward_base] - previouswallet[reward_base] - mintingAmount == gasUsed * unitPrice:
                result = False
                print("gas price error", "result gas price",currentwallet[reward_base] - previouswallet[reward_base] - mintingAmount, "expected gas price", gasUsed * unitPrice)
            if not result:
                log += f"reward error before weightedRandom start \n"
                log += f"proposer : {block['blockInfo']['proposer']} \n"
                log += f"reward base : {reward_base} \n"
                log += f"minting amount : {mintingAmount} \n"
                log += f"unitPrice : {unitPrice} \n"
                log += f"gasUsed : {gasUsed} \n"
                log += f"current balance : {int(currentwallet[reward_base])} \n"
                log += f"previous balance : {int(previouswallet[reward_base])} \n"
                log += f"difference : {int(currentwallet[reward_base]) - int(previouswallet[reward_base])} \n"
        else:
            expected_cn_reward = mintingAmount * block["config"]['cnRatio'] / block["config"]['totalRatio']
            expected_poc_reward = mintingAmount * block["config"]['pocRatio'] / block["config"]['totalRatio']
            expected_kir_reward = mintingAmount * block["config"]['kirRatio'] / block["config"]['totalRatio']

            proposer = block['blockInfo']['proposer']
            reward_address = block['council'][proposer].rewardAddress

            # result. include gas fee
            cn_reward = currentwallet[reward_address] - previouswallet[reward_address]
            poc_reward = currentwallet[block['stakingInfos']["pocAddress"]]-previouswallet[block['stakingInfos']["pocAddress"]]
            kir_reward = currentwallet[block['stakingInfos']["kirAddress"]]-previouswallet[block['stakingInfos']["kirAddress"]]
            total_reward = cn_reward + kir_reward + poc_reward

            if not reward_address == block['blockInfo']['rewardbase']:
                result = False
                print("reward address error", "result", block['blockInfo']['rewardbase'], "expected", reward_address)
                log += f"reward address error\n"

            if not total_reward >= mintingAmount:
                result = False
                print("total reward error result should be greater than minting amount", "result", total_reward, "Minting Amount", mintingAmount)
                log += f"total reward error\n"
                log += f"total_reward : {total_reward}\n"
                log += f"mintingAmount : {mintingAmount}\n"

            if not cn_reward >= expected_cn_reward:
                result = False
                print("cn reward error")
                print(currentwallet[reward_address] / float(self.test_util.PEB), previouswallet[reward_address] / float(self.test_util.PEB), expected_cn_reward / float(self.test_util.PEB))
                log += f"cn reward error\n"
                log += f"cn reward : {cn_reward}\n"
                log += f"expected cn reward : {expected_cn_reward}\n"
            if not kir_reward >= expected_kir_reward:
                result = False
                print("kir reward error")
                print(currentwallet[block['stakingInfos']["kirAddress"]], previouswallet[block['stakingInfos']["kirAddress"]], expected_kir_reward)
                log += f"kir reward error\n"
                log += f"kir reward : {kir_reward}\n"
                log += f"expected kir reward : {expected_kir_reward}\n"
            if not poc_reward >= expected_poc_reward:
                result = False
                print("poc reward error")
                print(currentwallet[block['stakingInfos']["pocAddress"]], previouswallet[block['stakingInfos']["pocAddress"]], expected_poc_reward)
                log += f"poc reward error\n"
                log += f"poc reward : {poc_reward}\n"
                log += f"expected kir reward : {expected_poc_reward}\n"
            if not total_reward - mintingAmount == gasUsed * unitPrice:
                result = False
                print("gas price error")
                print(total_reward - mintingAmount, gasUsed * unitPrice)
                if not gasUsed == 0:
                    print("used unitPrice", (total_reward - mintingAmount) / gasUsed, unitPrice)
                log += f"gas price error\n"
                log += f"gas price : {total_reward - mintingAmount}\n"
                log += f"expected gas price : {gasUsed * unitPrice}\n"
            if not result:
                prelog = f"reward error after weightedRandom start \n"
                prelog += f"reward base : {block['blockInfo']['rewardbase']} \n"
                prelog += f"reward address : {reward_address} \n"
                prelog += f"minting amount : {mintingAmount} \n"
                prelog += f"unitPrice : {unitPrice} \n"
                prelog += f"gasUsed : {gasUsed} \n"
                log = prelog + log
        return result, log

    def Get_BlockNumber(self):
        methodName = "klay_blockNumber"
        status_code, resultText, isError = self.test_util.callRPC(self.nodeip, methodName, [], None)

        if not isError:
            return int(resultText,16)
        else:
            return -1

    def CallRPCToAllNode(self, methodName, params):
        result_set = set()
        result_list = []
        err = False
        for idx, node in enumerate(self.council.node_list):
            status_code, resultText, isError = self.test_util.callRPC(node.ip, methodName, params, None)

            err = err or isError
            result_list.append((resultText, status_code, isError))
            result_set.add(json.dumps(resultText))

        return result_list, result_set, err