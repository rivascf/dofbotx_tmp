#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
# Importamos la libreria para ActionServer
from rclpy.action import ActionServer
from rclpy.action.server import ServerGoalHandle
# Importamos la libreria personalizada de mensajes (ActionMessage)
from dofbot_interfaces.action import GripperCmd
import uuid
import time

class DofbotSimpleActionSrv(Node):
    def __init__(self, node_name):
        super().__init__(node_name)

        # Crear el ActionServer
        self._action_srv = ActionServer(
            self,
            GripperCmd,
            'gripper_command',
            self.__execute_callback
        )
        self.get_logger().info(f"Dofbot ActionServer {node_name} inicializado.")

    def __validate_range(self, value, min_val, max_val, strict=False):
        if strict:
            if value <= max_val and value >= min_val:
                return False
        else:        
            if value < max_val and value > min_val:
                return False
            
        return True    

    def __execute_callback(self, goal_handle: ServerGoalHandle):
        # Recibimos una nueva meta del tipo GripperCmd.Goal
        goal_id = uuid.UUID(bytes=bytes(goal_handle.goal_id.uuid))
        self.get_logger().info(f"--> Recibimos una nueva GOAL: GOAL_ID({str(goal_id)})")
        # 1. Recuperamos los datos de la meta
        gripper_goal = goal_handle.request
        goal_state =  gripper_goal.gripper_state
        goal_duration = gripper_goal.duration

        # 2. Evaluamos si la meta es vaida
        # Si no cumple con los parámetros se rechaza
        if (self.__validate_range(goal_state, GripperCmd.Goal.OPEN, GripperCmd.Goal.CLOSE)):
            goal_handle.abort()
            self.get_logger().warn(f"--> GOAL_ID({str(goal_id)}) was ABORTED for 'GRIPPER out of range' rule.")
            result = GripperCmd.Result()
            result.success = False
            result.string_status_message = f"ERROR: GRIPPER_STATE {goal_state} debe ser menor a {GripperCmd.Goal.CLOSE} y mayor a {GripperCmd.Goal.OPEN}."
            result.current_state = 0.0
            return result
        if (self.__validate_range(goal_duration, 0.0, 10.0) ):
            goal_handle.abort()
            self.get_logger().warn(f"--> GOAL_ID({str(goal_id)}) was ABORTED for 'DURATION out of range' rule.")
            result = GripperCmd.Result()
            result.success = False
            result.string_status_message = f"ERROR: DURATION {goal_duration} debe ser mayor a {0.0} y menor a {10.0}."
            result.current_state = 0.0
            return result
        # 3. Acondicionamos los datos de execusion
        # en caso de ser necesario
        # --------- Just for this demo -------
        # Si el gripper fuera real entonces se lee el valor actual del gripper
        igripper_state = -0.7045 # Just for fun
        delta = (goal_state - igripper_state) / int(goal_duration)
        start_time = time.time()
        self.get_logger().info(f"--> Executing GOAL_ID({str(goal_id)}).")
        while int(time.time() - start_time) < int(goal_duration):
            feedback_msg = GripperCmd.Feedback()
            feedback_msg.current_state = igripper_state
            igripper_state += delta
            goal_handle.publish_feedback(feedback_msg)
            time.sleep(1.0)

        # 3. Terminamos la ejecusion de manera exitosa
        self.get_logger().info(f"--> Finish GOAL_ID({str(goal_id)}) successfully.")
        goal_handle.succeed()
        result = GripperCmd.Result()
        result.current_state = goal_state
        result.success = True
        result.string_status_message = "Gripper move successfully."
        return result

        
def init_action_srv(args=None):
    rclpy.init(args=args)
    simple_actionserver = DofbotSimpleActionSrv('gripper_action_srv_node')
    try:
        rclpy.spin(simple_actionserver)
    except KeyboardInterrupt:
        simple_actionserver.get_logger().info('Keyboard Interrupt (SIGINT) received. Shutting down...')
    finally:
        # simple_actionserver.destroy_node()
        rclpy.shutdown()

if __name__ == "__main__":
    init_action_srv()