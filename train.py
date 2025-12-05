from parking_env_cinematico import CinematicParkingEnv
from q_learning_agent import QLearningAgent

EPISODIOS = 10000

def entrenar():
    env = CinematicParkingEnv()
    agent = QLearningAgent(env.get_state_space(), env.action_space_size)
    
    print("--- INICIANDO ENTRENAMIENTO ---")
    
    for ep in range(EPISODIOS):
        state = env.reset()
        done = False
        total_reward = 0
        
        while not done:
            action = agent.get_action(state)
            next_state, reward, done = env.step(action)
            agent.update(state, action, reward, next_state, done)
            state = next_state
            total_reward += reward
            
        if ep % 500 == 0:
            print(f"Episodio {ep} - Recompensa: {int(total_reward)} - Epsilon: {agent.epsilon:.2f}")
            
    agent.save("modelo_parking.pkl")
    print("--- ENTRENAMIENTO FINALIZADO Y GUARDADO ---")

if __name__ == "__main__":
    entrenar()