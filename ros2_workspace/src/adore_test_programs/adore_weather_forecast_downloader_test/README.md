# Standalone Test Program for the Weather Forecast Downloader

---

To execute the test:

- Build ADORe with `make build` in the project directory `adore`.
- Then, in the same directory, type `make cli`, and press return to start the ADORe CLI.
- Type `cd ros2_workspace/install/adore_weather_forecast_downloader_test/bin`, and press return.
- Type `./adore_weather_forecast_downloader_test`, and press return.
- You should see the line "adore_weather_forecast_downloader_test: Weather forecast downloader
  query test completed successfully, good!" along the last few lines.
---

This program performs **real queries from the server** (unlike the offline gtest suite in the
`test` directory). It exercises the configured source chain — the first enabled source, in
priority order, wins — and then independently validates every configured source
(`noaa`, `dwd`, `open_meteo`) against its live API. A single source being temporarily
unavailable does not fail the test, as long as at least one source succeeds.