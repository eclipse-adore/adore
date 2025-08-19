# Contributing to ADORe

> ADORe is proudly open source. Sponsor features by sending a pull request.  
> We would also love to know how you are using ADORe – reach out to us on GitHub.  
>
> Did you find a bug? Then submit a GitHub [issue 🔗](https://github.com/eclipse/adore/issues) or provide a solution by  
> sending a [pull request 🔗](https://github.com/eclipse/adore/pulls), contributions are welcome!

---

## 1. Getting Started

1. Fork the repository to your own GitHub account.
2. Clone your fork:
   ```bash
   git clone https://github.com/your-username/adore.git
   cd adore
   ```
3. Set up the upstream remote:
   ```bash
   git remote add upstream https://github.com/eclipse/adore.git
   git fetch upstream
   ```
4. Ensure you're working off the `develop` branch:
   ```bash
   git checkout develop
   git pull upstream develop
   ```

Refer to the repository’s **README** for details about system requirements, installation steps (including Docker and ROS 2), and quick-start examples.

---

## 2. How to Contribute

### Reporting Issues
- Ensure the issue has not already been reported.
- Provide a clear title and detailed description, including:
  - Steps to reproduce
  - Expected vs actual behavior
  - Environment details (OS, Architecture, etc...)
- Label the issue according to the project’s conventions if applicable.

### Suggesting Features
- Propose enhancements or extensions, e.g., for planning algorithms or simulation integration (CARLA, SUMO).
- Describe use cases and potential benefits.

### Submitting Pull Requests (PRs)

1. Create a feature branch:
   ```bash
   git checkout -b feature/my-enhancement
   ```
2. Commit changes with descriptive messages.
3. Rebase on the latest `develop` branch to keep history clean:
   ```bash
   git fetch upstream
   git rebase upstream/develop
   ```
4. Push to your fork and open a PR against `develop`.
5. In your PR description, explain:
   - What the change addresses.
   - Any new dependencies or configuration adjustments.
   - How to test it.

### Code Style & Quality
- Adhere to the repository’s formatting and style rules.
  - **C++**: follow `.clang-format`
  - **Python / Shell**: match formatting of existing code
  - Maintain clean, readable commit history
- If applicable, ensure tests are included or updated.

### Documentation
- Add or update docs in the `documentation/technical_reference_manual` folder:
  - Installation instructions
  - Usage examples or reference manual
  - Architecture overviews, etc.
- Keep documentation consistent with existing style and structure.
- spell check you contributions with `aspell`

---

## 3. Review Workflow

- PRs will be reviewed by maintainers and may receive feedback.
- Please address comments promptly.
- Once approved, your PR will be merged into `develop`.
- Major features or disruptive changes may require design discussions or a design document.

---

## 4. Community & Support

- For general discussions, reach out via GitHub Discussions or open a new issue.
- Contributors may be acknowledged in an **ACKNOWLEDGMENTS** section in the README or a separate file.
- For any queries, feel free to contact the maintainers.

---

## 5. Code of Conduct

By participating, you agree to follow our [Code of Conduct](CODE_OF_CONDUCT.md), 
which aims to foster a welcoming and respectful environment.


---

## Thank You!

Your contributions help evolve **ADORe** and support the advancement of autonomous vehicle research. Welcome aboard!

