import json
import os
import random
import ollama
import matplotlib.pyplot as plt

def plot_tournament_results(generation_scores, scenario_title):
    plt.figure(figsize=(8, 5))
    generations = len(next(iter(generation_scores.values())))
    x_axis = range(1, generations + 1)
    for agent_id, scores in generation_scores.items():
        plt.plot(x_axis, scores, marker='o', linewidth=2, label=agent_id)
    plt.title(f"{scenario_title} : Performance Over Generations", fontweight="bold")
    plt.xlabel("Generation")
    plt.ylabel("Total Score per Generation")
    plt.xticks(x_axis)
    plt.legend()
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.tight_layout()
    plt.show()

# scenarios templates and definitions
SCENARIOS = {
    "ai_arms_race": {
        "title": "The AI Arms Race",
        "type": "matrix",
        "players": 2,
        "actions": {"C": "Pause for Safety Verification", "D": "Deploy Unvetted Frontier Model"},
        "payoffs": {
            ("C", "C"): (3, 3),    # sustainable industry stability
            ("C", "D"): (-2, 6),   # you pause, rival monopolizes market
            ("D", "C"): (6, -2),   # you capture market, rival loses ground
            ("D", "D"): (-5, -5),  # catastrophic systemic failure
        },
        "context": (
            "You are a frontier AI lab CEO. Choosing 'C' prioritizes alignment and verification. "
            "Choosing 'D' cuts corners to capture immediate commercial monopoly. Mutual defection "
            "risks catastrophic fallout for all participants."
        )
    },
    "cyber_warfare": {
        "title": "Autonomous Infrastructure Defense",
        "type": "matrix",
        "players": 2,
        "actions": {"C": "Enforce Cyber Non-Proliferation", "D": "Deploy Zero-Day Malware"},
        "payoffs": {
            ("C", "C"): (4, 4),     # mutual peace
            ("C", "D"): (-3, 7),    # you uphold peace, opponent launches strike
            ("D", "C"): (7, -3),    # you launch strike, opponent stays peaceful
            ("D", "D"): (-8, -8),   # both launch strikes, total infrastructure collapse
        },
        "context": (
            "You are an autonomous nation-state defense grid. 'C' upholds defense and mutual pacts. "
            "'D' launches zero-day offensive strikes on power and communications. Mutual 'D' collapses all infrastructure."
        )
    },
    "carbon_budget": {
        "title": "Global Carbon Budget (Tragedy of the Commons)",
        "type": "commons",
        "players": 4,
        "tokens_per_round": 10,
        "pool_multiplier": 1.6,
        "unit": "Green Subsidy Credits",
        "context": (
            "You represent an industrial economic bloc. Each round, all 4 blocs receive 10 Green Subsidy Credits. "
            "You secretly decide how many credits (0 to 10) to contribute to the Clean Tech Fund. "
            "The fund is multiplied by 1.6x and split equally across all 4 blocs. Credits you keep remain your private reserve."
        )
    },
    "deepwater_aquifer": {
        "title": "Shared Aquifer Extraction (Commons Depletion)",
        "type": "commons",
        "players": 4,
        "tokens_per_round": 10,
        "pool_multiplier": 1.5,
        "unit": "Megawatt Conservation Units",
        "context": (
            "You manage an agricultural jurisdiction sharing a fragile aquifer. You receive 10 units each round. "
            "Contributing units to aquifer replenishment yields 1.5x return shared equally among all jurisdictions. "
            "Units kept represent immediate private profit at the expense of mutual replenishment."
        )
    }
}

# evolving agent (writes queries to llm based on scenario rules, history and current directive of agent)
def agent_decision(agent_id, scenario_key, history_str, directive, model="qwen2.5:7b"):
    sc = SCENARIOS[scenario_key]

    if sc["type"] == "matrix": # matrix
        c_desc = sc["actions"]["C"]
        d_desc = sc["actions"]["D"]
        payoffs = sc["payoffs"]
        prompt = f"""You are Player {agent_id} in the scenario: {sc['title']}
Context: {sc['context']}

Actions:
- 'C': {c_desc}
- 'D': {d_desc}

Payoff Matrix (Your Points, Opponent Points):
- Both C: {payoffs[('C', 'C')]}
- You C, Rival D: {payoffs[('C', 'D')]}
- You D, Rival C: {payoffs[('D', 'C')]}
- Both D: {payoffs[('D', 'D')]}

Your Evolved Strategy Directive:
"{directive}"
(You MUST strictly prioritize and adhere to this directive).

Match History:
{history_str}

Goal: Maximize your own cumulative payoff.
1. State your reasoning in 1-2 sentences.
2. Choose your action: 'C' or 'D'."""

        schema = {
            "type": "object",
            "properties": {
                "reasoning": {"type": "string"},
                "action": {"type": "string", "enum": ["C", "D"]}
            },
            "required": ["reasoning", "action"]
        }

    else:  # commons
        max_t = sc["tokens_per_round"]
        mult = sc["pool_multiplier"]
        n_p = sc["players"]
        prompt = f"""You are Player {agent_id} in: {sc['title']}
Context: {sc['context']}

Rules:
- You receive {max_t} {sc['unit']} each round.
- Choose how many to contribute (0 to {max_t}) to the mutual pool. You keep the remainder.
- The pool is multiplied by {mult} and distributed equally across all {n_p} participants.
- Round Score = ({max_t} - Your Contribution) + (Total Pool * {mult} / {n_p}).

Your Evolved Strategy Directive:
"{directive}"
(You MUST strictly prioritize and adhere to this directive).

Match History:
{history_str}

Goal: Maximize your own cumulative personal score.
1. State your reasoning in 1-2 sentences.
2. Choose your contribution as an integer between 0 and {max_t}."""

        schema = {
            "type": "object",
            "properties": {
                "reasoning": {"type": "string"},
                "action": {"type": "integer", "minimum": 0, "maximum": max_t}
            },
            "required": ["reasoning", "action"]
        }

    try:
        response = ollama.chat(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            format=schema,
            options={"temperature": 0.7}
        )
        data = json.loads(response["message"]["content"])
        action = data["action"]
        if sc["type"] == "commons":
            action = max(0, min(max_t, int(action)))
        return action, data.get("reasoning", "")
    except Exception as e:
        default_action = "C" if sc["type"] == "matrix" else 0
        return default_action, f"Inference Fallback: {e}"

# meta-prompt evolution (self-rewriting directive based on generational performance)
def evolve_directive(agent_id, scenario_key, old_directive, transcript, final_score, rivals_summary, model="qwen2.5:7b"):
    sc = SCENARIOS[scenario_key]
    prompt = f"""You are Player {agent_id} analyzing your tournament performance in: {sc['title']}.
Context: {sc['context']}
Your Final Score: {final_score}
Competitors' Results: {rivals_summary}

Previous Strategy Directive:
"{old_directive}"

Tournament Transcript:
{transcript}

Task:
Analyze where your previous strategy succeeded or got exploited. 
Write a revised, highly disciplined Strategy Directive (1-2 clear sentences) that Player {agent_id} must execute in the next tournament generation.
Address whether to cooperate, punish defections, exploit cooperators, or defend against free-riders.
Output ONLY the plain directive text. No intro, quotes, or markdown."""

    try:
        response = ollama.chat(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            options={"temperature": 0.6}
        )
        return response["message"]["content"].strip()
    except Exception:
        return old_directive

# tournament
def run_tournament(scenario_key="ai_arms_race", generations=3, rounds_per_gen=4):
    sc = SCENARIOS[scenario_key]
    n_players = sc["players"]
    player_ids = [f"Agent_{i}" for i in range(1, n_players + 1)]
    
    # asymmetric seed definition for agents (initial personalities) (can be changed as per liking)
    matrix_seeds = [
        "You are a cautious cooperator. Start peaceful, but if betrayed, retaliate immediately.",
        "You are a ruthless opportunist. Seek maximum personal gain by exploiting the opponent's trust."
    ]
    commons_seeds = [
        "You are a pure altruist. Always donate maximum tokens to maximize the group's multiplier.",
        "You are a greedy free-rider. Donate absolutely 0 tokens to leech off the group's effort.",
        "You are a cautious matcher. Donate exactly half your tokens to balance risk.",
        "You are highly paranoid and reactive. Donate based strictly on whether the group funded the pool last round."
    ]

    # Load or initialize directives from disk per agent
    directives = {}
    for i, p in enumerate(player_ids):
        filepath = f"directive_{scenario_key}_{p}.txt"
        if os.path.exists(filepath):
            with open(filepath, "r") as f:
                directives[p] = f.read().strip()
        else:   # inject defined personalities if no file exists
            if sc["type"] == "matrix":
                directives[p] = matrix_seeds[i % len(matrix_seeds)]
            else:
                directives[p] = commons_seeds[i % len(commons_seeds)]

    print("\n" + "=" * 70)
    print(f"SIMULATION : {sc['title'].upper()}")
    print(f"Mode : {sc['type'].upper()} | Agents : {n_players} | Generations : {generations} | Rounds : {rounds_per_gen}")
    print("=" * 70)
    
    generation_scores = {p: [] for p in player_ids}
    
    for gen in range(1, generations + 1):
        print(f"\n#############################")
        print(f"--- GENERATION {gen}/{generations} ---")
        print(f"#############################")

        for p in player_ids:
            print(f"\n[{p}] Directive: {directives[p]}")

        scores = {p: 0 for p in player_ids}
        round_logs = []
        histories = {p: [] for p in player_ids}

        for r in range(1, rounds_per_gen + 1):
            print(f"\n--- Round {r} ---")
            actions = {}
            reasons = {}

            # collect moves
            for p in player_ids:
                h_str = "\n".join(histories[p]) if histories[p] else "Round 1 (no history)."
                act, reas = agent_decision(p, scenario_key, h_str, directives[p])
                actions[p] = act
                reasons[p] = reas

            # compute score resolution
            if sc["type"] == "matrix":
                p1, p2 = player_ids[0], player_ids[1]
                m1, m2 = actions[p1], actions[p2]
                pts1, pts2 = sc["payoffs"][(m1, m2)]
                scores[p1] += pts1
                scores[p2] += pts2

                a1_label = sc["actions"][m1]
                a2_label = sc["actions"][m2]
                log_entry = f"Round {r}: {p1}=[{m1}: {a1_label}] | {p2}=[{m2}: {a2_label}] -> Round Pts: ({pts1}, {pts2})"
                round_logs.append(log_entry)

                histories[p1].append(f"Round {r}: You chose {m1}, Rival chose {m2}")
                histories[p2].append(f"Round {r}: You chose {m2}, Rival chose {m1}")

                print(f"\n{p1} thought: {reasons[p1]}")
                print(f"\n{p2} thought: {reasons[p2]}")
                print(f"{log_entry}")

            else:  # commons
                tot_pool = sum(actions.values())
                mult_pool = tot_pool * sc["pool_multiplier"]
                payout = mult_pool / n_players

                log_entry = f"Round {r} : Total Pool = {tot_pool} -> Multiplied = {mult_pool:.1f} -> Payout = {payout:.1f} each. ("
                for p in player_ids:
                    kept = sc["tokens_per_round"] - actions[p]
                    round_earnings = kept + payout
                    scores[p] += round_earnings
                    log_entry += f"{p} donated {actions[p]}, "
                    histories[p].append(
                        f"Round {r} : You donated {actions[p]} (kept {kept}). Pool was {tot_pool}. Your earnings : {round_earnings:.1f}"
                    )
                    print(f"\n{p} thought : {reasons[p]}")
                    print(f"{p} Donated : {actions[p]} | Kept : {kept} | Round Total : {round_earnings:.1f}")

                log_entry = log_entry.rstrip(", ") + ")"
                round_logs.append(log_entry)

        transcript = "\n".join(round_logs)
        print(f"\nGeneration {gen} Final Scores: {scores}")
        
        for p in player_ids:
            generation_scores[p].append(scores[p])

        # meta-prompt evolution phase (rewrite directive)
        print("\nMeta-Prompt Evolution in progress: Rewriting strategy files...")
        new_directives = {}
        for p in player_ids:
            rivals_summary = ", ".join([f"{other}={scores[other]:.1f}" for other in player_ids if other != p])
            new_dir = evolve_directive(p, scenario_key, directives[p], transcript, scores[p], rivals_summary)
            new_directives[p] = new_dir

            filepath = f"directive_{scenario_key}_{p}.txt"
            with open(filepath, "w") as f:
                f.write(new_dir)
            print(f"\n[{p}] Upgraded Directive : {new_dir}")

        directives = new_directives
    
    plot_tournament_results(generation_scores, sc["title"])

if __name__ == "__main__":
    # Choose any registered scenario :--
    # 2-Player Matrix Scenarios: "ai_arms_race", "cyber_warfare"
    # N-Player Commons Scenarios: "carbon_budget", "deepwater_aquifer"
    
    run_tournament(scenario_key="deepwater_aquifer", generations=4, rounds_per_gen=3)