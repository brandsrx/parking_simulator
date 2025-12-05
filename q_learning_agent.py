import numpy as np
import pickle

class QLearningAgent:
    def __init__(self, state_shape, action_size):
        # Sumamos offsets para manejar indices negativos del ambiente
        self.state_shape = state_shape
        self.action_size = action_size
        self.q_table = np.zeros(state_shape + (action_size,))
        
        self.lr = 0.1
        self.gamma = 0.95
        self.epsilon = 1.0
        self.epsilon_decay = 0.995
        self.epsilon_min = 0.01

    def get_index(self, state):
        # Ajustamos los índices negativos a positivos para la matriz
        # state es (dx, dy, da). dx va de -10 a 10. Sumamos 10 para que sea 0 a 20.
        return (state[0]+10, state[1]+10, state[2]+6)

    def get_action(self, state, train=True):
        idx = self.get_index(state)
        
        if train and np.random.rand() < self.epsilon:
            return np.random.randint(self.action_size)
        
        return np.argmax(self.q_table[idx])

    def update(self, state, action, reward, next_state, done):
        idx = self.get_index(state)
        next_idx = self.get_index(next_state)
        
        current_q = self.q_table[idx][action]
        
        if done:
            target = reward
        else:
            target = reward + self.gamma * np.max(self.q_table[next_idx])
            
        self.q_table[idx][action] += self.lr * (target - current_q)
        
        if done:
            self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)

    def save(self, filename="modelo_parking.pkl"):
        with open(filename, 'wb') as f:
            pickle.dump(self.q_table, f)

    def load(self, filename="modelo_parking.pkl"):
        try:
            with open(filename, 'rb') as f:
                self.q_table = pickle.load(f)
            print("Modelo cargado.")
            self.epsilon = 0 # Si cargamos, no exploramos
            return True
        except:
            print("No se encontró modelo, se usará aleatorio.")
            return False