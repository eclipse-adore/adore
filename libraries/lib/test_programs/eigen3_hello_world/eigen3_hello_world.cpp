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
