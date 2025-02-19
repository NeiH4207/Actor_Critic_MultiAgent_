"""
Created on Fri Nov 27 16:00:47 2020
@author: hien
"""
from __future__ import division

import argparse

from src.environment import Environment
from read_input import Data
from itertools import count
import numpy as np
from src.mcts import MCTS
from collections import deque
import time
from src.model import Policy
from src.replay_memory import ReplayMemory
from src.trainer import Trainer
from src.utils import plot, dotdict

args = dotdict({
    'run_mode': 'train',
    'visualize': True,
    'min_size': 7,
    'max_size': 7,
    'n_games': 2,
    'num_iters': 20000,
    'n_epochs': 1000000,
    'n_maps': 1000,
    'show_screen': True,
    'optimizer': 'adas',
    'lr': 1e-4,
    'exp_rate': 0.0,
    'gamma': 0.99,
    'tau': 0.01,
    'max_grad_norm': 0.3,
    'discount': 0.6,
    'num_channels': 64,
    'batch_size': 256,
    'replay_memory_size': 100000,
    'dropout': 0.6,
    'initial_epsilon': 0.1,
    'final_epsilon': 1e-4,
    'dir': './Models/',
    'load_checkpoint': False,
    'saved_checkpoint': False
})

def execute_episode(netw, num_simulations, env, args):
    """
    Executes a single episode of the task using Monte-Carlo tree search with
    the given agent network. It returns the experience tuples collected during
    the search.
    :param netw: Network for predicting action probabilities and state
    value estimate.
    :param num_simulations: Number of simulations (traverses from root to leaf)
    per action.
    :param TreeEnv: Static environment that describes the environment dynamics.
    :return: The observations for each step of the episode, the policy outputs
    as output by the MCTS (not the pure neural network outputs), the individual
    rewards in each step, total return for this episode and the final state of
    this episode.
    """
    mcts = MCTS(netw, env)
    mcts.initialize_search()

    """
    Must run this once at the start, so that noise injection actually affects
    the first action of the episode.
    """
    
    first_node = mcts.root.select_leaf()
    probs, vals = netw.step(env.get_states_for_step(first_node.state),
                                  env.get_agent_for_step(0))
    first_node.incorporate_estimates(probs[0], vals[0], first_node)
    
    """ initialize """
    actions, state_vals, log_probs, rewards, soft_state, \
        soft_agent_pos, pred_acts = [[[], []] for i in range(7)]
        
    """ update by step """
    for i in range(env.num_players):
        soft_state[i] = env.get_observation(i)
        soft_agent_pos[i] = env.get_agent_pos(i)
        
    while True:
        actions = [[0] * env.n_agents, [0] * env.n_agents]
        for agent_id in range(env.n_agents):
            for player in range(env.num_players):
                mcts.root.inject_noise()
                current_simulations = mcts.root.N
        
                # We want `num_simulations` simulations per action not counting
                # simulations from previous actions.
                while mcts.root.N < current_simulations + num_simulations:
                    mcts.tree_search()
                act = mcts.pick_action()
                valid, next_state, reward = env.soft_step(agent_id, soft_state[i], act, soft_agent_pos[i])
                mcts.take_action(action)
                actions[player][agent_id] = action
            
        # for i in range(env.n_agents):
        #     if args.show_screen:
        #         env.render()
        #     mcts.root.inject_noise()
        #     current_simulations = mcts.root.N
        #     while mcts.root.N < current_simulations + num_simulations:
        #         mcts.tree_search()
    
        #     action = mcts.pick_action()
        #     mcts.take_action(action)
        #     actions_2[i] = action
        actions[0] = [np.random.randint(0, env.n_actions - 1) for _ in range(env.n_agents)]
        actions[1] = [np.random.randint(0, env.n_actions - 1) for _ in range(env.n_agents)]
        next_state, final_reward, done, _ = env.step(actions[0], actions[1], args.show_screen)
        if args.show_screen:
            env.render()
        # mcts.root.state = env.get_state(0)
        if mcts.root.is_done():
            break
    
    # Computes the returns at each step from the list of rewards obtained at
    # each step. The return is the sum of rewards obtained *after* the step.
    obs = np.concatenate(mcts.obs)
    return (obs, mcts.searches_pi,  mcts.rewards)

def train(): 
    data = Data(args.min_size, args.max_size)
    env = Environment(data.get_random_map(), args.show_screen, args.max_size)
    model = Policy(env, args)
    if args.load_checkpoint:
        model.load_checkpoint(name = args.model_name)
    mem = ReplayMemory(args.replay_memory_size, args.batch_size)
    
    trainer = Trainer(model, learning_rate=args.lr)
    
    visual_mean_value_3 = deque(maxlen = 5000)
    visual_mean_value_4 = deque(maxlen = 5000)
    visual_value_3 = deque(maxlen = 100)
    visual_value_4 = deque(maxlen = 100)
    
    
    for _ep in range(args.n_epochs):
        print('Training_epochs: {}'.format(_ep + 1))
        for _game in range(args.n_games):
            start = time.time()
            obs, pis, returns = execute_episode(model, 128, env, args)
            mem.add_all([obs, pis, returns])
            batch = mem.sample()
            vl, pl = trainer.train(batch)
            end = time.time()
            
            visual_value_3.append(vl)
            visual_value_4.append(pl)
            visual_mean_value_3.append(np.mean(visual_value_3))
            visual_mean_value_4.append(np.mean(visual_value_4))
            env.soft_reset()
        plot(visual_mean_value_3, True, 'red')
        plot(visual_mean_value_4, True, 'blue')
        print("Time: {0: >#.3f}s". format(1000*(end - start)))
        if args.saved_checkpoint:
            if _ep % 5 == 0:
                model.save_checkpoint(args.model_name)
        # print('Completed episodes')
        env.punish = 0
        # env = Environment(data.get_random_map(), args.show_screen, args.max_size)

def test():
    data = Data(args.min_size, args.max_size)
    rand_map = data.get_random_map()
    env = Environment(rand_map, args.show_screen, args.max_size)
    # model = ActorCritic_2(8, 288, action_dim = env.action_dim, lr = args.lr)
    model = Policy(env, args)
    model.load_checkpoint(name = args.model_name)
    
    visual_mean_value_3 = deque(maxlen = 5000)
    visual_mean_value_4 = deque(maxlen = 5000)
    visual_value_3 = deque(maxlen = 1)
    visual_value_4 = deque(maxlen = 1)
    win = 0
    lose = 0
    
    for _ep in range(args.n_epochs):
        print('Training_epochs: {}'.format(_ep + 1))
        for _iter in count():
            if args.show_screen:
                env.render()
            # initialize
            actions_1 = []
            actions_2 = []
            # update by step
            soft_state_1 = env.get_obs_for_states(env.get_observation(0))[0]
            soft_agent_pos_1 = env.get_agent_pos(0)
            
            # soft_state_2 = env.get_observation(1)
            # soft_agent_pos_2 = env.get_agent_pos(1)
            # fit for each agent
            for agent_id in range(env.n_agents):
                agent_state_1 = env.get_obs_for_states([soft_state_1, env.get_agent_state(agent_id, soft_agent_pos_1)])
                action_1, _ = model.step(agent_state_1)
                action_1 = np.argmax(action_1[0])
                valid_1, next_state_1, reward_1 = env.soft_step(agent_id, soft_state_1, action_1, soft_agent_pos_1)
                soft_state_1 = next_state_1
                actions_1.append(action_1)
                
                # agent_state_2 = np.array(flatten([soft_state_2, env.get_agent_state(agent_id, soft_agent_pos_2)]))
                # action_2, log_prob_2, state_value_2 = agent.select_action(agent_state_2)
                # state_values_2.append(state_value_2)
                # valid_2, next_state_2, reward_2 = env.soft_step(agent_id, soft_state_2, action_2, soft_agent_pos_2)
                # soft_state_2 = next_state_2
                
                actions_2.append(np.random.randint(0, env.n_actions - 1))
                # actions_2 = [0] * agent.n_agents)
            next_state, final_reward, done, _ = env.step(actions_1, actions_2, args.show_screen)
            if final_reward >= 0:
                win += 1
            else:
                lose += 1
            visual_value_3.append(win)
            visual_value_4.append(lose)
            if done:
                break
                
        start = time.time()
        end = time.time()
        
        visual_mean_value_3.append(np.mean(visual_value_3))
        visual_mean_value_4.append(np.mean(visual_value_4))
        plot(visual_mean_value_3, False, 'red')
        plot(visual_mean_value_4, True, 'blue')
        print("Time: {0: >#.3f}s". format(1000*(end - start)))
        if args.saved_checkpoint:
            if _ep % 5 == 0:
                model.save_checkpoint(args.model_name)
        print('Completed episodes')
        env.punish = 0
        env.reset()
        env = Environment(data.get_random_map(), args.show_screen, args.max_size)

if __name__ == "__main__":
    if args.run_mode == "train":
        train()
    if args.run_mode == "test":
        test()