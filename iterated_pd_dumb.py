""" ITERATED PRISONER's DILEMMA with FAMOUS STRATEGIC GAME THEORY AGENTS """

import random

# Game Engine

PAYOFFS = {
    ("C", "C"): (3, 3),   # C -> Cooperate, D -> Defect
    ("C", "D"): (0, 5),   
    ("D", "C"): (5, 0),   
    ("D", "D"): (1, 1),   
}

def play_match(agent_a_func, agent_b_func, rounds = 5, quiet = False):
    score_a, score_b = 0, 0
    history_a, history_b = [], []

    if not quiet:
        print(f"--- {agent_a_func.__name__} vs {agent_b_func.__name__} ---")
    
    for r in range(1, rounds + 1):
        move_a = agent_a_func(history_a, history_b)
        move_b = agent_b_func(history_b, history_a)

        points_a, points_b = PAYOFFS[(move_a, move_b)]
        score_a += points_a
        score_b += points_b

        history_a.append(move_a)
        history_b.append(move_b)

        if not quiet:
            print(f"Round {r}: A chose {move_a}, B chose {move_b} | Total Score: {score_a} : {score_b}")
    
    if not quiet:  
        print("--- Match Over ---\n")
    return score_a, score_b


# Classic Game Theory Strategic Agents

def always_cooperate(my_history, their_history):
    """ Always plays Cooperate """
    return "C"

def always_defect(my_history, their_history):
    """ Always plays Defect (Nash equilibrium benchmark) """
    return "D"

def agent_random(my_history, their_history):
    """ Plays Cooperate or Defect completely at random """
    return random.choice(["C", "D"])

def tit_for_tat(my_history, their_history):
    """ Cooperates first, then copies opponent's previous move """
    if not their_history:
        return "C"
    return their_history[-1]

def suspicious_tit_for_tat(my_history, their_history):
    """ Defects on round 1, then mimics opponent's previous move """
    if not their_history:
        return "D"
    return their_history[-1]

def grim_trigger(my_history, their_history):
    """ Cooperates until opponent defects once; defects forever after """
    if "D" in their_history:
        return "D"
    return "C"

def pavlov(my_history, their_history):
    """ Win-Stay, Lose-Shift: Repeats previous move if it earned >= 3 pts, else flips """
    if not my_history:
        return "C"
    
    last_my_move = my_history[-1]
    last_their_move = their_history[-1]
    last_score, _ = PAYOFFS[(last_my_move, last_their_move)]
    
    # if satisfied with outcome (earned 3 or 5) keep same move, otherwise switch
    if last_score >= 3:
        return last_my_move
    return "D" if last_my_move == "C" else "C"

def generous_tit_for_tat(my_history, their_history, forgiveness_rate=0.1):
    """ Copies opponent's move, but forgives a defection with a 10% chance """
    if not their_history:
        return "C"
    if their_history[-1] == "D":
        return "C" if random.random() < forgiveness_rate else "D"
    return "C"

def tit_for_two_tats(my_history, their_history):
    """ Highly forgiving : Cooperates unless the opponent defected in BOTH of the last two rounds """
    if len(their_history) < 2:
        return "C"
    if their_history[-1] == "D" and their_history[-2] == "D":
        return "D"
    return "C"

def two_tits_for_tat(my_history, their_history):
    """ Highly punitive : Defects twice for every single defection by the opponent """
    if not their_history:
        return "C"
    if "D" in their_history[-2:]:
        return "D"
    return "C"

def alternator(my_history, their_history):
    """ Ignores the opponent completely and just alternates C, D, C, D """
    if not my_history:
        return "C"
    return "D" if my_history[-1] == "C" else "C"

def majority_rule(my_history, their_history):
    """ Plays whatever move the opponent has played most frequently (defaults to C on a tie) """
    if not their_history:
        return "C"
    d_count = their_history.count("D")
    c_count = their_history.count("C")
    return "D" if d_count > c_count else "C"

# every agent plays against every agent (including themselves)
def run_tournament(agents, rounds = 10, quiet = True):
    print("\n" + "="*40)
    print(f"* TOURNAMENT STARTING WITH ({len(agents)} agents) *")
    print("="*40)
    leaderboard = {agent.__name__: 0 for agent in agents} # track total points across all matches
    
    for agent_a in agents:
        for agent_b in agents:
            score_a, score_b = play_match(agent_a, agent_b, rounds=rounds, quiet = quiet) # runs quietly by default
            leaderboard[agent_a.__name__] += score_a # Add to A's total score (B's score will be counted when B is agent_a)
            
    sorted_leaders = sorted(leaderboard.items(), key=lambda x: x[1], reverse=True)
    print("-"*40)
    print("* FINAL TOURNAMENT STANDINGS *")
    print("-"*40)
    for rank, (name, score) in enumerate(sorted_leaders, 1):
        print(f"{rank}. {name.ljust(25)} {score} pts")
    print("="*40 + "\n")
    
if __name__ == "__main__":
    ALL_AGENTS = [always_cooperate, always_defect, agent_random, tit_for_tat, suspicious_tit_for_tat, grim_trigger, pavlov,generous_tit_for_tat, tit_for_two_tats, two_tits_for_tat, alternator, majority_rule]
    run_tournament(ALL_AGENTS, rounds = 10, quiet = True)