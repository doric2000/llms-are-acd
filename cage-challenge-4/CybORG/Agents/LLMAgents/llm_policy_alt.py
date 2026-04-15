from ray.rllib.policy.policy import Policy
from CybORG.Simulator.Actions import Sleep

class LLMDefenderPolicy(Policy):
    def __init__(self, observation_space, action_space, config={}):
        super().__init__(observation_space, action_space, {})

    def compute_single_action(self, obs=None, prev_action=None, **kwargs):
        return Sleep(), [], {}

    def compute_actions(self, obs_batch, state_batches=None, prev_action_batch=None,
                        prev_reward_batch=None, info_batch=None, episodes=None, **kwargs):
        return [Sleep() for _ in obs_batch], [], {}

    def get_weights(self):
        return None

    def set_weights(self, weights):
        pass
