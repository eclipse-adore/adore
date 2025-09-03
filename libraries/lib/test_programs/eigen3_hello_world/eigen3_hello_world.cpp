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

#include <iostream>
#include <Eigen/Dense>

int main() {
    std::cout << "Eigen3 Test:" << std::endl;
    Eigen::MatrixXd m_eigen(2,2);
    m_eigen(0,0) = 3;
    m_eigen(1,0) = 2.5;
    m_eigen(0,1) = -1;
    m_eigen(1,1) = m_eigen(1,0) + m_eigen(0,1);
    std::cout << m_eigen << std::endl;
    return 0;
}
