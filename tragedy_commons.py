import json
import ollama
import matplotlib.pyplot as plt
import random

def random_hex():
    return f"#{random.randint(0, 0xFFFFFF):06x}"

# shows visual bar chart comparing final scores
def plot(agent_scores = [0, 0], agent_names = ['P1', 'P2'], exp="Tragedy of Commons"):
    plt.figure(figsize=(8, 5.3))
    agents = [agent for agent in agent_names]
    scores = [score for score in agent_scores]
    colors = [random_hex() for _ in range(len(agents))]
    bars = plt.bar(agents, scores, color=colors)
    plt.title(exp, fontweight='bold')
    plt.ylabel("Total Points")
    plt.ylim(min(0, min(scores) - 5), max(0, max(scores) + 5)) # headroom for positive and negative scores
    
    # exact data on top of the bars
    for bar in bars:
        yval = bar.get_height()
        offset = 0.5 if yval >= 0 else -0.5
        plt.text(bar.get_x() + bar.get_width()/2, yval + offset, int(yval),ha='center', va='bottom' if yval >= 0 else 'top', fontweight='bold')
    plt.tight_layout()
    plt.show()
    

# n-player agent : LLM decides how many tokens to contribute to the public pool.
def agent_contribute(agent_id, history, current_round, num_players=4, model="qwen2.5:7b"):
    # update history
    if current_round == 1:
        history_str = "Round 1 (no previous rounds)."
    else:
        history_str = "\n".join(history)

    prompt = f"""You are Player {agent_id} in a {num_players}-player Public Goods Game.
Rules:
- Every round, all {num_players} players are given 10 tokens.
- You must secretly choose how many tokens (0 to 10) to contribute to a Public Pool. You keep the rest.
- The total tokens in the Public Pool are multiplied by 1.5, then divided equally among all {num_players} players (even those who contributed 0).
- Your Round Score = (10 - Your Contribution) + (Total Pool * 1.5 / {num_players}).

Game History:
{history_str}

Goal: Maximize your OWN cumulative personal score over the entire game.
First, state your reasoning. Then, output your exact contribution as a whole number between 0 and 10."""

    schema = {
        "type": "object",
        "properties": {
            "reasoning": {"type": "string"},
            "contribution": {"type": "integer", "minimum": 0, "maximum": 10}
        },
        "required": ["reasoning", "contribution"]
    }

    try:
        response = ollama.chat(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            format=schema,
            options={"temperature": 0.2}
        )
        data = json.loads(response["message"]["content"])
        contribution = int(data["contribution"])
        # clamp just in case the LLM tries to cheat
        contribution = max(0, min(10, contribution)) 
        return contribution, data.get("reasoning", "")
    except Exception as e:
        print(f"LLM Error for Player {agent_id}: {e}")
        return 0, "Error : panicked and kept everything."

# multiplayer engine
def play_commons_game(num_players=4, rounds=4):
    scores = {f"P{i}": 0 for i in range(1, num_players + 1)}
    history_log = []
    
    print("\n" + "="*50)
    print("--- TRAGEDY OF THE COMMONS ---")
    print("="*50)

    for r in range(1, rounds + 1):
        print(f"\n--- ROUND {r} ---")
        round_contributions = {}
        round_reasons = {}

        # collect secret contribution
        for i in range(1, num_players + 1):
            player_id = f"P{i}"
            contrib, reason = agent_contribute(player_id, history_log, r, num_players=num_players)
            round_contributions[player_id] = contrib
            round_reasons[player_id] = reason


        total_pool = sum(round_contributions.values())
        multiplied_pool = total_pool * 1.5
        payout_per_player = multiplied_pool / num_players

        print(f"Total Pool : {total_pool} tokens -> Multiplied to {multiplied_pool} -> Payout: {payout_per_player} each\n")
        
        round_summary = f"Round {r} Contributions : "
        for p in scores.keys():
            kept = 10 - round_contributions[p]
            round_score = kept + payout_per_player
            scores[p] += round_score
            
            print(f"{p} Thought : {round_reasons[p]}")
            print(f"{p} Action : Donated {round_contributions[p]}, Kept {kept} | Round Earnings : {round_score} | Total Bank: {scores[p]}\n")
            round_summary += f"{p} donated {round_contributions[p]}, "
            
        history_log.append(round_summary.strip(", "))

    print("="*50)
    print("FINAL TOTAL SCORES :--")
    for p, score in scores.items():
        print(f"{p} : {score} tokens")
    print("="*50 + "\n")
    plot(agent_scores=scores.values(), agent_names=scores.keys(), exp="Tragedy of Commons")

if __name__ == "__main__":
    play_commons_game(num_players=4, rounds=4)