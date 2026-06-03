"""
main.py

Terminal-based CLI chat loop for the Conga CPQ AI Agent.
Run this file directly to start a conversation:

    python main.py

Type 'exit' or 'quit' to end the session.
Type 'reset' to clear conversation history and start fresh.
Type 'state' to print the current running JSON.
"""

import sys
from pathlib import Path

# Make sure project root is on the path when running directly
sys.path.insert(0, str(Path(__file__).resolve().parent))

from dotenv import load_dotenv
load_dotenv()

from agents.cpq_agent import CPQAgent
from state.running_json import print_state, clear_state
from utils.logger import get_logger

logger = get_logger("main")

BANNER = """
╔══════════════════════════════════════════════════════════════╗
║          Conga CPQ AI Agent — Hackathon Edition              ║
║                  Powered by Azure AI Foundry                 ║
╠══════════════════════════════════════════════════════════════╣
║  Commands:                                                   ║
║    exit / quit  — End the session                            ║
║    reset        — Clear conversation history                 ║
║    state        — Print current running JSON                 ║
╚══════════════════════════════════════════════════════════════╝
"""

COMMANDS = {
    "exit": None,
    "quit": None,
    "reset": None,
    "state": None,
}


def run_cli():
    print(BANNER)
    logger.info("cli_session_started")

    agent = CPQAgent()

    while True:
        try:
            user_input = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n\nSession ended. Goodbye!")
            logger.info("cli_session_ended", reason="keyboard_interrupt")
            break

        if not user_input:
            continue

        # ── Built-in commands ─────────────────────────────────────────────────
        lower = user_input.lower()

        if lower in ("exit", "quit"):
            print("Goodbye!")
            logger.info("cli_session_ended", reason="user_exit")
            break

        if lower == "reset":
            agent.reset()
            clear_state()
            print("✅  Conversation history and running JSON cleared.\n")
            continue

        if lower == "state":
            print_state()
            continue

        # ── Agent turn ────────────────────────────────────────────────────────
        print()  # blank line before agent response
        try:
            response = agent.chat(user_input)
            print(f"Agent: {response}\n")
        except Exception as err:
            logger.error("agent_error", error=str(err))
            print(f"⚠️  Error: {err}\n")


if __name__ == "__main__":
    print("Started with main.py")
    run_cli()
