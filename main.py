import retro
from gym.wrappers import Monitor
import numpy as np
from DDQAgent import DDQAgent

# Build game enviroment
env = retro.make(game="SuperMarioWorld-Snes", state="YoshiIsland1")

# Recoder video for every 10 episodes
env = Monitor(env, './video', force=True, video_callable=lambda episode_id: episode_id%10==0)

# How many episodes to play
n_games = 5000

# Initialize double deep q agent
agent = DDQAgent(
    alpha=0.0005,       # Learning Rate
    gamma=0.99,         # Discount factor. Make future event weighted less
    n_actions=256,      # Number of possible actions. 2^8 for 8 inputs
    epsilon=1.0,        # How often should agent "explore" (Do random action). Set to 0 for well train model
    batch_size=64,      # How many samples should this agent train on
    input_dimension=(224, 256, 3),  # Input dimension.
    memory_size=1000,   # Max capacity of ReplayBuffer
)

#Load agent
agent.load_model()

#Keep track of scores
scores = []

#Some variable
renderAtEpisode = 10    #At which episode should game be render
learnEvery = 300        #Keep track of how many frame between each time agent learn
remeberEvery = 10       #How many frame between each time agent remember

#Start playing
for i in range(n_games):

    done = False 
    score = 0
    oberservation = env.reset() / 255.0 #Scale rgb to between 0 and 1
    frame_counter = 0

    while not done:
        # Render only at target episode
        # if i % renderAtEpisode == 0:
        #     env.render()

        # Time Step
        action = agent.choose_action(oberservation)
        new_oberservation, reward, done, _ = env.step(action)
        new_oberservation = new_oberservation / 255.0
        score += reward
        oberservation = new_oberservation

        # Agent only remember 1 frame for every 10 frame
        if frame_counter % remeberEvery == 0:
            agent.remember(oberservation, action, reward, new_oberservation, done)

        # Agent will learn every 300 frame
        if frame_counter % learnEvery == 0:
            agent.learn()

        frame_counter+=1
    
    scores.append(score)
    avg_score = np.mean(scores[max(0, i - 100) : i + 1])
    print(
        "Episode",
        i,
        "score %.2f" % score,
        "Average score %.2f" % avg_score,
        "Epsilon %.2f" % agent.epsilon,
    )

    #Save model every 10 episodes
    if i % 10 == 0 and i > 0:
        agent.save_model()
