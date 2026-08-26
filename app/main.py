from agent.agent import ask_agent
from services.usage_tracker import get_usage_summary


def print_usage():

    usage = get_usage_summary()

    print("\n========== PersonalOps Usage ==========")
    print(f"API calls:         {usage['requests']}")
    print(f"Input tokens:      {usage['input_tokens']:,}")
    print(f"Output tokens:     {usage['output_tokens']:,}")
    print(f"Thought tokens:    {usage['thought_tokens']:,}")
    print(f"Total tokens:      {usage['total_tokens']:,}")
    print()
    print(f"Estimated cost:    ${usage['estimated_cost']:.6f}")
    print(f"Remaining budget:  ${usage['remaining_budget']:.6f}")
    print("=======================================\n")


def main():
    print("================================")
    print("        PersonalOps v0.2")
    print("================================")
    print("Type 'exit' to quit.")
    print("Type '/usage' to view API usage.\n")

    while True:
        user_input = input("You: ")

        if user_input.lower() == "exit":
            print("Goodbye!")
            break

        if user_input.lower() == "/usage":
            print_usage()
            continue

        try:
            response = ask_agent(user_input)
            print(f"\nPersonalOps: {response}\n")

        except Exception as error:
            print(f"\nError: {error}\n")


if __name__ == "__main__":
    main()