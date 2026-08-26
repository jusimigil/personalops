def request_confirmation(action_description):
    """
    Ask the user to approve a potentially destructive
    or state-changing action.
    """

    print("\n--------------------------------")
    print("        ACTION REQUIRES APPROVAL")
    print("--------------------------------")
    print(action_description)

    while True:
        response = input("\nApprove this action? (y/n): ").strip().lower()

        if response in ("y", "yes"):
            return True

        if response in ("n", "no"):
            return False

        print("Please enter 'y' or 'n'.")