import requests
import json
import random
from websocket import create_connection, WebSocket

class Test_Util:
    PEB = 1000000000000000000
    UnitPrice =25000000000

    def getResult(self, response):
        jsonData = ""
        try:
            jsonData = json.loads(response)['result']
        except:
            print(response)

        return jsonData

    def callRPC(self, nodeHost, methodName, params, logfile, saveResult=False, rpcPort=8551):
        # send request through rpc with methodName and param
        HOST = F"http://{nodeHost}:{rpcPort}"
        HEADERS = {'Content-Type': 'application/json'}
        isErrer = False

        payload = {'jsonrpc': '2.0', 'method': methodName, 'params': params, 'id': self.getRequestId()}
        response = requests.post(HOST, data=json.dumps(payload), headers=HEADERS, timeout=300)
        #self.writeLog(logfile, methodName, HOST, payload, response.text, saveFile=saveResult)

        try:
            # When success, result key exists.
            resultText = json.loads(response.text)['result']
        except KeyError:
            # When fail, error key exists.
            resultText = json.loads(response.text)['error']
            isErrer = True

        return (response.status_code, resultText, isErrer)

    def callWS(self, nodeHost, methodName, params, logfile, saveResult=False, wsPort=8552):
        # send request through ws with methodName and param
        HOST = F"ws://{nodeHost}:{wsPort}"
        payload = {'jsonrpc': '2.0', 'method': methodName, 'params': params, 'id': self.getRequestId()}
        isErrer = False

        ws = create_connection(HOST)
        ws.send(json.dumps(payload))
        response = ws.recv()
        ws.close()

        try:
            # When success, result key exists.
            resultJson = json.loads(response)['result']
        except KeyError:
            # When fail, error key exists.
            resultJson = json.loads(response)['error']
            isErrer = True

        self.writeLog(logfile, methodName, HOST, payload, response, saveFile=saveResult, service="ws")
        return (resultJson, isErrer)

    def getRequestId(self):
        '''
        You can choose random requestId from 1 to 99.
        '''
        return random.randint(1, 100)

    def calcProposerBlockNumber(self, blockNumber, proposerInterval):
        if blockNumber <= proposerInterval:
            return 0

        return (blockNumber-1)//proposerInterval*proposerInterval

    def calcStakingBlockNumber(self, blockNumber, stakingInterval):
        if blockNumber <= stakingInterval * 2:
            return 0
        return (blockNumber//stakingInterval-1)*stakingInterval

    def gini(self, incomes):
        # skip this if it's unneeded
        incomes = incomes[:]
        incomes.sort()

        sum_of_absolute_differences = 0
        subsum = 0

        for i, x in enumerate(incomes):
            sum_of_absolute_differences += i * x - subsum
            subsum += x

        return sum_of_absolute_differences / subsum / len(incomes)