#ifndef __KINEMATICS_DOFBOT_H__
#define __KINEMATICS_DOFBOT_H__

#include <memory>
#include <string>
#include <vector>

#include "rclcpp/rclcpp.hpp"

#include <kdl_parser/kdl_parser.hpp>
#include <kdl/chain.hpp>
#include <kdl/tree.hpp>
#include <kdl/chainfksolverpos_recursive.hpp>
#include <kdl/chainiksolvervel_pinv.hpp>
#include <kdl/chainiksolverpos_nr_jl.hpp>

#include "geometry_msgs/msg/pose.hpp"
#include "dofbot_interfaces/srv/compute_kinematics.hpp"


class DofbotKinematicsNode : public rclcpp::Node
{
public:
    /**
     * @brief Constructor del nodo de cinemática para el robot Dofbot.
     */
    DofbotKinematicsNode();

    /**
     * @brief Callback del servicio que procesa las solicitudes de cinemática directa e inversa.
     * @param request Datos de la petición con el modo seleccionado (FK o IK) y parámetros geométricos.
     * @param response Datos de la respuesta con los resultados del cálculo y telemetría de tiempo.
     */
    void handle_kinematics_request(
    const std::shared_ptr<dofbot_interfaces::srv::ComputeKinematics::Request> request,
    std::shared_ptr<dofbot_interfaces::srv::ComputeKinematics::Response> response);

    /**
     * @brief Función de inicialización del servicio, carga del archivo urdf y las variables para el 
     * cálculo de la cinemática para el robot Dofbot.
     */
    void initialize_kinematics();

    // Miembros de ROS 2
    rclcpp::TimerBase::SharedPtr timer_;
    rclcpp::Service<dofbot_interfaces::srv::ComputeKinematics>::SharedPtr service_;

    // Elementos estructurales cinemáticos de Orocos KDL
    KDL::Chain chain_;
    unsigned int num_joints_;
    KDL::JntArray joint_min_;
    KDL::JntArray joint_max_;

    // Resolvedores (Solvers) de KDL encapsulados en punteros inteligentes
    std::unique_ptr<KDL::ChainFkSolverPos_recursive> fk_solver_;
    std::unique_ptr<KDL::ChainIkSolverVel_pinv> ik_vel_solver_;
    std::unique_ptr<KDL::ChainIkSolverPos_NR_JL> ik_pos_solver_;

};

#endif //__KINEMATICS_DOFBOT_H__