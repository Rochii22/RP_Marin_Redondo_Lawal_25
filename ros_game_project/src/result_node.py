#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import rospy
from std_msgs.msg import Int64
from ros_game_project_msgs.msg import user_msg
from ros_game_project.srv import GetUserScore, GetUserScoreRequest

class ResultNode():
    def __init__(self):
        rospy.init_node("RESULT_NODE")
        rospy.loginfo("Result node started!")
        self.__sub_re = rospy.Subscriber("result_information", Int64, self.score_callback)
        self.__sub_us = rospy.Subscriber ("user_information", user_msg, self.user_callback)
        self.username = None
    
    def user_callback(self, msg):
        self.username = msg.username

    def score_callback(self, msg):
        score = msg.data
        rospy.loginfo("New results---------------")
        rospy.loginfo(f"   > Username: {self.username}")
        rospy.loginfo(f"   > Score: {score}")

        rospy.wait_for_service('user_score')
        
        # 2. Crear el handle (proxy) del servicio
        self.get_score_service = rospy.ServiceProxy('user_score', GetUserScore)
        rospy.loginfo(f"Service client initialized.")

        user = rospy.get_param('/user_name')
        request = GetUserScoreRequest(username=user)                
        response = self.get_score_service(request) 
                
        rospy.loginfo("--- Service Call Result ---")
        rospy.loginfo(f"  > Percentage Score obtained: {response.score}%")

    
    def start(self):
        rospy.spin()

if __name__ == "__main__":
    try:
        node = ResultNode()
        node.start()
    except rospy.ROSInterruptException:
        pass
