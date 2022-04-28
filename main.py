from reward_tester import *
import os

if __name__== "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(base_dir, 'test.conf.json')) as configure_file:
        configure = json.load(configure_file)

    reward_tester = Reward_Tester(configure)
    reward_tester.start()