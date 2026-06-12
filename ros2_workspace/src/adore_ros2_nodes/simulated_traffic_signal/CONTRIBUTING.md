# Contributing to the project 

Thank you for your interest in contributing to this Eclipse project!  
This document outlines the process and guidelines for contributing.

---

## Eclipse Foundation Requirements

This project is governed by the [Eclipse Foundation Development Process](https://www.eclipse.org/projects/dev_process/).  
Before contributing, please ensure you have completed:

- **Eclipse Contributor Agreement (ECA)**  
  All contributors must have a valid, signed [ECA](https://www.eclipse.org/legal/eca/).  
  Contributions can only be accepted from contributors with an active ECA.

- **Sign-off on commits**  
  Each commit must be signed off to certify compliance with the [Developer Certificate of Origin (DCO)](https://developercertificate.org/).  
  Use the `-s` flag when committing:  

  ```bash
  git commit -s -m "Commit message"
  ```

---

## How to Contribute

1. **Fork and clone the repository**  
   ```bash
   git clone https://github.com/eclipse/[project].git
   ```

2. **Create a feature branch**  
   ```bash
   git checkout -b feature/my-feature
   ```

3. **Make your changes**  
   - Follow project coding style and guidelines.
   - Include/update tests where appropriate.
   - Update documentation if behavior changes.

4. **Run tests locally**  
   Ensure the build and test suite passes before opening a PR:
   ```bash
   mvn clean verify
   ```

5. **Commit and push**  
   ```bash
   git commit -s -m "Describe your change"
   git push origin feature/my-feature
   ```

6. **Open a Pull Request (PR)**  
   - Clearly describe the problem and solution.
   - Reference any related issues (`Closes #123`).
   - Ensure all checks pass before requesting review.

---

## Reporting Issues

- Use the GitHub Issues page.
- Provide steps to reproduce, expected behavior, and actual behavior.
- Attach logs, stack traces, or test cases where possible.

---

## License

All contributions to this project are made under the terms of the [Eclipse Public License 2.0 (EPL-2.0)](https://www.eclipse.org/legal/epl-2.0/).

---

