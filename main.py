import retro
from gym.wrappers import Monitor
import numpy as np
import cv2
from DDQAgent import DDQAgent
import pickle
import time

# Build game enviroment
env = retro.make(game="SuperMarioWorld-Snes", state="Start")

# Recoder video for every 10 episodes
env = Monitor(
    env,
    "./data/video",
    resume=True,
    video_callable=lambda episode_id: episode_id % 10 == 0,
    uid=time.time(),
)

# How many episodes to play
n_games = 100000000

# Initialize double deep q agent
agent = DDQAgent(
    alpha=0.00025,  # Learning Rate
    gamma=0.95,  # Discount factor. Make future event weighted less
    n_actions=8,  # Number of possible actions. 2^8 for 8 inputs
    epsilon=1.0,  # How often should agent "explore" (Do random action). Set to 0 for well train model
    epsilon_dec=0.99999,  # How fast should start perform greedy action
    epsilon_min=0.1,
    batch_size=32,  # How many samples should this agent train on
    input_dimension=(112, 128, 3),  # Input dimension.
    memory_size=25000,  # Max capacity of ReplayBuffer
)


# Load agent
agent.load_model()

# Keep track of scores
scores = [0.]

temp_experience = []
# Some variable
learnEvery = 4  # Keep track of how many frame between each time agent learn
rememberEvery = 4  # How many frame between each time agent remember
frame_skip = 4  # Only getting new action every X frame

# Start playing
for i in range(n_games):

    done = False
    score = 0
    frame_counter = 0

    # Scale rgb to between 0 and 1 and resize frame
    oberservation = cv2.resize(env.reset() / 255.0, (128, 112))

    while not done:
        # Get new actions per X frames skip
        if frame_counter % frame_skip == 0:
            action = agent.choose_action(oberservation)

        # Time Step
        new_oberservation, reward, done, _ = env.step(action)

        # Scale rgb to between 0 and 1 and resize frame
        new_oberservation = cv2.resize(new_oberservation / 255.0, (128, 112))
        score += reward

        # Agent will remember every X frames
        if frame_counter % rememberEvery == 0:
            temp_experience.append(
                (oberservation, action, reward, new_oberservation, done)
            )
            # agent.remember(oberservation, action, reward, new_oberservation, done)

        oberservation = new_oberservation

        # Agent will learn every X frames
        # if frame_counter % learnEvery == 0:
        #     agent.learn()

        frame_counter += 1

    train = False
    if score >= np.mean(scores):
        train = True
        for (oberservation, action, reward, new_oberservation, done) in temp_experience:
            agent.remember(oberservation, action, reward, new_oberservation, done)
            agent.learn()

    scores.append(score)
    avg_score = np.mean(scores)
    temp_experience.clear()

    print(
        "Episode:",
        i,
        "score: %.8f" % score,
        "Average score: %.8f" % avg_score,
        "Epsilon: %.8f" % agent.epsilon,
        "Loss: %.15f" % agent.loss,
        "Train: ",
        train,
    )

    # Write scores to disk
    with open("./data/performance_file.bin", "ab+") as performance_file:
        pickle.dump([score, avg_score, agent.epsilon], performance_file)

    # Save model every 10 episodes
    if i % 10 == 0 and i > 0:
        agent.save_model()
