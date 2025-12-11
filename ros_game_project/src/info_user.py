#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import rospy
from ros_game_project_msgs.msg import user_msg
from ros_game_project.srv import SetGameDifficulty, SetGameDifficultyRequest

class UserInfo(object):
    def __init__(self):
        rospy.init_node("INFO_USER")
        rospy.loginfo("Node user_info has started")
        self.__pub = rospy.Publisher("user_information", user_msg, queue_size = 10)

    def start(self):
        rospy.sleep(1) # Ensure GAME_NODE is listening
        rospy.loginfo("Enter the following data----------------")
        while not rospy.is_shutdown():
            try:
                user = user_msg()
                user.name = input("Name: ")
                user.username = input("Username: ")
                user.age = int(input("Age: "))
                self.__pub.publish(user)
                selected_difficulty = input("Difficulty (easy/medium/hard): ")
                break # Only do once

            except ValueError:
                rospy.logerr("Introduce a valid age")
            
        rospy.wait_for_service('difficulty')
        
        self.get_difficulty = rospy.ServiceProxy('difficulty', SetGameDifficulty)
        rospy.loginfo(f"Difficulty Service Client initialized.")

        request = SetGameDifficultyRequest(change_difficulty=selected_difficulty)                
        response = self.get_difficulty(request) 
                
        rospy.loginfo("--- Service Call Result ---")
        rospy.loginfo(f"  > Difficulty changed: {response.success}")

if __name__ == '__main__':
    try:
        node = UserInfo()
        node.start()
    except rospy.ROSInterruptException:
        pass