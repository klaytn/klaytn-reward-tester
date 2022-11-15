# Branch name will be changed

We will change the `master` branch to `main` on Dec 15, 2022.
After the branch policy change, please check your local or forked repository settings.

# klaytn-reward-tester
Klaytn Reward Tester is a project to test klaytn reward system easily.

## Quick Start
Run `init_tester`
* Before running init_tester, python3 should be installed.
* By running init_tester, it provides python virtual environment and install dependent python libraries.

Prepare a klaytn network
* Tested network configuration is 4cn/1pn/1en.
* You can use any klaytn node type to conduct reward test.
* The testing node(target_node) should support rpc api of klay, governance, istanbul.
* The testing node(target_node) should open 8551 rpc port.

Edit `test.conf.json`
* test.conf.json file is a configure file for klaytn-reward-tester.
* if not use klaytn_deploy, node ip should be given
* **startBlockNumber** is the number to start test from   
* **endBlockNumber** is the number for ending test   
* **target_node** is the node info for rpc api. If it is klaytn_deploy, tester automatically use ip of **en0**.
  otherwise, ip of target node should be provided. 

Run `./start_tester` to run the test.

## How to contribute?
* issue: Please make an issue if there's bug, improvement, docs suggestion, etc.
* contribute: Please make a PR. If the PR is related with an issue, link the issue.
