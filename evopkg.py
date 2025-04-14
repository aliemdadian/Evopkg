#!/usr/bin/env python3
# Signature for Evopkg package manager
import subprocess
import sys
import os
import shutil
import stat
import json
import time  # For progress bar delay
import threading  # For output locking
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from functools import lru_cache

# Path to store color settings
COLORS_FILE = os.path.expanduser("~/.evopkg_colors.conf")

# Lock for managing output in multi-threaded environment
output_lock = threading.Lock()

# ANSI color definitions
COLORS = {
    "normal": "\033[0;37m",     # White for normal text and table borders
    "info": "\033[1;32m",       # Bright green for informational text
    "success": "\033[0;32m",    # Green for success messages
    "error": "\033[0;31m",      # Red for errors
    "package": "\033[1;32m",    # Bright green for packages and table content
    "warning": "\033[0;33m",    # Yellow for warnings and goodbye messages
    "prompt": "\033[0;34m",     # Blue for prompts
    "header": "\033[0;37m",     # White for headers
    "reset": "\033[0m"          # Reset color
}

# Backup of default colors
DEFAULT_COLORS = COLORS.copy()

# List of reserved names that cannot be used for custom package managers
RESERVED_NAMES = ["pacman", "paru", "yay", "apt", "dnf", "zypper", "snap", "flatpak"]

# Improved progress bar function
def progress_bar(message, repo_name=""):
    bar_length = 20  # Increased length for better visibility
    full_message = f"{message} {repo_name}".strip()
    total_length = 15  # Adjusted padding for alignment

    # Initial message display
    with output_lock:
        sys.stdout.write(f"\r{COLORS['info']}{full_message:<{total_length}}{COLORS['reset']} [{COLORS['normal']}{'-' * bar_length}{COLORS['reset']}]  0%")
        sys.stdout.flush()

    # Progress animation
    step_time = 0.02  # Smooth delay between steps
    for i in range(bar_length + 1):
        percent = (i / bar_length) * 100
        filled = "#" * i
        empty = "-" * (bar_length - i)
        with output_lock:
            sys.stdout.write(f"\r{COLORS['info']}{full_message:<{total_length}}{COLORS['reset']} [{COLORS['package']}{filled}{COLORS['normal']}{empty}{COLORS['reset']}] {percent:3.0f}%")
            sys.stdout.flush()
        time.sleep(step_time)

    # Finalize with newline
    with output_lock:
        sys.stdout.write(f"\r{COLORS['info']}{full_message:<{total_length}}{COLORS['reset']} [{COLORS['package']}{'#' * bar_length}{COLORS['reset']}] 100%\n")
        sys.stdout.flush()

# Load saved colors from file
def load_colors():
    global COLORS
    if os.path.exists(COLORS_FILE):
        try:
            with open(COLORS_FILE, "r") as f:
                saved_colors = json.load(f)
                COLORS.update(saved_colors)
        except (json.JSONDecodeError, IOError):
            pass

# Save colors to file
def save_colors():
    try:
        with open(COLORS_FILE, "w") as f:
            json.dump({k: v for k, v in COLORS.items() if k != "reset"}, f)
    except IOError:
        sys.stdout.write(f"{COLORS['error']}Failed to save colors!{COLORS['reset']}\n")
        sys.stdout.flush()

# Banner for Evopkg
EVOPKG_BANNER = [
    "                                                  ",
    "███████╗██╗   ██╗ ██████╗ ██████╗ ██╗  ██╗ ██████╗",
    "██╔════╝██║   ██║██╔═══██╗██╔══██╗██║ ██╔╝██╔════╝",
    "█████╗  ██║   ██║██║   ██║██████╔╝█████╔╝ ██║  ███╗",
    "██╔══╝  ╚██╗ ██╔╝██║   ██║██╔═══╝ ██╔═██╗ ██║   ██║",
    "███████╗ ╚████╔╝ ╚██████╔╝██║     ██║  ██╗╚██████╔╝",
    "╚══════╝  ╚═══╝   ╚═════╝ ╚═╝     ╚═╝  ╚═╝ ╚═════╝",
    "                                                  "
]

# Color settings menu
def color_menu():
    global COLORS
    while True:
        sys.stdout.write(f"{COLORS['package']}=== Color Settings ==={COLORS['reset']}\n")
        sys.stdout.write(f"{COLORS['package']}1: default{COLORS['reset']}\n")
        sys.stdout.write(f"{COLORS['package']}2: black{COLORS['reset']}\n")
        sys.stdout.write(f"{COLORS['package']}3: dark gray{COLORS['reset']}\n")
        sys.stdout.write(f"{COLORS['package']}4: white{COLORS['reset']}\n")
        sys.stdout.write(f"{COLORS['package']}5: brown{COLORS['reset']}\n")
        sys.stdout.write(f"{COLORS['package']}6: red{COLORS['reset']}\n")
        sys.stdout.write(f"{COLORS['package']}7: orange{COLORS['reset']}\n")
        sys.stdout.write(f"{COLORS['package']}8: yellow{COLORS['reset']}\n")
        sys.stdout.write(f"{COLORS['package']}9: neon green{COLORS['reset']}\n")
        sys.stdout.write(f"{COLORS['package']}10: light green{COLORS['reset']}\n")
        sys.stdout.write(f"{COLORS['package']}11: light blue{COLORS['reset']}\n")
        sys.stdout.write(f"{COLORS['package']}12: dark blue{COLORS['reset']}\n")
        sys.stdout.write(f"{COLORS['package']}13: purple{COLORS['reset']}\n")
        sys.stdout.write(f"{COLORS['package']}14: pink{COLORS['reset']}\n")
        sys.stdout.write(f"{COLORS['package']}15: exit{COLORS['reset']}\n")
        sys.stdout.flush()

        try:
            choice = input(f"{COLORS['prompt']}Choose (1-15): {COLORS['reset']}").strip()
            if choice == "1":
                COLORS.update(DEFAULT_COLORS.copy())
                save_colors()
                progress_bar("Applying color settings")
                sys.stdout.write(f"{COLORS['success']}Switched to default program colors{COLORS['reset']}\n")
            elif choice == "2":
                for key in COLORS:
                    if key != "reset":
                        COLORS[key] = "\033[0;30m"  # Black
                save_colors()
                progress_bar("Applying color settings")
                sys.stdout.write(f"{COLORS['success']}All program colors set to black{COLORS['reset']}\n")
            elif choice == "3":
                for key in COLORS:
                    if key != "reset":
                        COLORS[key] = "\033[0;90m"  # Dark gray
                save_colors()
                progress_bar("Applying color settings")
                sys.stdout.write(f"{COLORS['success']}All program colors set to dark gray{COLORS['reset']}\n")
            elif choice == "4":
                for key in COLORS:
                    if key != "reset":
                        COLORS[key] = "\033[0;37m"  # White
                save_colors()
                progress_bar("Applying color settings")
                sys.stdout.write(f"{COLORS['success']}All program colors set to white{COLORS['reset']}\n")
            elif choice == "5":
                for key in COLORS:
                    if key != "reset":
                        COLORS[key] = "\033[38;5;94m"  # Brown
                save_colors()
                progress_bar("Applying color settings")
                sys.stdout.write(f"{COLORS['success']}All program colors set to brown{COLORS['reset']}\n")
            elif choice == "6":
                for key in COLORS:
                    if key != "reset":
                        COLORS[key] = "\033[0;31m"  # Red
                save_colors()
                progress_bar("Applying color settings")
                sys.stdout.write(f"{COLORS['success']}All program colors set to red{COLORS['reset']}\n")
            elif choice == "7":
                for key in COLORS:
                    if key != "reset":
                        COLORS[key] = "\033[38;5;214m"  # Orange
                save_colors()
                progress_bar("Applying color settings")
                sys.stdout.write(f"{COLORS['success']}All program colors set to orange{COLORS['reset']}\n")
            elif choice == "8":
                for key in COLORS:
                    if key != "reset":
                        COLORS[key] = "\033[0;93m"  # Yellow
                save_colors()
                progress_bar("Applying color settings")
                sys.stdout.write(f"{COLORS['success']}All program colors set to yellow{COLORS['reset']}\n")
            elif choice == "9":
                for key in COLORS:
                    if key != "reset":
                        COLORS[key] = "\033[38;5;46m"  # Neon green
                save_colors()
                progress_bar("Applying color settings")
                sys.stdout.write(f"{COLORS['success']}All program colors set to neon green{COLORS['reset']}\n")
            elif choice == "10":
                for key in COLORS:
                    if key != "reset":
                        COLORS[key] = "\033[1;32m"  # Light green
                save_colors()
                progress_bar("Applying color settings")
                sys.stdout.write(f"{COLORS['success']}All program colors set to light green{COLORS['reset']}\n")
            elif choice == "11":
                for key in COLORS:
                    if key != "reset":
                        COLORS[key] = "\033[1;34m"  # Light blue
                save_colors()
                progress_bar("Applying color settings")
                sys.stdout.write(f"{COLORS['success']}All program colors set to light blue{COLORS['reset']}\n")
            elif choice == "12":
                for key in COLORS:
                    if key != "reset":
                        COLORS[key] = "\033[38;5;27m"  # Dark blue
                save_colors()
                progress_bar("Applying color settings")
                sys.stdout.write(f"{COLORS['success']}All program colors set to dark blue{COLORS['reset']}\n")
            elif choice == "13":
                for key in COLORS:
                    if key != "reset":
                        COLORS[key] = "\033[0;35m"  # Purple
                save_colors()
                progress_bar("Applying color settings")
                sys.stdout.write(f"{COLORS['success']}All program colors set to purple{COLORS['reset']}\n")
            elif choice == "14":
                for key in COLORS:
                    if key != "reset":
                        COLORS[key] = "\033[38;5;206m"  # Pink
                save_colors()
                progress_bar("Applying color settings")
                sys.stdout.write(f"{COLORS['success']}All program colors set to pink{COLORS['reset']}\n")
            elif choice == "15":
                progress_bar("Exiting color menu")
                sys.stdout.write(f"{COLORS['warning']}Exiting color menu{COLORS['reset']}\n")
                sys.stdout.flush()
                break
            else:
                sys.stdout.write(f"{COLORS['warning']}Invalid option! Please choose 1-15{COLORS['reset']}\n")
            sys.stdout.flush()
        except KeyboardInterrupt:
            sys.stdout.write(f"\n{COLORS['warning']}Operation canceled by user{COLORS['reset']}\n")
            sys.stdout.flush()
            break

# Check if text is alphanumeric and ASCII
def is_english_alphanumeric(text):
    return all(c.isalnum() and ord(c) < 128 for c in text)

# Detect operating system
def detect_os():
    os_release_path = "/etc/os-release"
    if os.path.exists(os_release_path):
        with open(os_release_path, "r") as f:
            os_info = dict(line.strip().split("=", 1) for line in f if "=" in line)
        os_id = os_info.get("ID", "").strip('"')
        os_like = os_info.get("ID_LIKE", "").strip('"').split()

        if os_id == "arch" or "arch" in os_like or os_id in ["manjaro", "parch", "endeavouros", "garuda", "artix"]:
            return "Arch Linux", "pacman"
        elif os_id == "debian" or "debian" in os_like or os_id in ["ubuntu", "kali", "linuxmint", "pop", "zorin", "deepin", "raspbian"]:
            return "Debian", "apt"
        elif os_id == "fedora" or "fedora" in os_like or os_id in ["centos", "rhel", "rocky", "almalinux"]:
            return "Fedora", "dnf"
        elif os_id in ["opensuse", "opensuse-leap", "opensuse-tumbleweed", "suse"] or "opensuse" in os_like:
            return "openSUSE", "zypper"
    return None, None

# Detect available package managers
def detect_package_managers():
    managers = {}
    distro, _ = detect_os()
    if distro == "Arch Linux":
        managers["pacman"] = True
        if shutil.which("paru"):
            managers["paru"] = True
        if shutil.which("yay"):
            managers["yay"] = True
    if shutil.which("apt") and distro == "Debian":
        managers["apt"] = True
    if shutil.which("dnf") and distro == "Fedora":
        managers["dnf"] = True
    if shutil.which("zypper") and distro == "openSUSE":
        managers["zypper"] = True
    if shutil.which("snap"):
        managers["snap"] = True
    if shutil.which("flatpak") or os.path.exists("/var/lib/flatpak") or os.path.exists(os.path.expanduser("~/.local/share/flatpak")):
        managers["flatpak"] = True
    return managers

# Run a command with output handling and interruption
def run_command(command, suppress_output=False):
    try:
        if suppress_output:
            process = subprocess.Popen(command, env={"TERM": "xterm-256color"}, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        else:
            process = subprocess.Popen(command, env={"TERM": "xterm-256color"}, stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr)
        process.wait()
        return process.returncode == 0
    except subprocess.CalledProcessError:
        if not suppress_output:
            sys.stdout.write(f"{COLORS['error']}Error executing command{COLORS['reset']}\n")
            sys.stdout.flush()
        return False
    except KeyboardInterrupt:
        sys.stdout.write(f"\n{COLORS['warning']}Command interrupted by user{COLORS['reset']}\n")
        sys.stdout.flush()
        process.terminate()
        return False

# Check if a package exists with caching
@lru_cache(maxsize=128)
def package_exists(package, pkg_manager):
    search_commands = {
        "pacman": ["pacman", "-Ss"],
        "paru": ["paru", "-Ss"],
        "yay": ["yay", "-Ss"],
        "apt": ["apt", "search"],
        "dnf": ["dnf", "search"],
        "zypper": ["zypper", "search"],
        "snap": ["snap", "find"],
        "flatpak": ["flatpak", "search"]
    }
    command = search_commands.get(pkg_manager, []) + [package]
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=10)
        output = result.stdout.lower()
        if pkg_manager == "flatpak":
            if package.lower() not in output:
                for line in result.stdout.splitlines():
                    if package.lower() in line.lower():
                        flatpak_name = line.split()[0]
                        return flatpak_name
            return package.lower() in output and result.returncode == 0
        return package.lower() in output and result.returncode == 0
    except (subprocess.TimeoutExpired, subprocess.SubprocessError):
        return False

# Check if sudo is required for a command
def requires_sudo(command, pkg_manager):
    sudo_required_commands = {
        "pacman": ["-S", "-R", "-Sy", "-Syu", "-Sc"],
        "paru": [],
        "yay": [],
        "apt": ["install", "remove", "update", "dist-upgrade", "autoremove"],
        "dnf": ["install", "remove", "update", "upgrade", "clean"],
        "zypper": ["install", "remove", "refresh", "update", "clean"],
        "snap": ["snap", "install", "remove"],
        "flatpak": ["install", "uninstall"]
    }
    return command in sudo_required_commands.get(pkg_manager, [])

# Show package dependencies/info
def show_dependencies(package, pkg_manager):
    info_commands = {
        "pacman": ["pacman", "-Qi"],
        "paru": ["paru", "-Qi"],
        "yay": ["yay", "-Qi"],
        "apt": ["apt", "show"],
        "dnf": ["dnf", "info"],
        "zypper": ["zypper", "info"],
        "snap": ["snap", "info"],
        "flatpak": ["flatpak", "info"]
    }
    command = info_commands.get(pkg_manager, []) + [package]
    sys.stdout.write(f"{COLORS['info']}Fetching info for {package} with {pkg_manager}...{COLORS['reset']}\n")
    sys.stdout.flush()
    run_command(command)

def truncate_text(text, max_length=22):
    return text if len(text) <= max_length else text[:19] + "..."

def compare_packages(packages, available_managers):
    comparison_data = {pkg: {} for pkg in packages}
    dep_commands = {
        "pacman": ["pacman", "-Si"],
        "paru": ["paru", "-Si"],
        "yay": ["yay", "-Si"],
        "apt": ["apt", "show"],
        "dnf": ["dnf", "info"],
        "zypper": ["zypper", "info"],
        "snap": ["snap", "info"],
        "flatpak": ["flatpak", "info"]
    }

    progress_bar("Comparing packages across repositories")
    sys.stdout.write(f"{COLORS['info']}Building comparison table...{COLORS['reset']}\n")

    def fetch_package_info(manager, package):
        exists = package_exists(package, manager)
        if not exists:
            comparison_data[package][manager] = {"Error": "Not found"}
            return

        pkg_name = exists if isinstance(exists, str) and manager == "flatpak" else package
        command = dep_commands[manager] + [pkg_name]
        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=15)
            output = result.stdout
            info = {}

            for line in output.splitlines():
                line = line.strip()
                if not line:
                    continue
                if manager == "snap":
                    if line.startswith("name:"):
                        info["Name"] = line.split(":", 1)[-1].strip()
                    elif line.startswith("version:"):
                        info["Version"] = line.split(":", 1)[-1].strip()
                    elif line.startswith("installed:") or line.startswith("size:"):
                        info["Size"] = line.split(":", 1)[-1].strip().split()[0]
                    elif line.startswith("summary:") or line.startswith("description:"):
                        info["Description"] = line.split(":", 1)[-1].strip()
                    elif line.startswith("depends:"):
                        info["Dependencies"] = line.split(":", 1)[-1].strip()
                else:
                    if "Version" in line or "version" in line:
                        info["Version"] = line.split(":", 1)[-1].strip() if ":" in line else line.split()[-1]
                    elif "Size" in line or "Installed-Size" in line:
                        info["Size"] = line.split(":", 1)[-1].strip() if ":" in line else line.split()[-1]
                    elif "Description" in line:
                        info["Description"] = line.split(":", 1)[-1].strip() if ":" in line else " ".join(line.split()[1:])
                    elif "Depends" in line:
                        info["Dependencies"] = line.split(":", 1)[-1].strip() if ":" in line else " ".join(line.split()[1:])

            if not info:
                info["Error"] = "Data unavailable"
            comparison_data[package][manager] = info
        except subprocess.TimeoutExpired:
            comparison_data[package][manager] = {"Error": "Timeout"}

    with ThreadPoolExecutor(max_workers=max(len(available_managers), 4)) as executor:
        for package in packages:
            for manager in available_managers:
                executor.submit(fetch_package_info, manager, package)

    for package in packages:
        sys.stdout.write(f"{COLORS['header']}Package: {package}{COLORS['reset']}\n")

        max_repo_len = max([min(len(manager), 22) for manager in comparison_data[package].keys()] + [len("Repository")])
        max_version_len = max([min(len(info.get("Version", "N/A")), 22) for info in comparison_data[package].values()] + [len("Version")])
        max_size_len = max([min(len(info.get("Size", "N/A")), 22) for info in comparison_data[package].values()] + [len("Size")])
        max_desc_len = max([min(len(info.get("Description", "No description")), 22) for info in comparison_data[package].values()] + [len("Description")])
        max_deps_len = max([min(len(info.get("Dependencies", "None")), 22) for info in comparison_data[package].values()] + [len("Dependencies")])

        SOLID_SEPARATOR = "+" + "-" * (max_repo_len + 2) + "+" + "-" * (max_version_len + 2) + "+" + "-" * (max_size_len + 2) + "+" + "-" * (max_desc_len + 2) + "+" + "-" * (max_deps_len + 2) + "+"
        DASHED_SEPARATOR = SOLID_SEPARATOR.replace("-", "–")
        sys.stdout.write(f"{COLORS['normal']}{SOLID_SEPARATOR}{COLORS['reset']}\n")
        sys.stdout.write(f"{COLORS['header']}| {'Repository':<{max_repo_len}} | {'Version':<{max_version_len}} | {'Size':<{max_size_len}} | {'Description':<{max_desc_len}} | {'Dependencies':<{max_deps_len}} |{COLORS['reset']}\n")
        sys.stdout.write(f"{COLORS['normal']}{SOLID_SEPARATOR}{COLORS['reset']}\n")

        for i, (manager, info) in enumerate(comparison_data[package].items()):
            version = truncate_text(info.get("Version", "N/A"))
            size = truncate_text(info.get("Size", "N/A"))
            desc = truncate_text(info.get("Description", "No description"))
            deps = truncate_text(info.get("Dependencies", "None"))
            sys.stdout.write(f"{COLORS['package']}| {manager:<{max_repo_len}} | {version:<{max_version_len}} | {size:<{max_size_len}} | {desc:<{max_desc_len}} | {deps:<{max_deps_len}} |{COLORS['reset']}\n")

            if i < len(comparison_data[package]) - 1:
                sys.stdout.write(f"{COLORS['normal']}{DASHED_SEPARATOR}{COLORS['reset']}\n")

        sys.stdout.write(f"{COLORS['normal']}{SOLID_SEPARATOR}{COLORS['reset']}\n\n")
    sys.stdout.flush()

# Select repository and package manager
def select_repository(packages, available_managers, install_mode=False):
    valid_options = {}
    flatpak_mismatches = {}
    available_packages = []
    repo_order = list(available_managers.keys())  # Keep the order of repositories as detected

    # Check repositories one by one with progress bar
    for manager in repo_order:
        progress_bar("Checking repository", manager)
        for package in packages:
            result = package_exists(package, manager)
            if manager == "flatpak" and isinstance(result, str) and result != package:
                flatpak_mismatches[package] = result
            elif result is True:
                valid_options[manager] = True
                if install_mode and package not in available_packages:
                    available_packages.append(package)

    if flatpak_mismatches and install_mode:
        sys.stdout.write(f"{COLORS['info']}Note: Flatpak mismatches detected:{COLORS['reset']}\n")
        for pkg, flatpak_name in flatpak_mismatches.items():
            sys.stdout.write(f"{COLORS['info']}- '{pkg}' is available as '{flatpak_name}' in Flatpak.{COLORS['reset']}\n")
        sys.stdout.flush()

    if not valid_options:
        sys.stdout.write(f"{COLORS['warning']}No repositories found for {', '.join(packages)}!{COLORS['reset']}\n")
        sys.stdout.flush()
        return None, []

    # Use the same order as checked for display
    options = [mgr for mgr in repo_order if mgr in valid_options]
    sys.stdout.write(f"{COLORS['package']}Select repository for {', '.join(packages)}:{COLORS['reset']}\n")
    for i, opt in enumerate(options, 1):
        sys.stdout.write(f"{COLORS['package']}{i}: {opt}{COLORS['reset']}\n")
    sys.stdout.write(f"{COLORS['package']}{len(options) + 1}: Exit{COLORS['reset']}\n")
    sys.stdout.flush()

    while True:
        try:
            choice = input(f"{COLORS['prompt']}Enter number (1-{len(options) + 1}): {COLORS['reset']}").strip()
            if choice.isdigit():
                choice_int = int(choice)
                if 1 <= choice_int <= len(options):
                    selected_manager = options[choice_int - 1]
                    progress_bar("Selecting", selected_manager)
                    if install_mode:
                        return selected_manager, available_packages
                    return selected_manager, packages
                elif choice_int == len(options) + 1:
                    return None, []
            else:
                sys.stdout.write(f"{COLORS['warning']}Invalid input, please enter a number{COLORS['reset']}\n")
                sys.stdout.flush()
        except KeyboardInterrupt:
            sys.stdout.write(f"\n{COLORS['warning']}Operation canceled by user{COLORS['reset']}\n")
            sys.stdout.flush()
            return None, []

# Simulate package managers
def simulate_package_manager():
    options = [mgr for mgr in ["dnf", "zypper", "apt", "pacman"] if mgr != detect_os()[1]]

    sys.stdout.write(f"{COLORS['package']}=== Package Manager Simulation ==={COLORS['reset']}\n")
    sys.stdout.write(f"{COLORS['package']}Detected OS: {detect_os()[0]}{COLORS['reset']}\n")
    sys.stdout.write(f"{COLORS['package']}Which package manager would you like to simulate?{COLORS['reset']}\n")
    for i, mgr in enumerate(options, 1):
        sys.stdout.write(f"{COLORS['package']}{i}: {mgr}{COLORS['reset']}\n")
    sys.stdout.write(f"{COLORS['package']}{len(options) + 1}: Install all simulators{COLORS['reset']}\n")
    sys.stdout.write(f"{COLORS['package']}{len(options) + 2}: Exit{COLORS['reset']}\n")
    sys.stdout.flush()

    while True:
        try:
            choice = input(f"{COLORS['prompt']}Choose (1-{len(options) + 2}): {COLORS['reset']}").strip()
            if choice.isdigit():
                choice_int = int(choice)
                if 1 <= choice_int <= len(options):
                    self_install(options[choice_int - 1])
                    progress_bar("Simulating", options[choice_int - 1])
                    sys.stdout.write(f"{COLORS['success']}Now you can use '{options[choice_int - 1]}'!{COLORS['reset']}\n")
                    sys.stdout.flush()
                    break
                elif choice_int == len(options) + 1:
                    for mgr in options:
                        self_install(mgr)
                        progress_bar("Installing simulator", mgr)
                    sys.stdout.write(f"{COLORS['success']}All simulators installed!{COLORS['reset']}\n")
                    sys.stdout.flush()
                    break
                elif choice_int == len(options) + 2:
                    break
            else:
                sys.stdout.write(f"{COLORS['warning']}Please enter a valid number!{COLORS['reset']}\n")
                sys.stdout.flush()
        except KeyboardInterrupt:
            sys.stdout.write(f"\n{COLORS['warning']}Operation canceled by user{COLORS['reset']}\n")
            sys.stdout.flush()
            break

# Interactive menu
def interactive_menu(available_managers):
    sys.stdout.write(f"{COLORS['package']}=== Interactive Package Manager ==={COLORS['reset']}\n")
    sys.stdout.write(f"{COLORS['package']}1: Install a package{COLORS['reset']}\n")
    sys.stdout.write(f"{COLORS['package']}2: Remove a package{COLORS['reset']}\n")
    sys.stdout.write(f"{COLORS['package']}3: Search for a package{COLORS['reset']}\n")
    sys.stdout.write(f"{COLORS['package']}4: Show package dependencies/info{COLORS['reset']}\n")
    sys.stdout.write(f"{COLORS['package']}5: Compare packages across repositories{COLORS['reset']}\n")
    sys.stdout.write(f"{COLORS['package']}6: Exit{COLORS['reset']}\n")
    sys.stdout.flush()

    try:
        choice = input(f"{COLORS['prompt']}Choose (1-6): {COLORS['reset']}").strip()
        if choice == "1":
            packages = input(f"{COLORS['prompt']}Enter package names (space-separated): {COLORS['reset']}").strip().split()
            if not packages:
                sys.stdout.write(f"{COLORS['warning']}No packages specified!{COLORS['reset']}\n")
                sys.stdout.flush()
                return
            handle_install(packages, available_managers)

        elif choice == "2":
            packages = input(f"{COLORS['prompt']}Enter package names to remove: {COLORS['reset']}").strip().split()
            if not packages:
                sys.stdout.write(f"{COLORS['warning']}No packages specified!{COLORS['reset']}\n")
                sys.stdout.flush()
                return
            chosen_manager, available_packages = select_repository(packages, available_managers)
            if chosen_manager and available_packages:
                command = command_mappings[chosen_manager]["-R"] + available_packages
                if requires_sudo("-R", chosen_manager):
                    command = ["sudo"] + command
                sys.stdout.write(f"{COLORS['success']}Removing with {chosen_manager}...{COLORS['reset']}\n")
                sys.stdout.flush()
                run_command(command)

        elif choice == "3":
            search_term = input(f"{COLORS['prompt']}Enter search term: {COLORS['reset']}").strip()
            if not search_term:
                sys.stdout.write(f"{COLORS['warning']}No search term specified!{COLORS['reset']}\n")
                sys.stdout.flush()
                return
            chosen_manager, _ = select_repository([search_term], available_managers)
            if chosen_manager:
                sys.stdout.write(f"{COLORS['success']}Searching with {chosen_manager}...{COLORS['reset']}\n")
                sys.stdout.flush()
                run_command(command_mappings[chosen_manager]["-Ss"] + [search_term])

        elif choice == "4":
            package = input(f"{COLORS['prompt']}Enter package name: {COLORS['reset']}").strip()
            if not package:
                sys.stdout.write(f"{COLORS['warning']}No package specified!{COLORS['reset']}\n")
                sys.stdout.flush()
                return
            chosen_manager, _ = select_repository([package], available_managers)
            if chosen_manager:
                show_dependencies(package, chosen_manager)

        elif choice == "5":
            packages = input(f"{COLORS['prompt']}Enter package names to compare (space-separated): {COLORS['reset']}").strip().split()
            if not packages:
                sys.stdout.write(f"{COLORS['warning']}No packages specified!{COLORS['reset']}\n")
                sys.stdout.flush()
                return
            compare_packages(packages, available_managers)

        elif choice == "6":
            progress_bar("Exiting")
            sys.stdout.write(f"{COLORS['warning']}Goodbye!{COLORS['reset']}\n")
            sys.stdout.flush()
            sys.exit(0)
        else:
            sys.stdout.write(f"{COLORS['warning']}Invalid option!{COLORS['reset']}\n")
            sys.stdout.flush()
    except KeyboardInterrupt:
        sys.stdout.write(f"\n{COLORS['warning']}Operation canceled by user{COLORS['reset']}\n")
        sys.stdout.flush()
        sys.exit(0)

# Handle package installation
def handle_install(packages, available_managers):
    remaining_packages = packages.copy()

    while remaining_packages:
        chosen_manager, available_packages = select_repository(remaining_packages, available_managers, install_mode=True)
        if not chosen_manager or not available_packages:
            sys.stdout.write(f"{COLORS['warning']}Installation aborted.{COLORS['reset']}\n")
            sys.stdout.flush()
            break

        existing_packages = [pkg for pkg in available_packages if package_exists(pkg, chosen_manager)]
        if existing_packages:
            for package in existing_packages:
                show_dependencies(package, chosen_manager)
            command = command_mappings[chosen_manager]["-S"] + existing_packages
            if requires_sudo("-S", chosen_manager):
                command = ["sudo"] + command
            sys.stdout.write(f"{COLORS['success']}Installing {', '.join(existing_packages)} with {chosen_manager}...{COLORS['reset']}\n")
            sys.stdout.flush()
            run_command(command)

        remaining_packages = [pkg for pkg in remaining_packages if not package_exists(pkg, chosen_manager)]
        if remaining_packages:
            sys.stdout.write(f"{COLORS['warning']}The following packages were not found in {chosen_manager}: {', '.join(remaining_packages)}{COLORS['reset']}\n")
            sys.stdout.write(f"{COLORS['warning']}Please select another repository for the remaining packages.{COLORS['reset']}\n")
            sys.stdout.flush()

# Removal menu
def removal_menu():
    bin_dir = "/usr/local/bin"
    default_managers = ["dnf", "zypper", "apt", "pacman", "evopkg"]
    installed_managers = []
    signature = "# EVOPKG_SIGNATURE_EVOPM"

    for item in os.listdir(bin_dir):
        item_path = os.path.join(bin_dir, item)
        if os.path.isfile(item_path) and os.access(item_path, os.X_OK):
            try:
                with open(item_path, 'r') as f:
                    if signature in f.read() and item != "evopkg":
                        installed_managers.append(item)
            except (IOError, PermissionError):
                continue

    if not installed_managers:
        sys.stdout.write(f"{COLORS['error']}No Evopkg-installed package managers found (excluding evopkg itself)!{COLORS['reset']}\n")
        sys.stdout.flush()
        return

    sys.stdout.write(f"{COLORS['error']}=== Remove Installed Package Managers ==={COLORS['reset']}\n")
    for i, mgr in enumerate(installed_managers, 1):
        sys.stdout.write(f"{COLORS['error']}{i}: {mgr}{COLORS['reset']}\n")
    sys.stdout.write(f"{COLORS['error']}{len(installed_managers) + 1}: Remove all{COLORS['reset']}\n")
    sys.stdout.write(f"{COLORS['error']}{len(installed_managers) + 2}: Exit{COLORS['reset']}\n")
    sys.stdout.flush()

    while True:
        try:
            choice = input(f"{COLORS['prompt']}Choose (1-{len(installed_managers) + 2}): {COLORS['reset']}").strip()
            if choice.isdigit():
                choice_int = int(choice)
                if 1 <= choice_int <= len(installed_managers):
                    mgr = installed_managers[choice_int - 1]
                    target_path = os.path.join(bin_dir, mgr)
                    progress_bar("Removing", mgr)
                    try:
                        os.remove(target_path)
                    except PermissionError:
                        run_command(["sudo", "rm", target_path], suppress_output=True)
                    sys.stdout.write(f"{COLORS['success']}Removed {mgr}{COLORS['reset']}\n")
                    sys.stdout.flush()
                    break
                elif choice_int == len(installed_managers) + 1:
                    for mgr in installed_managers:
                        target_path = os.path.join(bin_dir, mgr)
                        progress_bar("Removing", mgr)
                        try:
                            os.remove(target_path)
                        except PermissionError:
                            run_command(["sudo", "rm", target_path], suppress_output=True)
                    sys.stdout.write(f"{COLORS['success']}All Evopkg-installed managers removed (excluding evopkg itself){COLORS['reset']}\n")
                    sys.stdout.flush()
                    break
                elif choice_int == len(installed_managers) + 2:
                    progress_bar("Exiting removal menu")
                    sys.stdout.write(f"{COLORS['warning']}Exiting removal menu{COLORS['reset']}\n")
                    sys.stdout.flush()
                    break
            else:
                sys.stdout.write(f"{COLORS['warning']}Please enter a valid number!{COLORS['reset']}\n")
                sys.stdout.flush()
        except KeyboardInterrupt:
            sys.stdout.write(f"\n{COLORS['warning']}Operation canceled by user{COLORS['reset']}\n")
            sys.stdout.flush()
            break

# Self-install function
def self_install(name):
    script_path = os.path.realpath(__file__)
    target_path = f"/usr/local/bin/{name}"
    if not os.path.exists(target_path):
        sys.stdout.write(f"{COLORS['success']}Installing {name}...{COLORS['reset']}\n")
        sys.stdout.flush()
        progress_bar("Installing", name)
        try:
            shutil.copyfile(script_path, target_path)
        except PermissionError:
            if run_command(["sudo", "cp", script_path, target_path], suppress_output=True):
                sys.stdout.write(f"{COLORS['success']}Installed with sudo{COLORS['reset']}\n")
            else:
                sys.stdout.write(f"{COLORS['error']}Failed to install {name}. Run with sudo.{COLORS['reset']}\n")
                sys.exit(1)

        if run_command(["chmod", "755", target_path], suppress_output=True) or run_command(["sudo", "chmod", "755", target_path], suppress_output=True):
            progress_bar("Setting up", name)
            sys.stdout.write(f"{COLORS['success']}Installed! Use '{name}' now.{COLORS['reset']}\n")
        else:
            sys.stdout.write(f"{COLORS['error']}Failed to set permissions.{COLORS['reset']}\n")
            sys.exit(1)

# Command mappings for package managers
command_mappings = {
    "pacman": {"-S": ["pacman", "-S"], "-R": ["pacman", "-R"], "-Sy": ["pacman", "-Sy"], "-Syu": ["pacman", "-Syu"], "-Sc": ["pacman", "-Sc"], "-Q": ["pacman", "-Q"], "-Qs": ["pacman", "-Qs"], "-Ss": ["pacman", "-Ss"], "-Qi": ["pacman", "-Qi"], "-Ql": ["pacman", "-Ql"]},
    "paru": {"-S": ["paru", "-S"], "-R": ["paru", "-R"], "-Sy": ["paru", "-Sy"], "-Syu": ["paru", "-Syu"], "-Sc": ["paru", "-Sc"], "-Q": ["paru", "-Q"], "-Qs": ["paru", "-Qs"], "-Ss": ["paru", "-Ss"], "-Qi": ["paru", "-Qi"], "-Ql": ["paru", "-Ql"]},
    "yay": {"-S": ["yay", "-S"], "-R": ["yay", "-R"], "-Sy": ["yay", "-Sy"], "-Syu": ["yay", "-Syu"], "-Sc": ["yay", "-Sc"], "-Q": ["yay", "-Q"], "-Qs": ["yay", "-Qs"], "-Ss": ["yay", "-Ss"], "-Qi": ["yay", "-Qi"], "-Ql": ["yay", "-Ql"]},
    "apt": {"-S": ["apt", "install"], "-R": ["apt", "remove"], "-Sy": ["apt", "update"], "-Syu": ["apt", "dist-upgrade"], "-Sc": ["apt", "autoremove"], "-Q": ["dpkg", "-l"], "-Qs": ["dpkg-query", "-l"], "-Ss": ["apt", "search"], "-Qi": ["apt", "show"], "-Ql": ["dpkg", "-L"]},
    "dnf": {"-S": ["dnf", "install"], "-R": ["dnf", "remove"], "-Sy": ["dnf", "update"], "-Syu": ["dnf", "upgrade"], "-Sc": ["dnf", "clean", "all"], "-Q": ["dnf", "list", "installed"], "-Qs": ["dnf", "list", "installed"], "-Ss": ["dnf", "search"], "-Qi": ["dnf", "info"], "-Ql": ["rpm", "-ql"]},
    "zypper": {"-S": ["zypper", "install"], "-R": ["zypper", "remove"], "-Sy": ["zypper", "refresh"], "-Syu": ["zypper", "update"], "-Sc": ["zypper", "clean"], "-Q": ["zypper", "se", "-i"], "-Qs": ["zypper", "se", "-i"], "-Ss": ["zypper", "search"], "-Qi": ["zypper", "info"], "-Ql": ["rpm", "-ql"]},
    "snap": {"-S": ["snap", "install"], "-R": ["snap", "remove"], "-Sy": ["snap", "refresh"], "-Syu": ["snap", "refresh"], "-Sc": ["snap", "remove", "--purge"], "-Q": ["snap", "list"], "-Qs": ["snap", "list"], "-Ss": ["snap", "find"], "-Qi": ["snap", "info"]},
    "flatpak": {"-S": ["flatpak", "install"], "-R": ["flatpak", "uninstall"], "-Sy": ["flatpak", "update"], "-Syu": ["flatpak", "update"], "-Sc": ["flatpak", "uninstall", "--unused"], "-Q": ["flatpak", "list"], "-Qs": ["flatpak", "list"], "-Ss": ["flatpak", "search"], "-Qi": ["flatpak", "info"]}
}

# Main menu
def main_menu():
    for line in EVOPKG_BANNER:
        sys.stdout.write(f"{COLORS['package']}{line}{COLORS['reset']}\n")
    sys.stdout.write(f"\n{COLORS['package']}=== Welcome to Evopkg ==={COLORS['reset']}\n")
    sys.stdout.write(f"{COLORS['package']}1: Simulate package managers{COLORS['reset']}\n")
    sys.stdout.write(f"{COLORS['package']}2: Create a custom package manager{COLORS['reset']}\n")
    sys.stdout.write(f"{COLORS['package']}3: Exit{COLORS['reset']}\n")
    sys.stdout.flush()

    while True:
        try:
            choice = input(f"{COLORS['prompt']}Choose (1-3): {COLORS['reset']}").strip()
            if choice == "1":
                simulate_package_manager()
                break
            elif choice == "2":
                custom_install()
                break
            elif choice == "3":
                progress_bar("Exiting")
                sys.stdout.write(f"{COLORS['warning']}Goodbye!{COLORS['reset']}\n")
                sys.stdout.flush()
                sys.exit(0)
            else:
                sys.stdout.write(f"{COLORS['warning']}Invalid option!{COLORS['reset']}\n")
                sys.stdout.flush()
        except KeyboardInterrupt:
            sys.stdout.write(f"\n{COLORS['warning']}Operation canceled by user{COLORS['reset']}\n")
            sys.stdout.flush()
            sys.exit(0)

# Custom installation with reserved name check
def custom_install():
    sys.stdout.write(f"{COLORS['package']}Detected OS: {detect_os()[0]}{COLORS['reset']}\n")
    sys.stdout.flush()
    try:
        while True:
            custom_name = input(f"{COLORS['prompt']}Enter custom command name (e.g., 'mypkg'): {COLORS['reset']}").strip()

            # Check if the name is reserved
            if custom_name.lower() in [name.lower() for name in RESERVED_NAMES]:
                sys.stdout.write(f"{COLORS['error']}Error: '{custom_name}' is a reserved package manager name. Please choose a different name.{COLORS['reset']}\n")
                sys.stdout.flush()
                continue

            # Check if the name is alphanumeric and ASCII
            if not custom_name or is_english_alphanumeric(custom_name):
                break
            sys.stdout.write(f"{COLORS['warning']}Use only English letters and numbers{COLORS['reset']}\n")
            sys.stdout.flush()

        if custom_name:
            self_install(custom_name)
    except KeyboardInterrupt:
        sys.stdout.write(f"\n{COLORS['warning']}Installation canceled by user{COLORS['reset']}\n")
        sys.stdout.flush()
        sys.exit(0)

# Main logic
def main():
    global COLORS
    load_colors()
    script_name = os.path.basename(sys.argv[0])
    distro, pkg_manager = detect_os()
    available_managers = detect_package_managers()

    if not distro:
        sys.stdout.write(f"{COLORS['error']}Unsupported OS!{COLORS['reset']}\n")
        sys.stdout.flush()
        sys.exit(1)

    evopkg_path = "/usr/local/bin/evopkg"
    if not os.path.exists(evopkg_path):
        self_install("evopkg")

    running_with_python = script_name.startswith("python3") or script_name.endswith(".py")
    simulated_manager = script_name if script_name in ["dnf", "zypper", "apt", "pacman"] else None
    custom_manager = script_name if script_name not in ["dnf", "zypper", "apt", "pacman", "python3"] and not script_name.endswith(".py") else None

    if len(sys.argv) == 1:
        if script_name == "evopkg" or custom_manager:
            interactive_menu(available_managers)
        elif running_with_python:
            main_menu()
        else:
            interactive_menu(available_managers)
    else:
        command = sys.argv[1]
        args = sys.argv[2:] if len(sys.argv) > 2 else []

        if command == "-r" and script_name == "evopkg":
            removal_menu()
            sys.exit(0)
        elif command == "-m" and script_name == "evopkg":
            main_menu()
            sys.exit(0)
        elif command == "-c" and script_name == "evopkg":
            color_menu()
            sys.exit(0)

        if simulated_manager:
            if command == "install":
                command = "-S"
            elif command == "remove":
                command = "-R"
            elif command == "update":
                command = "-Sy"
            elif command == "upgrade":
                command = "-Syu"
            elif command == "clean":
                command = "-Sc"
            elif command == "list":
                command = "-Q"
            elif command == "search":
                command = "-Ss"
            elif command == "info":
                command = "-Qi"

        if command in command_mappings[pkg_manager]:
            chosen_manager = pkg_manager
            if (simulated_manager or custom_manager or script_name == "evopkg") and args:
                if command == "-S":
                    handle_install(args, available_managers)
                elif command in ["-R", "-Ss", "-Qi"]:
                    chosen_manager, available_packages = select_repository(args, available_managers)
                    if not chosen_manager:
                        sys.stdout.write(f"{COLORS['warning']}No repository selected.{COLORS['reset']}\n")
                        sys.stdout.flush()
                        sys.exit(1)
                    if command == "-R":
                        cmd = command_mappings[chosen_manager]["-R"] + available_packages
                        if requires_sudo("-R", chosen_manager):
                            cmd = ["sudo"] + cmd
                        sys.stdout.write(f"{COLORS['success']}Removing with {chosen_manager}...{COLORS['reset']}\n")
                        sys.stdout.flush()
                        run_command(cmd)
                    elif command == "-Ss":
                        cmd = command_mappings[chosen_manager]["-Ss"] + args
                        sys.stdout.write(f"{COLORS['success']}Searching with {chosen_manager}...{COLORS['reset']}\n")
                        sys.stdout.flush()
                        run_command(cmd)
                    elif command == "-Qi":
                        for package in args:
                            show_dependencies(package, chosen_manager)
                else:
                    cmd = command_mappings[chosen_manager][command] + args
                    if requires_sudo(command, chosen_manager):
                        cmd = ["sudo"] + cmd
                    sys.stdout.write(f"{COLORS['success']}Executing with {chosen_manager}...{COLORS['reset']}\n")
                    sys.stdout.flush()
                    run_command(cmd)
            else:
                cmd = command_mappings[chosen_manager][command] + args
                if requires_sudo(command, chosen_manager):
                    cmd = ["sudo"] + cmd
                sys.stdout.write(f"{COLORS['success']}Executing with {chosen_manager}...{COLORS['reset']}\n")
                sys.stdout.flush()
                run_command(cmd)
        else:
            sys.stdout.write(f"{COLORS['error']}Unknown command '{command}'!{COLORS['reset']}\n")
            sys.stdout.flush()
            sys.exit(1)

if __name__ == "__main__":
    main()
