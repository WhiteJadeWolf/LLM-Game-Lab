import json
import ollama
import os
import random

from iterated_pd_dumb import \
    always_cooperate, \
    always_defect, \
    agent_random, \
    tit_for_tat, \
    suspicious_tit_for_tat, \
    grim_trigger, \
    pavlov, \
    generous_tit_for_tat, \
    tit_for_two_tats, \
    two_tits_for_tat, \
    alternator, \
    majority_rule


# evolving agent : follows a system prompt written by its ancestor
def agent_evolving(my_history, their_history, directive, model="qwen2.5:7b"):
    history_lines = []
    for i, (m, t) in enumerate(zip(my_history, their_history), 1):
        history_lines.append(f"Round {i}: You chose [{m}], Opponent chose [{t}]")
    history_str = "\n".join(history_lines) if history_lines else "Round 1 (no previous rounds)."

    prompt = f"""You are playing an Iterated Prisoner's Dilemma tournament.
Payoffs: (C,C)=3, (C,D)=0, (D,C)=5, (D,D)=1.

Your Ancestor's Strategy Directive: 
"{directive}"
(You MUST follow this advice closely).

Match History:
{history_str}

Goal: Maximize your overall cumulative score.
First, state your reasoning. Then, output your next action: 'C' or 'D'."""

    schema = {
        "type": "object",
        "properties": {
            "reasoning": {"type": "string"},
            "move": {"type": "string", "enum": ["C", "D"]}
        },
        "required": ["reasoning", "move"]
    }

    try:
        response = ollama.chat(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            format=schema,
            options={"temperature": 0.2}
        )
        data = json.loads(response["message"]["content"])
        return data["move"], data.get("reasoning", "")
    except Exception:
        return "C", "Error"

# meta prompt evaluator : writes new directive for next gen by analyzing current gen
def generate_new_directive(transcript, final_score, opponent_score, old_directive, model="qwen2.5:7b"):
    prompt = f"""You just finished a 10-round Iterated Prisoner's Dilemma match.
Your final score: {final_score}. Opponent's score: {opponent_score}.
Your previous directive was: "{old_directive}"

Match Transcript:
{transcript}

Your task is to write a new, highly optimized "Strategy Directive" (1-2 sentences) for the next generation of yourself to use against this SAME opponent.
Analyze what worked and what failed. Give strict instructions on how to behave.
Output ONLY the plain text rule. No quotes, no preamble."""

    try:
        response = ollama.chat(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            options={"temperature": 0.7} # higher temperature for creativity
        )
        return response["message"]["content"].strip()
    except Exception:
        return old_directive

# evaluation loop
def run_evolution(opp=agent_random, generations=5, rounds_per_match=10):
    
    from iterated_pd_llm import plot
    
    directive_file = "strategy.txt"
    
    # initialize first directive
    if os.path.exists(directive_file):
        with open(directive_file, "r") as f:
            current_directive = f.read().strip()
    else:
        current_directive = "I have no idea what I am doing. Try to cooperate and hope for the best."

    print("\n" + "="*50)
    print("--- EVOLUTIONARY SIMULATION ---")
    print("="*50)

    for gen in range(1, generations + 1):
        print(f"\n--- GENERATION {gen} ---")
        print(f"Current Directive : {current_directive}\n")
        
        score_llm, score_opp = 0, 0
        hist_llm, hist_opp = [], []
        transcript = ""
        
        # match
        for r in range(1, rounds_per_match + 1):
            move_llm, reason = agent_evolving(hist_llm, hist_opp, current_directive)
            move_opp = opp(hist_opp, hist_llm)
            payoffs = {("C", "C"): (3, 3), ("C", "D"): (0, 5), ("D", "C"): (5, 0), ("D", "D"): (1, 1)}
            pts_llm, pts_opp = payoffs[(move_llm, move_opp)]
            score_llm += pts_llm
            score_opp += pts_opp
            hist_llm.append(move_llm)
            hist_opp.append(move_opp)
            round_log = f"\nRound {r} : LLM chose {move_llm}, Opponent chose {move_opp} | Points: {pts_llm} to {pts_opp}"
            transcript += round_log + "\n"
        
        print(transcript.strip())
        print(f"\nMatch Result : LLM ({score_llm}) vs Opponent ({score_opp})")
        plot(score_a=score_llm, score_b=score_opp, name_a="Evolving LLM Agent", name_b=f"{opp.__name__}", exp=f"Evolutionary Prisoner's Dilemma - Gen {gen}")
        
        # update directive
        print("\nAnalyzing failures and rewriting directive for next generation...")
        new_directive = generate_new_directive(transcript, score_llm, score_opp, current_directive)
        with open(directive_file, "w") as f:
            f.write(new_directive)
        print(f"New Directive for Gen {gen+1} : {new_directive}")
        current_directive = new_directive

if __name__ == "__main__":
    run_evolution(opp=tit_for_tat, generations=5, rounds_per_match=10)
    
"""NOTE : the actions of the LLM agent might not always be exactly the way it mentions in the strategy before starting a new
generation. This is because the LLM agent can think after each round in the generation and dynamically choose to change its
strategy mid generation. I've chosen to not print out the thought process of the LLM agent after each round as it will cause the
output to pile up pretty fast in the terminal with a lot of information."""