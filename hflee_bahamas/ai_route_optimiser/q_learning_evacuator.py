import numpy as np
import random

# Graph structure: adjacency list
graph = {
    0: [1, 2],   # 0 = Start
    1: [3],
    2: [3, 4],
    3: [4],      # 4 = Safe Zone
    4: []        # Terminal
}

location_names = {
    0: "marsh_harbor",
    1: "road_a",
    2: "road_b",
    3: "junction",
    4: "nassua (safe zone)"
}

# Hurricane severity at each location
hurricane_levels = {
    0: 4,  # Evac zone
    1: 2,
    2: 3,
    3: 1,
    4: 0  # Safe zone
}

hurricane_impact_map = {
    1: -1,
    2: -3,
    3: -5,
    4: -8,
    5: -10
}

evacuation_threshold = 3

# Parameters
gamma = 0.8  # Discount factor
alpha = 0.1  # Learning rate
episodes = 500
epsilon = 0.2  # Exploration factor

# Q-table: [states x actions]
q_table = np.zeros((len(graph), len(graph)))

# Rewards
def get_reward(current, next):
    if next == 4:
        return 10  # Safe zone reached
    elif hurricane_levels[next] >= evacuation_threshold:
        return hurricane_impact_map[hurricane_levels[next]]  # Penalize danger
    else:
        return -1  # Movement cost

# Q-learning loop
for ep in range(episodes):
    state = 0  # Start at marsh_harbor

    while state != 4:
        if random.uniform(0, 1) < epsilon:
            action = random.choice(graph[state])
        else:
            # Choose best known action
            q_vals = [q_table[state][a] for a in graph[state]]
            best_action_idx = np.argmax(q_vals)
            action = graph[state][best_action_idx]

        reward = get_reward(state, action)
        future = max([q_table[action][a] for a in graph[action]] or [0])
        q_table[state][action] += alpha * (reward + gamma * future - q_table[state][action])

        state = action

# Show learned Q-values
print("\nLearned Q-Table:")
print(q_table.round(2))

# Trace optimal path
print("\nOptimal route from marsh_harbor:")
state = 0
path = [location_names[state]]

while state != 4:
    next_states = graph[state]
    next_state = max(next_states, key=lambda a: q_table[state][a])
    path.append(location_names[next_state])
    state = next_state

print(" → ".join(path))
