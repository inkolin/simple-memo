"""Terminal color helpers (no dependencies)."""

RED = "\033[91m"
YELLOW = "\033[93m"
GREEN = "\033[92m"
CYAN = "\033[96m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"


def red(text: str) -> str:
    return f"{RED}{text}{RESET}"


def yellow(text: str) -> str:
    return f"{YELLOW}{text}{RESET}"


def green(text: str) -> str:
    return f"{GREEN}{text}{RESET}"


def cyan(text: str) -> str:
    return f"{CYAN}{text}{RESET}"


def bold(text: str) -> str:
    return f"{BOLD}{text}{RESET}"


def dim(text: str) -> str:
    return f"{DIM}{text}{RESET}"
