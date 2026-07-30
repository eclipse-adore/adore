# Standalone Test Program for Downloading a Map from a WFS

---

To execute the test:

- Add the password in `config/r2s_wfs_config_bs.json`.
- If not done yet, build ADORe with `make build` in the project directory `adore`.
- Then, in the same directory, type `make cli`, and press return to start the ADORe CLI.
- Type `cd ros2_workspace/install/adore_map_downloader_test/bin`, and press return.
- Type `./basic_map_loading_from_wfs_test` (without any parameters), and press return.
- You should see the line "adore_nowcast_test: Nowcast query test completed successfully, good!" along the last few lines.

---
