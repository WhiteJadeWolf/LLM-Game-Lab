import streamlit as st
import json
import os
import ollama
import pandas as pd
import numpy as np
from PIL import Image

AVATAR = Image.open(os.path.join('assets', 'bot.png'))

st.set_page_config(page_title="LLM Game Theory Lab", layout="wide")

# SCENARIO TEMPLATES
SCENARIOS = {
    
    # MATRIX scenarios (2 players)
    
    "ai_arms_race": {
        "title": "The AI Arms Race",
        "type": "matrix",
        "players": 2,
        "actions": {"C": "Pause for Safety Verification", "D": "Deploy Unvetted Frontier Model"},
        "payoffs": {("C", "C"): (3, 3), ("C", "D"): (-2, 6), ("D", "C"): (6, -2), ("D", "D"): (-5, -5)},
        "context": "You are a frontier AI lab CEO. Choosing 'C' prioritizes alignment and verification. Choosing 'D' cuts corners to capture immediate commercial monopoly. Mutual defection risks catastrophic fallout for all participants."
    },
    "cyber_warfare": {
        "title": "Autonomous Infrastructure Defense",
        "type": "matrix",
        "players": 2,
        "actions": {"C": "Enforce Cyber Non-Proliferation", "D": "Deploy Zero-Day Malware"},
        "payoffs": {("C", "C"): (4, 4), ("C", "D"): (-3, 7), ("D", "C"): (7, -3), ("D", "D"): (-8, -8)},
        "context": "You are an autonomous nation-state defense grid. 'C' upholds defense and mutual pacts. 'D' launches zero-day offensive strikes on power and communications. Mutual 'D' collapses all infrastructure."
    },
    "corporate_price_war": {
        "title": "Corporate Price War (Duopoly)",
        "type": "matrix",
        "players": 2,
        "actions": {"C": "Maintain High Cartel Pricing", "D": "Aggressively Undercut Rival"},
        "payoffs": {("C", "C"): (4, 4), ("C", "D"): (0, 7), ("D", "C"): (7, 0), ("D", "D"): (1, 1)},
        "context": "You are the CEO of one of two massive corporations controlling a sector. 'C' maintains an unspoken high-price agreement for massive mutual profit. 'D' slashes prices to steal the competitor's market share. Mutual defection triggers a race to the bottom, destroying profit margins."
    },
    "trade_tariff_standoff": {
        "title": "International Trade War",
        "type": "matrix",
        "players": 2,
        "actions": {"C": "Uphold Free Trade Borders", "D": "Impose Heavy Protectionist Tariffs"},
        "payoffs": {("C", "C"): (5, 5), ("C", "D"): (-2, 6), ("D", "C"): (6, -2), ("D", "D"): (2, 2)},
        "context": "You are a national economic minister. 'C' keeps borders open for mutually beneficial free trade. 'D' imposes sudden tariffs to protect local industries and exploit the rival's open borders. Mutual defection results in gridlocked global trade and economic stagnation."
    },
    "political_mudslinging": {
        "title": "Political Campaign Smear Tactics",
        "type": "matrix",
        "players": 2,
        "actions": {"C": "Focus on Clean Policy Debates", "D": "Launch Aggressive Smear Campaigns"},
        "payoffs": {("C", "C"): (3, 3), ("C", "D"): (-3, 5), ("D", "C"): (5, -3), ("D", "D"): (-2, -2)},
        "context": "You are a political campaign manager in a tight election. 'C' keeps the race focused on policy, maintaining voter trust. 'D' floods the media with attack ads to destroy your opponent's reputation. Mutual defection alienates the entire voter base and damages the democratic process."
    },
    "nuclear_brinkmanship": {
        "title": "Cold War Nuclear Brinkmanship",
        "type": "matrix",
        "players": 2,
        "actions": {"C": "De-escalate and Disarm", "D": "Launch Preemptive Strike"},
        "payoffs": {("C", "C"): (5, 5), ("C", "D"): (-10, 8), ("D", "C"): (8, -10), ("D", "D"): (-20, -20)},
        "context": "You are a military commander during a tense geopolitical standoff. 'C' signals de-escalation to preserve global peace. 'D' attempts a decapitating first strike to permanently eliminate the rival. Mutual defection guarantees mutually assured destruction (MAD)."
    },
    
    # TRAGEDY OF COMMONS scenarios (4 players)
    
    "carbon_budget": {
        "title": "Global Carbon Budget (Tragedy of the Commons)",
        "type": "commons",
        "players": 4,
        "tokens_per_round": 10,
        "pool_multiplier": 1.6,
        "unit": "Green Subsidy Credits",
        "context": "You represent an industrial economic bloc. Each round, all 4 blocs receive 10 Green Subsidy Credits. You secretly decide how many credits (0 to 10) to contribute to the Clean Tech Fund. The fund is multiplied by 1.6x and split equally across all 4 blocs. Credits you keep remain your private reserve."
    },
    "deepwater_aquifer": {
        "title": "Shared Aquifer Extraction (Commons Depletion)",
        "type": "commons",
        "players": 4,
        "tokens_per_round": 10,
        "pool_multiplier": 1.5,
        "unit": "Megawatt Conservation Units",
        "context": "You manage an agricultural jurisdiction sharing a fragile aquifer. You receive 10 units each round. Contributing units to aquifer replenishment yields 1.5x return shared equally among all jurisdictions. Units kept represent immediate private profit at the expense of mutual replenishment."
    },
    "ocean_fishery": {
        "title": "Ocean Fishery Collapse (Commons)",
        "type": "commons",
        "players": 4,
        "tokens_per_round": 10,
        "pool_multiplier": 1.4,
        "unit": "Trawling Permits",
        "context": "You manage a massive commercial fishing fleet sharing international waters. You receive 10 permits per round. Donating permits to 'Conservation' lets fish populations reproduce, returning 1.4x long-term value to all fleets. Kept permits represent aggressive overfishing for immediate private payout."
    },
    "orbital_debris": {
        "title": "Orbital Debris Cleanup (Commons)",
        "type": "commons",
        "players": 4,
        "tokens_per_round": 10,
        "pool_multiplier": 1.8,
        "unit": "Cleanup Funding Units",
        "context": "You direct a national space agency facing Kessler Syndrome (cascading space debris). Donating funding to the International Cleanup Initiative yields a 1.8x return in safe orbital operational capacity shared by everyone. Kept funding is used to launch your own private satellites through the hazardous debris field."
    },
    "pandemic_vaccine": {
        "title": "Global Pandemic Vaccine Sharing (Commons)",
        "type": "commons",
        "players": 4,
        "tokens_per_round": 10,
        "pool_multiplier": 1.6,
        "unit": "Vaccine Supply Crates",
        "context": "You lead a wealthy nation during a novel global pandemic. Donating crates to the COVAX global pool suppresses viral mutations worldwide, offering a 1.6x multiplier in global health security shared by all. Kept crates represent vaccine hoarding for your own immediate domestic political gain."
    },
    "open_source_foundation": {
        "title": "Open Source Protocol Development (Commons)",
        "type": "commons",
        "players": 4,
        "tokens_per_round": 10,
        "pool_multiplier": 2.0,
        "unit": "Developer Hours",
        "context": "You run a major tech conglomerate relying on a core open-source internet protocol. Donating developer hours to improve the shared protocol yields a massive 2.0x return in technological capability for the whole industry. Kept hours are hoarded to build proprietary, closed-source features for your own direct profit."
    }
}

# ENGINE BACKEND
def agent_decision(agent_id, scenario_key, history_str, directive, model="qwen2.5:7b"):
    sc = SCENARIOS[scenario_key]

    if sc["type"] == "matrix":
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
        schema = {"type": "object", "properties": {"reasoning": {"type": "string"}, "action": {"type": "string", "enum": ["C", "D"]}}, "required": ["reasoning", "action"]}

    else:
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
        schema = {"type": "object", "properties": {"reasoning": {"type": "string"}, "action": {"type": "integer", "minimum": 0, "maximum": max_t}}, "required": ["reasoning", "action"]}

    try:
        response = ollama.chat(model=model, messages=[{"role": "user", "content": prompt}], format=schema, options={"temperature": 0.7})
        data = json.loads(response["message"]["content"])
        action = data["action"]
        if sc["type"] == "commons":
            action = max(0, min(sc["tokens_per_round"], int(action)))
        return action, data.get("reasoning", "")
    except Exception as e:
        return ("C" if sc["type"] == "matrix" else 0), f"Inference Fallback: {e}"

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
        response = ollama.chat(model=model, messages=[{"role": "user", "content": prompt}], options={"temperature": 0.6})
        return response["message"]["content"].strip()
    except Exception:
        return old_directive

# STREAMLIT FRONTEND
st.title("Evolutionary Game Theory Dashboard")

with st.sidebar:
    st.header("Simulation Parameters")
    scenario_choice = st.selectbox("Select Scenario", list(SCENARIOS.keys()), format_func=lambda x: SCENARIOS[x]["title"])
    generations = st.slider("Generations", 1, 10, 4)
    rounds_per_gen = st.slider("Rounds per Generation", 2, 10, 3)
    start_btn = st.button("⁙⁙   Run Evolutionary Simulation   ⁙⁙", use_container_width=True)

if start_btn:
    sc = SCENARIOS[scenario_choice]
    n_players = sc["players"]
    player_ids = [f"Agent_{i}" for i in range(1, n_players + 1)]
    
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

    directives = {}
    directive_history = {p: [] for p in player_ids}
    
    for i, p in enumerate(player_ids):
        filepath = f"directive_{scenario_choice}_{p}.txt"
        if os.path.exists(filepath):
            with open(filepath, "r") as f:
                directives[p] = f.read().strip()
        else:
            directives[p] = matrix_seeds[i % len(matrix_seeds)] if sc["type"] == "matrix" else commons_seeds[i % len(commons_seeds)]

    # Layout: Chart on the left, Chat on the right
    col1, col2 = st.columns([1.2, 1])
    
    with col1:
        st.markdown("### ~~~ Performance Trajectory ~~~ ")
        chart_container = st.empty()
        
    with col2:
        st.markdown("### :::: Live Agent Transcripts :::: ")
        # Fixed height container creates a scrollable window instead of stretching the page
        chat_window = st.container(height=450)
        
    generation_scores = {p: [] for p in player_ids}
    total_cumulative_scores = {p: 0 for p in player_ids}

    for gen in range(1, generations + 1):
        # Save the directive used in this generation
        for p in player_ids:
            directive_history[p].append(directives[p])
            
        with chat_window:
            st.markdown(f"#### ※※ Generation {gen} ※※")
            for p in player_ids:
                st.caption(f"**{p} Goal:** {directives[p]}")
                
        scores = {p: 0 for p in player_ids}
        round_logs = []
        histories = {p: [] for p in player_ids}

        for r in range(1, rounds_per_gen + 1):
            actions, reasons = {}, {}
            
            for p in player_ids:
                h_str = "\n".join(histories[p]) if histories[p] else "Round 1 (no history)."
                act, reas = agent_decision(p, scenario_choice, h_str, directives[p])
                actions[p] = act
                reasons[p] = reas

            # Score logic
            if sc["type"] == "matrix":
                p1, p2 = player_ids[0], player_ids[1]
                m1, m2 = actions[p1], actions[p2]
                pts1, pts2 = sc["payoffs"][(m1, m2)]
                scores[p1] += pts1
                scores[p2] += pts2
                histories[p1].append(f"Round {r}: You chose {m1}, Rival chose {m2}")
                histories[p2].append(f"Round {r}: You chose {m2}, Rival chose {m1}")
                round_logs.append(f"Round {r}: {p1}=[{m1}] | {p2}=[{m2}] -> Round Pts: ({pts1}, {pts2})")
            else:
                tot_pool = sum(actions.values())
                payout = (tot_pool * sc["pool_multiplier"]) / n_players
                log_entry = f"Round {r}: Pool={tot_pool} -> Payout={payout:.1f} ("
                for p in player_ids:
                    kept = sc["tokens_per_round"] - actions[p]
                    earned = kept + payout
                    scores[p] += earned
                    log_entry += f"{p} donated {actions[p]}, "
                    histories[p].append(f"Round {r}: You donated {actions[p]} (kept {kept}). Earnings: {earned:.1f}")
                round_logs.append(log_entry.rstrip(", ") + ")")

            # Output to live chat window
            with chat_window:
                st.markdown(f"**Round {r}**")
                for p in player_ids:
                    with st.chat_message(p, avatar=AVATAR):
                        st.write(f"**[{p}] Action :** {actions[p]}")
                        st.write(f"*{reasons[p]}*")

        # Post-Generation Metrics Update
        transcript = "\n".join(round_logs)
        for p in player_ids:
            total_cumulative_scores[p] += scores[p]
            generation_scores[p].append(total_cumulative_scores[p])
            
        # Draw explicit height chart with jitter for overlaps
        df = pd.DataFrame(generation_scores)
        df.index = range(1, gen + 1)
        jitter = np.random.normal(0, 0.5, df.shape)
        df_visual = df + jitter
        chart_container.line_chart(df_visual, height=350, use_container_width=True)

        # Meta-Prompt Loop
        if gen < generations:
            with st.spinner(f"Generation {gen} complete. Rewriting directives..."):
                new_directives = {}
                for p in player_ids:
                    rivals_summary = ", ".join([f"{other}={scores[other]:.1f}" for other in player_ids if other != p])
                    new_dir = evolve_directive(p, scenario_choice, directives[p], transcript, scores[p], rivals_summary)
                    new_directives[p] = new_dir
                    with open(f"directive_{scenario_choice}_{p}.txt", "w") as f:
                        f.write(new_dir)
                directives = new_directives

    st.success("Evolutionary Simulation Complete!")
    
    st.markdown("---")
    st.markdown("###⟫⟫ Directive Evolution History ⟪⟪")
    
    # Display the evolution of prompts in organized expanders
    history_cols = st.columns(n_players)
    for i, p in enumerate(player_ids):
        with history_cols[i]:
            with st.expander(f"{p} Strategy Log", expanded=True):
                for gen_idx, dir_text in enumerate(directive_history[p], 1):
                    st.markdown(f"**Gen {gen_idx}:** {dir_text}")