# Standalone Test Program for Querying the Nowcast Service (Work in Progress)

---

To execute the (preliminary) test:

- Add the password in `config/nowcast_test_config.json`.
- If not done yet, build ADORe with `make build` in the project directory `adore`.
- Then, in the same directory, type `make cli`, and press return to start the ADORe CLI.
- Type `cd ros2_workspace/install/adore_nowcast_test/bin`, and press return.
- Type `./adore_nowcast_test` (without any parameters), and press return.
- You should see the line "adore_nowcast_test: Nowcast query test completed successfully, good!" along the last few lines.

---
