# Infinite Crossy Road - ROS Project

This project is a distributed implementation of the classic "Crossy Road" game using **ROS (Robot Operating System)**. The game logic, user input, visual rendering, and scoring are separated into independent nodes that communicate asynchronously via Topics and synchronously via Services.

## Table of Contents
1. Dependencies & Installation
2. System Architecture (Topics, Services, Parameters)
3. How to Run
4. Global Shutdown Command
5. Node Descriptions

---

## 1. Dependencies & Installation

To run this project, you need a working installation of ROS (Noetic recommended for Python 3) and the necessary Python libraries.

### 1. System Requirements
* Ubuntu 20.04 (or compatible)
* ROS Noetic
* Python 3

### 2. Install Python Dependencies
The game node uses 'pygame' for graphics and audio rendering. Install it using pip:
```bash 
pip3 install pygame
```
Note on the Control Node: The control_node.py uses low-level libraries (termios, tty) for keyboard input capture. In some environments, it may require the control_node to be run in a dedicated terminal like gnome-terminal to function correctly. If you experience keyboard input issues, ensure it is installed:

```bash
sudo apt install gnome-terminal 
```

### 3. ROS Workspace Configuration
Ensure your custom message package (ros_game_project_msgs) and the game package (ros_game_project) are inside your Catkin workspace source folder (~/catkin_ws/src/).

Navigate to your workspace:

```bash
cd ~/catkin_ws
```

Build the packages:

```bash
catkin_make
```

Source environment
```bash
source devel/setup.bash
```

Execution permissions:

```bash
chmod +x src/ros_game_project/*.py
```

## 2. System Architecture (Topics, Services, Parameters)
The system consists of 4 nodes communicating via ROS Topics and Services.

### Topics Used:
#### __user_information__ 
    (Type: ros_game_project_msgs/user_msg): Contains Name, Username, and Age.

#### __keyboard_control__ 
    (Type: std_msgs/String): Contains movement and control commands (UP, DOWN, LEFT, RIGHT, FULL, ESC, RESET, END).

#### __result_information__ 
    (Type: std_msgs/Int64): Contains the final score upon Game Over.

### Services Used:
#### __difficulty (SetGameDifficulty)__:

    Server: game_node.py

    Client: info_user.py

    Function: Allows the user node to set the game difficulty (easy/medium/hard) synchronously in the main node before the game starts.

#### __user_score (GetUserScore)__:

    Server: game_node.py

    Client: result_node.py (Optional)

    Function: Allows other nodes to query the current player's score from the game_node.

### ROS Parameters:
The game_node uses parameters defined in the game_launcher.launch file for runtime configuration, such as:

* __/game_node/user_name:__ Store the current user's username.

* __/game_node/change_player_color:__ Toggles a feature related to the player's appearance.

* __/game_node/screen_param:__ Variable to know which state the game is currently at (phase1, phase2 or phase3).

## 3. How to Run
The entire system is started using a single roslaunch file, which manages all nodes and dependencies correctly.

__Terminal: Start the entire system__

Ensure your environment is sourced (source devel/setup.bash) and execute:

```bash
roslaunch ros_game_project game_launcher.launch
```

This command starts the ROS Master and the four nodes (game_node is marked as required).

__Initial Interaction__

The INFO_USER node (info_user.py) will immediately prompt for your Name, Username, Age, and Difficulty level. You must provide this data for the game to start.

### Game Control

Once the game starts, focus on the CONTROL_NODE terminal and use W/A/S/D to move the character in the Pygame window.

## 4. Node Descriptions
#### __info_user.py (INFO_USER):__

    Role: User Interface and Initialization.

    Function: Prompts the user for personal details and difficulty level. It publishes the user data via Topic and then calls the difficulty Service to configure the game before exiting its execution.

#### __control_node.py (CONTROL_NODE):__

    Role: Input Driver and System Commander.

    Function: Reads raw keystrokes (W/A/S/D, R, Q/END) and maps them to String commands, publishing them to the keyboard_control Topic.

#### __game_node.py (GAME_NODE):__

    Role: Core Logic, Rendering, and Service Server.

    Function: Contains the main Pygame loop (physics, rendering, collisions). It hosts the difficulty and user_score Services and publishes the final score via the result_information Topic. It is a required node for the roslaunch.

#### __result_node.py (RESULT_NODE):__

    Role: Statistics and Reporting.

    Function: Listens to both user_information and result_information Topics. Upon receiving the final score, it prints a detailed report in its terminal with the username and the score obtained. Then, asks the game_node for the percentage of the score and publishes it.