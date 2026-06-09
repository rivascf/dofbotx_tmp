
#include "dofbot_kinematics/dofbot_kinematics_node.hpp"

DofbotKinematicsNode::DofbotKinematicsNode() : Node("dofbot_kinematics_node")
{
    this->declare_parameter<std::string>("robot_description", "");
    // Configurar un timer corto para esperar a que el parámetro contenga el URDF en disco o red
    timer_ = this->create_wall_timer(
        std::chrono::milliseconds(500),
        std::bind(&DofbotKinematicsNode::initialize_kinematics, this)
    );

}

void DofbotKinematicsNode::initialize_kinematics()
{
    std::string urdf_xml;
    if (!this->get_parameter("robot_description", urdf_xml) || urdf_xml.empty()) {
        RCLCPP_WARN_THROTTLE(this->get_logger(), *this->get_clock(), 2000,
            "Esperando a que el parámetro 'robot_description' sea poblado...");
        return;
    }

    timer_->cancel();

    KDL::Tree tree;
    if (!kdl_parser::treeFromString(urdf_xml, tree)) {
        RCLCPP_ERROR(this->get_logger(), "Fallo al parsear el URDF en un árbol KDL.");
        return;
    }

    std::string base_link = "base_link";
    std::string tip_link = "arm5_Link";

    if (!tree.getChain(base_link, tip_link, chain_)) {
        RCLCPP_ERROR(this->get_logger(), "No se pudo extraer la cadena KDL desde %s hasta %s", 
        base_link.c_str(), tip_link.c_str());
        return;
    }

    num_joints_ = chain_.getNrOfJoints();
    RCLCPP_INFO(this->get_logger(), "Cadena cinemática cargada con éxito. Número de articulaciones: %d", num_joints_);

    joint_min_.resize(num_joints_);
    joint_max_.resize(num_joints_);

    // Límites de joints por defecto de -PI a PI
    for (unsigned int i = 0; i < num_joints_; ++i) {
        joint_min_(i) = -M_PI;
        joint_max_(i) = M_PI;
    }

    fk_solver_ = std::make_unique<KDL::ChainFkSolverPos_recursive>(chain_);
    ik_vel_solver_ = std::make_unique<KDL::ChainIkSolverVel_pinv>(chain_);
    ik_pos_solver_ = std::make_unique<KDL::ChainIkSolverPos_NR_JL>(
        chain_, joint_min_, joint_max_, *fk_solver_, *ik_vel_solver_, 100, 1e-5);

    service_ = this->create_service<dofbot_interfaces::srv::ComputeKinematics>(
        "compute_kinematics",
        std::bind(&DofbotKinematicsNode::handle_kinematics_request, 
        this, 
        std::placeholders::_1, 
        std::placeholders::_2)
    );

    RCLCPP_INFO(this->get_logger(), "Servicio /compute_kinematics listo.");
}

void DofbotKinematicsNode::handle_kinematics_request(
  const std::shared_ptr<dofbot_interfaces::srv::ComputeKinematics::Request> request,
  std::shared_ptr<dofbot_interfaces::srv::ComputeKinematics::Response> response)
{
    auto start_time = this->now();

    if (request->kinematics_mode == dofbot_interfaces::srv::ComputeKinematics::Request::FORWARD_KINEMATICS) {
        if (request->joint_positions.size() != num_joints_) {
            response->success = false;
            response->message = "Error: El número de joints provisto no coincide con la cadena.";
            response->elapsed_time = (this->now() - start_time);
            return;
        }

        KDL::JntArray jnt_pos(num_joints_);
        for (unsigned int i = 0; i < num_joints_; ++i) {
            jnt_pos(i) = request->joint_positions[i];
        }

        KDL::Frame result_frame;
        int status = fk_solver_->JntToCart(jnt_pos, result_frame);

        if (status >= 0) {
            response->success = true;
            response->message = "FK calculada correctamente.";
        
            response->calculated_pose.position.x = result_frame.p.x();
            response->calculated_pose.position.y = result_frame.p.y();
            response->calculated_pose.position.z = result_frame.p.z();
        
            double qx, qy, qz, qw;
            result_frame.M.GetQuaternion(qx, qy, qz, qw);
            response->calculated_pose.orientation.x = qx;
            response->calculated_pose.orientation.y = qy;
            response->calculated_pose.orientation.z = qz;
            response->calculated_pose.orientation.w = qw;
        } else {
            response->success = false;
            response->message = "Fallo interno en el solver FK de KDL.";
        }
    }
    else if (request->kinematics_mode == dofbot_interfaces::srv::ComputeKinematics::Request::INVERSE_KINEMATICS) {
        KDL::Vector pos(request->target_pose.position.x, request->target_pose.position.y, request->target_pose.position.z);
        KDL::Rotation rot = KDL::Rotation::Quaternion(
            request->target_pose.orientation.x,
            request->target_pose.orientation.y,
            request->target_pose.orientation.z,
            request->target_pose.orientation.w
        );

        KDL::Frame target_frame(rot, pos);

        KDL::JntArray jnt_seed(num_joints_);
        KDL::JntArray jnt_result(num_joints_);

        int status = ik_pos_solver_->CartToJnt(jnt_seed, target_frame, jnt_result);
        if (status >= 0) {
            response->success = true;
            response->message = "IK calculada correctamente.";
            response->calculated_joint_positions.resize(num_joints_);
            for (unsigned int i = 0; i < num_joints_; ++i) {
                response->calculated_joint_positions[i] = jnt_result(i);
            }
        } else {
            response->success = false;
            response->message = "El solver IK no pudo converger a una solución.";
        }
    } 
    else {
        response->success = false;
        response->message = "Tipo de modo cinemático (kinematics_mode) desconocido.";
    }

    rclcpp::Duration duration = this->now() - start_time;
    response->elapsed_time = duration;
}

int main(int argc, char * argv[])
{
    rclcpp::init(argc, argv);
    rclcpp::spin(std::make_shared<DofbotKinematicsNode>());
    rclcpp::shutdown();
    return 0;
}