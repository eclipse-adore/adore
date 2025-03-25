#include <iostream>
#include <iomanip>  // Include <iomanip> for std::setw
#include <vector>
#include <Eigen/Dense>
#include "adore_math/eigen.h"  // Adjust the path accordingly

int main() {
    Eigen::MatrixXd eigenMatrix(3, 4);
    eigenMatrix << 1, 2, 3, 4,
                   5, 6, 7, 8,
                   9, 10, 11, 12;

    std::cout << "Original Eigen Matrix:\n" << eigenMatrix << "\n\n";

    auto stdVector = adore::math::to_vector(eigenMatrix);

    std::cout << "Matrix After Conversion to std::vector:\n";
    for (const auto& row : stdVector) {
        for (const auto& element : row) {
            std::cout << std::setw(4) << element << " ";
        }
        std::cout << "\n";
    }
    std::cout << "\n";

    auto newEigenMatrix = adore::math::to_eigen(stdVector);

    std::cout << "Matrix After Conversion back to Eigen Matrix:\n" << newEigenMatrix << "\n\n";

    return 0;
}

