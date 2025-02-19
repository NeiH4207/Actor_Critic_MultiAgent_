"""
@author: Vu Quoc Hien <NeiH4207@gmail.com>
"""

import numbers
import numpy as np
import torch
import shutil
import torch.autograd as Variable
import matplotlib.pyplot as plt

class dotdict(dict):
    def __getattr__(self, name):
        return self[name]

def dtanh(x):
    return 1 / np.cosh(x) ** (0.2)

# print([dtanh(i) for i in range(10)])

def vizualize(arr, name, cl = 'red'):
#     ax.set_yticks(np.arange(0, 1.04, 0.15))
    ax = plt.figure(num=1, figsize=(4, 3), dpi=200).gca()
    ax.set_xticks(np.arange(0, 100000, 10000))
    plt.grid()
    plt.xlabel("Iteration")
    plt.ylabel("Loss value")
#     plt.xlim(-3, 3)
#     plt.ylim(1000, 1220)
    plt.plot(arr, color = cl, linewidth = 0.9)
    # plt.legend(bbox_to_anchor=(0.785, 1), loc='upper left', borderaxespad=0.1)
    # name = name + '.pdf'
    plt.savefig(name,bbox_inches='tight')
    plt.show()
    
def plot(values, vtype = 'Scores'):
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.grid()
    ax.set_xlabel('Episode')
    ax.set_ylabel(vtype)
    ax.plot(values[0], color='red', label='Bot 1')
    ax.plot(values[1], color='blue', label='Bot 2')
    ax.set_xlabel('Episode', fontsize=16)
    ax.set_ylabel(vtype, fontsize=16)

    plt.savefig('./Experiments/' + vtype + '.pdf',bbox_inches='tight')
    plt.show()



def flatten(data):
    new_data = []
    # data = copy.deepcopy(data)  
    for element in data:
        if (isinstance(element, numbers.Number) ):
            new_data.append(element)
        else:
            element = flatten(element)
            for x in element:
                new_data.append(x)
    return new_data

def soft_update(target, source, tau):
	"""
	Copies the parameters from source network (x) to target network (y) using the below update
	y = TAU*x + (1 - TAU)*y
	:param target: Target network (PyTorch)
	:param source: Source network (PyTorch)
	:return:
	"""
	for target_param, param in zip(target.parameters(), source.parameters()):
		target_param.data.copy_(
			target_param.data * (1.0 - tau) + param.data * tau
		)


def hard_update(target, source):
	"""
	Copies the parameters from source network to target network
	:param target: Target network (PyTorch)
	:param source: Source network (PyTorch)
	:return:
	"""
	for target_param, param in zip(target.parameters(), source.parameters()):
			target_param.data.copy_(param.data)


def save_training_checkpoint(state, is_best, episode_count):
	"""
	Saves the models, with all training parameters intact
	:param state:
	:param is_best:
	:param filename:
	:return:
	"""
	filename = str(episode_count) + 'checkpoint.path.rar'
	torch.save(state, filename)
	if is_best:
		shutil.copyfile(filename, 'model_best.pth.tar')


# Based on http://math.stackexchange.com/questions/1287634/implementing-ornstein-uhlenbeck-in-matlab
class OrnsteinUhlenbeckActionNoise:

	def __init__(self, action_dim, mu = 0, theta = 0.15, sigma = 0.2):
		self.action_dim = action_dim
		self.mu = mu
		self.theta = theta
		self.sigma = sigma
		self.X = np.ones(self.action_dim) * self.mu

	def reset(self):
		self.X = np.ones(self.action_dim) * self.mu

	def sample(self):
		dx = self.theta * (self.mu - self.X)
		dx = dx + self.sigma * np.random.randn(len(self.X))
		self.X = self.X + dx
		return self.X
