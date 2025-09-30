/********************************************************************************
 * Copyright (c) 2025 Contributors to the Eclipse Foundation
 *
 * See the NOTICE file(s) distributed with this work for additional
 * information regarding copyright ownership.
 *
 * This program and the accompanying materials are made available under the
 * terms of the Eclipse Public License 2.0 which is available at
 * https://www.eclipse.org/legal/epl-2.0
 *
 * SPDX-License-Identifier: EPL-2.0
 ********************************************************************************/

#include "rclcpp/rclcpp.hpp"
#include <Eigen/Dense>
#include <sstream>

static std::string matrixToString(const Eigen::MatrixXd& mat){
    std::stringstream ss;
    ss << mat;
    return ss.str();
}

int main(int argc, char *argv[]) {
    rclcpp::init(argc, argv);
    auto node = rclcpp::Node::make_shared("ros2_eigen_hello_world");

    RCLCPP_INFO(node->get_logger(), "ROS2 Eigen3 Hello, World!");

    Eigen::MatrixXd m_eigen(2, 2);
    m_eigen(0, 0) = 3;
    m_eigen(1, 0) = 2.5;
    m_eigen(0, 1) = -1;
    m_eigen(1, 1) = m_eigen(1, 0) + m_eigen(0, 1);

    //std::cout << m_eigen << std::endl;
    RCLCPP_INFO_STREAM(node->get_logger(), ("m_eigen matrix:\n" + matrixToString(m_eigen)).c_str());

    std::this_thread::sleep_for(std::chrono::seconds(1));

    rclcpp::shutdown();
    return 0;
}

