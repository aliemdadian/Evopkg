## Evopkg - Universal Package Manager Simulator
Evopkg is a Python-based tool designed to simulate and unify package management across various Linux distributions. It is not a full-fledged package manager but a simulator that enhances user experience by providing a consistent interface for interacting with native package managers like pacman, apt, dnf, zypper, snap, and flatpak. With features like color customization, progress bars, and package comparison, Evopkg aims to simplify package management for users across different systems.

## Features
### Cross-Distro Compatibility: 
Automatically detects the operating system (Arch Linux, Debian, Fedora, openSUSE, and derivatives) and available package managers (pacman, paru, yay, apt, dnf, zypper, snap, flatpak).
### Package Manager Simulation: 
Simulate other package managers (e.g., use dnf on Arch or apt on Fedora) by installing custom command aliases.
### Custom Command Creation: 
Create your own package manager command (e.g., mypkg) with reserved name protection.
### Interactive Menu: 
User-friendly menu for installing, removing, searching, and comparing packages.
### Package Installation: 
Install packages with repository selection and dependency display.
### Package Removal:
Remove packages or uninstall simulated package managers.
### Package Search: 
Search for packages across detected repositories.
### Dependency Info:
Display detailed package information and dependencies.
### Package Comparison: 
Compare packages across multiple repositories in a formatted table (version, size, description, dependencies).
### Color Customization: 
Extensive color settings with 14 options (default, black, white, neon green, etc.) saved to ~/.evopkg_colors.conf.
### Progress Bar: 
Smooth, animated progress bars for operations like installation, removal, and repository checks.
### Threaded Operations:
Multi-threaded package info fetching for faster comparisons.
### Error Handling:
Robust handling of interrupts (Ctrl+C), permissions, and timeouts.
### ASCII Banner: 
Stylish Evopkg banner on startup.
### Flatpak Support:
Handles Flatpak package name mismatches gracefully.
### Sudo Detection:
Automatically prepends sudo for commands requiring elevated privileges.
### Caching:
Uses @lru_cache to speed up repeated package existence checks.
### Output Synchronization:
Thread-safe output with threading.Lock for clean console display.

## Installation
### Prerequisites
Python 3.x
A supported Linux distribution (Arch, Debian, Fedora, openSUSE, or derivatives)
At least one package manager installed (pacman, apt, dnf, zypper, snap, or flatpak)


## Download the Script:
Save Evopkg.py to any directory on your system (e.g., ~/Downloads).
Run the Script:

```bash
sudo python3 evopkg.py
```
## Usage
### Running Evopkg
Interactive Mode: Run without arguments for the main menu:

```bash
evopkg
```
## Command-Line Mode: Use with arguments to simulate package manager commands

```bash
evopkg -S package1 package2  # Install packages
evopkg -R package1          # Remove packages
evopkg -Ss search_term      # Search for packages
```
## Main Menu Options
1. Simulate Package Managers: Install simulators for dnf, zypper, apt, or pacman.

2. Create Custom Package Manager: Define a custom command (e.g., mypkg).

3. Exit: Quit the program.

## Interactive Menu Options
1. Install a Package: Select a repository and install packages.

2. Remove a Package: Remove specified packages.

3. Search for a Package: Search across repositories.

4. Show Package Dependencies/Info: View package details.

5. Compare Packages: Compare packages across repositories.

6. Exit: Exit the interactive menu.

## Special Commands

### Remove Installed Simulators:
```bash
evopkg -r
```
### Access Main Menu:
```bash
evopkg -m
```
### Customize Colors:
```bash
evopkg -c
```

## Custom Package Manager
### Create a custom command:
```bash
evopkg -m
# Choose option 2, enter a name (e.g., mypkg)
```
Use it like:
```bash
mypkg -S package_name
```
And after creating a custom package manager, you can go to the interactive menu by entering its name in the terminal.
```bash
mypkg
```
Or even perform various operations like installation and removal with a custom package manager.
```bash
mypkg -S package1 package2  # Install packages
mypkg -R package1          # Remove packages
mypkg -Ss search_term      # Search for packages
```
## Simulated Package Managers
### Simulate another package manager:

```bash
evopkg -m
# Choose option 1, select a manager (e.g., dnf)
dnf install package_name
```

## Notes
Single File: Evopkg is a single Python script (evopkg.py).

Reserved Names: Cannot use pacman, paru, yay, apt, dnf, zypper, snap, or flatpak as custom names.

Flatpak Handling: Detects and suggests correct Flatpak package names if mismatches occur.

Thread Safety: Ensures clean output during multi-threaded operations.

On distributions where the default package manager requires sudo access for operations, be sure to enter sudo with the emulator.

## Contributing
Feel free to fork this repository, submit issues, or create pull requests to enhance Evopkg!

## License
This project is licensed under the MIT License - see the  file for details.
