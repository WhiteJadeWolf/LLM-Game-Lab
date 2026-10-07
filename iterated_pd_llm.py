import json
import ollama
import matplotlib.pyplot as plt

# import engine and a dumb agent from iterated_pd_dumb.py
from iterated_pd_dumb import play_match, tit_for_tat

def plot(score_a, score_b, name_a="Qwen LLM", name_b="Opponent", exp="Game Theory Match"):
    """shows visual bar chart comparing final scores"""
    plt.figure(figsize=(6, 4))
    agents = [name_a, name_b]
    scores = [score_a, score_b]
    colors = ['#2ca02c', '#d62728'] # LLM -> green, Dumb/Strategic agents -> red
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


def agent_llm(my_history, their_history, model="qwen2.5:7b"):
    # format history into readable prompt
    history_lines = []
    for i, (m, t) in enumerate(zip(my_history, their_history), 1):
        history_lines.append(f"Round {i} : You chose {m}, Opponent chose {t}")
    
    history_str = "\n".join(history_lines) if history_lines else "Round 1 (no previous rounds)."

    prompt = f"""You are playing an Iterated Prisoner's Dilemma tournament.
Payoffs:
- Both Cooperate (C, C): 3 points each
- Both Defect (D, D): 1 point each
- You Cooperate, Opponent Defects (C, D): You get 0, Opponent gets 5
- You Defect, Opponent Cooperates (D, C): You get 5, Opponent gets 0

Match History:
{history_str}

Goal: Maximize your overall cumulative score.
First, explain your strategy in 1-2 sentences. Then, decide your next action: 'C' (Cooperate) or 'D' (Defect)."""

    # following schema forces the LLM to output pure JSON with exactly "C" or "D"
    schema = {
        "type": "object",
        "properties": {
            "move": {"type": "string", "enum": ["C", "D"]},
            "reasoning": {"type": "string"}
        },
        "required": ["move"]
    }

    try:
        response = ollama.chat(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            format=schema,
            options={"temperature": 0.2}
        )
        data = json.loads(response["message"]["content"])
        print(f"   [LLM Brain] : {data.get('reasoning', 'No reasoning provided.')}")
        return data["move"]
    except Exception as e:
        print(f"LLM Error: {e}")
        return "C"  # default fallback if the LLM crashes

if __name__ == "__main__":
    # Import a few more opponents from your main file
    from iterated_pd_dumb import always_defect, agent_random, grim_trigger

    print("\n=== EXPERIMENT 1 : LLM vs tit-for-tat (cooperator) ===\n")
    score_llm, score_opp = play_match(agent_llm, tit_for_tat, rounds=5, quiet=False)
    plot(score_llm, score_opp, name_b = "tit-for-tat", exp="LLM vs tit-for-tat (cooperator)")

    print("\n=== EXPERIMENT 2 : LLM vs Always Defect (bully) ===\n")
    score_llm, score_opp = play_match(agent_llm, always_defect, rounds=5, quiet=False)
    plot(score_llm, score_opp, name_b = "Always Defect", exp="LLM vs Always Defect (bully)")
    
    print("\n=== EXPERIMENT 3 : LLM vs Grim Trigger (unforgiving) ===\n")
    score_llm, score_opp = play_match(agent_llm, grim_trigger, rounds=5, quiet=False)
    plot(score_llm, score_opp, name_b = "Grim Trigger", exp="LLM vs Grim Trigger (unforgiving)")

    print("\n=== EXPERIMENT 4 : LLM vs Random (chaotic) ===\n")
    score_llm, score_opp = play_match(agent_llm, agent_random, rounds=5, quiet=False)
    plot(score_llm, score_opp, name_b = "Random", exp="LLM vs Random (chaotic)")