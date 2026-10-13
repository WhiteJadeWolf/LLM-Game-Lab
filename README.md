# LLM GAME LAB

The LLM GAME LAB is a modular, multi-agent Game Theory simulator that leverages local Large Language Models (LLMs) to explore evolutionary strategy. By placing LLM agents into classic economic and psychological scenarios (Matrix games and Tragedy of the Commons), the engine evaluates how autonomous entities negotiate, betray, cooperate, and adapt. The defining feature is **Meta-Prompt Evolution**, where agents independently rewrite their own system directives between tournament generations based on match transcripts and opponent behavior.

## Live Interactive Dashboard

The final build of the project is a real-time Streamlit dashboard (`app.py`) that serves as a visual laboratory for observing LLMs. The user interface is divided into functional zones:

- **Configuration Sidebar:** Contains a scenario selector for the 12 (and growing) domains, simulation sliders to adjust the number of Generations and Rounds per Generation, and the main execution button.
- **Performance Trajectory Chart:** A dynamically rendering line chart tracking cumulative scores. It utilizes a mathematical "jitter" (a microscopic random offset) so that if multiple agents achieve the exact same score by cooperating, their trajectory lines remain visually distinct rather than overlapping.
- **Live Agent Transcripts:** A fixed-height, scrollable chat window displaying the internal monologue of the agents. As each round processes, the UI injects a labeled chat bubble (e.g., **[Agent_1] Action: 10**) followed by the LLM's private reasoning, allowing users to watch their logic unfold live.
- **Directive Evolution Logs:** Expandable drop-down menus storing the complete history of meta-prompts for every agent, allowing users to trace exactly how an agent's strategy evolved from the first generation to the last.

## Repository Structure & Project Evolution

This repository tracks the evolution of the simulator from basic algorithmic tournaments to a full LLM-driven meta-learning dashboard.

```
├── 📁 assets
│   └── 🖼️ bot.png
├── 📝 README.md
├── 🐍 app.py
├── 🐍 cheap_talk.py
├── 🐍 iterated_pd_dumb.py
├── 🐍 iterated_pd_llm.py
├── 🐍 llm_gt_sim.py
├── 🐍 meta_evolution.py
├── 🐍 modern_games.py
└── 🐍 tragedy_commons.py
```

- **`iterated_pd_dumb.py`**: The foundational tournament simulation for an N-round Iterated Prisoner's Dilemma using standard programmatic and famous Game Theory strategies.
- **`iterated_pd_llm.py`**: Upgraded the PD tournament to use LLM agents with integrated score plotting and negative score handling.
- **`modern_games.py`**: Expanded the matrix evaluation to include custom, modern scenario definitions.
- **`cheap_talk.py`**: Introduced pre-action "cheap talk" negotiation phases between dual LLM agents.
- **`tragedy_commons.py`**: Scaled the engine from 2-player matrix games to an N-player Public Goods / Tragedy of the Commons token allocation simulation.
- **`meta_evolution.py`**: Implemented the core meta-prompt evolution loop allowing agents to self-rewrite their strategy files between generations.
- **`llm_gt_sim.py`**: The universal backend engine that unified Matrix and Commons games with the evolutionary learning loops.
- **`app.py`**: The final interactive Streamlit frontend that visualizes live agent reasoning, evolving trajectories, and transcript histories.
- **`assets/`**: Directory containing assets utilized by the Streamlit frontend.

## Architecture & Mechanics

The backend unifies symmetric and asymmetric game theory into a single framework evaluated by local LLMs.

### 1. Game Engines

- **2-Player Matrix Engine:** Resolves standard 2x2 payoff matrices. Agents output "C" (Cooperate) or "D" (Defect). The engine cross-references outputs to award points (e.g., Mutual Defection yields negative points, the Sucker's Payoff yields heavily skewed points).
- **4-Player Commons Engine (Public Goods Game):** Agents receive a round allowance (e.g., 10 tokens) and output an integer to donate to a central pool. The engine multiplies the total pool by a designated scalar (e.g., 1.6x) and divides it equally among all 4 agents, regardless of individual contributions.

### 2. Asymmetric Seeding

To prevent LLMs from getting stuck in a polite, stagnant equilibrium, the engine injects conflicting starting "personalities" into the agents if no previous history exists (e.g., Agent 1 starts as an Altruist, Agent 2 starts as a Free-Rider). This forces immediate strategic conflict.

### 3. The Meta-Evolution Loop

The self-rewriting feedback loop operates in three phases:

1.  **The Play Phase:** Agents receive their current "Strategy Directive", scenario rules, and match history. They generate an action based strictly on that directive.
2.  **The Assessment Phase:** After a generation finishes, agents are fed their total score, rivals' scores, and the complete round-by-round transcript.
3.  **The Rewrite Phase:** The LLM diagnoses where it was exploited or missed points and writes a brand new 1-2 sentence rule. The system saves this locally to a `.txt` file (e.g., `directive_carbon_budget_Agent_1.txt`), which the agent is forced to use in the next generation.

## Technical Stack

- **Language:** Python 3
- **LLM Inference:** Ollama (default model: `qwen2.5:7b`)
- **Frontend UI:** Streamlit
- **Data Visualization:** Pandas, NumPy (for calculations)
- **Persistence:** Local `.txt` files (`directive_<scenario>_<agent_id>.txt`) to store evolving prompts.

## Scenario Library (12 Domains)

### 2-Player Matrix Scenarios

1.  **The AI Arms Race:** Frontier labs balancing alignment/safety vs. rapid unvetted deployment for monopoly.
2.  **Autonomous Infrastructure Defense:** Nation-states choosing between cyber non-proliferation or launching zero-day malware.
3.  **Corporate Price War (Duopoly):** Corporations deciding to maintain cartel pricing or aggressively undercut their rival.
4.  **International Trade War:** Economic ministers choosing between open free trade or imposing protectionist tariffs.
5.  **Political Campaign Smear Tactics:** Campaign managers debating clean policy focus versus aggressive mudslinging.
6.  **Cold War Nuclear Brinkmanship:** Military commanders navigating de-escalation versus preemptive decapitation strikes.

### 4-Player Commons Scenarios

7.  **Global Carbon Budget:** Economic blocs contributing to a Clean Tech Fund or hoarding Green Subsidy Credits.
8.  **Shared Aquifer Extraction:** Agricultural jurisdictions balancing aquifer replenishment against immediate private pumping.
9.  **Ocean Fishery Collapse:** Fishing fleets choosing between conservation permits or aggressive overfishing.
10. **Orbital Debris Cleanup:** Space agencies allocating funds to Kessler Syndrome cleanup versus private satellite launches.
11. **Global Pandemic Vaccine Sharing:** Wealthy nations donating to a COVAX-style pool versus domestic hoarding.
12. **Open Source Protocol Development:** Tech conglomerates donating developer hours to a shared protocol versus proprietary features.

## Setup and Execution

1.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
2.  **Start Ollama:** Ensure the Ollama background service is running and the target model is pulled to your local machine.
    ```bash
    ollama run <model_name>
    ```
    By default :
    ```bash
    ollama run qwen2.5:7b
    ```
    > **NOTE ON CUSTOM LLM MODELS :**
    > By default, the simulator uses the `qwen2.5:7b` model via Ollama. If you are using a different model (e.g., `llama3`, `mistral`, or `phi3`), you **must** update the model parameter in the Python scripts. Search the code for `model="qwen2.5:7b"` (located in the `agent_decision` and `evolve_directive` functions) and replace it with your downloaded model's exact name before running the simulation.
3.  **Launch the Dashboard:** Run the main application file from your terminal.
    ```bash
    streamlit run app.py
    ```
4.  **Clear History (Optional):** To reset an agent's evolutionary progress and force them back to their asymmetric seeds, delete the auto-generated `directive_*.txt` files in the working directory before launching a new tournament.
