import gymnasium as gym
from gymnasium import spaces
import pandas as pd
import numpy as np
from stable_baselines3 import PPO
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("RLTradingAgent")

class BankNiftyEnv(gym.Env):
    """
    Custom Environment for Bank Nifty Trading that follows gymnasium interface.
    """
    metadata = {'render.modes': ['human']}

    def __init__(self, df, features, initial_balance=100000):
        super(BankNiftyEnv, self).__init__()
        
        self.df = df
        self.features = features
        self.initial_balance = initial_balance
        
        # Action space: 0 = Hold/Neutral, 1 = Buy (Long), 2 = Sell (Exit/Short)
        self.action_space = spaces.Discrete(3)
        
        # Observation space: Features + Balance + Current Position
        self.observation_space = spaces.Box(
            low=-np.inf, high=np.inf, shape=(len(features) + 2,), dtype=np.float32
        )
        
        if self.df is not None:
            self.reset()

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.balance = self.initial_balance
        self.current_step = 0
        self.position = 0 # 0: None, 1: Long
        self.entry_price = 0
        self.total_profit = 0
        
        return self._get_observation(), {}

    def _get_observation(self):
        obs = self.df[self.features].iloc[self.current_step].values
        # Append balance and position normalized roughly
        obs = np.append(obs, [self.balance / 100000, self.position])
        return obs.astype(np.float32)

    def step(self, action):
        current_price = self.df['Close'].iloc[self.current_step]
        reward = 0
        terminated = False
        truncated = False
        
        # Execute Action
        if action == 1: # Buy / Long
            if self.position == 0:
                self.position = 1
                self.entry_price = current_price
                # Slight penalty for trade execution
                reward = -0.01
        
        elif action == 2: # Sell / Exit
            if self.position == 1:
                profit_pct = (current_price - self.entry_price) / self.entry_price
                reward = profit_pct * 10 # Scaled reward
                self.balance *= (1 + profit_pct)
                self.total_profit += (current_price - self.entry_price)
                self.position = 0
        
        # Move to next step
        self.current_step += 1
        
        if self.current_step >= len(self.df) - 1:
            terminated = True
        
        obs = self._get_observation()
        info = {"balance": self.balance, "profit": self.total_profit}
        
        return obs, reward, terminated, truncated, info

    def render(self, mode='human'):
        print(f"Step: {self.current_step}, Balance: {self.balance:.2f}, Profit: {self.total_profit:.2f}")

class RLTradingAgent:
    def __init__(self, df, features):
        self.env = BankNiftyEnv(df, features)
        self.model = PPO("MlpPolicy", self.env, verbose=1)
        self.features = features
        
        # Dynamic paths
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.model_path = os.path.join(base_dir, f"rl_model_sniper.zip")

    def train(self, total_timesteps=10000):
        logger.info(f"Training PPO Agent for {total_timesteps} timesteps...")
        self.model.learn(total_timesteps=total_timesteps)
        logger.info("RL Training Complete.")

    def get_action(self, obs):
        action, _states = self.model.predict(obs, deterministic=True)
        return int(action)

    def save_model(self):
        self.model.save(self.model_path)
        logger.info(f"RL Model saved to {self.model_path}")

    def load_model(self):
        if os.path.exists(self.model_path):
            self.model = PPO.load(self.model_path, env=self.env)
            logger.info("RL Model Loaded successfully.")
            return True
        return False

if __name__ == "__main__":
    from data_pipeline import DataPipeline
    from model_engine import ModelEngine
    
    dp = DataPipeline("^NSEBANK")
    if dp.run_full_pipeline():
        me = ModelEngine()
        agent = RLTradingAgent(dp.train_data, me.features)
        agent.train(total_timesteps=5000)
        
        # Test on 2-year testing data
        test_env = BankNiftyEnv(dp.test_data, me.features)
        obs, _ = test_env.reset()
        final_info = {}
        for _ in range(100):
            action = agent.get_action(obs)
            obs, reward, terminated, truncated, info = test_env.step(action)
            final_info = info
            if terminated or truncated: break
        
        logger.info(f"Test Run Results: Final Balance: {final_info.get('balance', 0):.2f}, Total Profit: {final_info.get('profit', 0):.2f}")
