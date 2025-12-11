#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import rospy
from std_msgs.msg import String
import sys
import select
import termios
import tty

class ControlNode(object):
    def __init__(self):
        rospy.init_node("CONTROL_NODE")
        rospy.loginfo("Control node started! Use WASD to move.")
        
        self.pub = rospy.Publisher("keyboard_control", String, queue_size=10)

        self.settings = termios.tcgetattr(sys.stdin)

    def get_key(self):
        try:
            tty.setraw(sys.stdin.fileno())
            rlist, _, _ = select.select([sys.stdin], [], [], 0.1)
            if rlist:
                key = sys.stdin.read(1)
            else:
                key = ''
        finally:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.settings)
        return key

    def start(self):
        key_mapping = {
            'w': 'UP',
            's': 'DOWN',
            'a': 'LEFT',
            'd': 'RIGHT',
            ' ': 'SPACE',  
            'r': 'RESET',
            'f': 'FULL',
            '\x1b': 'ESC', 
            'q': 'QUIT'    # Quit game if control node closed
        }

        rospy.loginfo("---------------------------")
        rospy.loginfo("CONTROLS:")
        rospy.loginfo(" W/A/S/D : Move")
        rospy.loginfo(" SPACE : Start / Pause")
        rospy.loginfo(" R       : Reset")
        rospy.loginfo(" ESC     : Menu / Exit")
        rospy.loginfo(" Q       : Close control node")
        rospy.loginfo("---------------------------")

        while not rospy.is_shutdown():
            key = self.get_key()
            
            if key == '\x03': # Ctrl + C
                break
            
            if key.lower() in key_mapping:
                command_str = key_mapping[key.lower()]
                self.pub.publish(command_str)

                if command_str == 'QUIT': 
                    rospy.loginfo("Closing control...")
                    break

if __name__ == "__main__":
    try:
        node = ControlNode()
        node.start()
    except rospy.ROSInterruptException:
        pass
    except Exception as e:
        print(f"Error: {e}")