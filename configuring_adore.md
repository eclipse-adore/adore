# Configuring ADORe

ADORe and the ADORe CLI can be configured through environment variables defined in [`adore.env`](./adore.env).

## Configuration File

The configuration file can be used to configure control ADORe's behavior:

- **Build Configuration**: Control parallel vs sequential builds
- **API Configuration**: Enable/disable and configure the ADORe API server
- **Logging Configuration**: Configure rsyslog server and forwarding
- **General Settings**: File size limits, paths, and other runtime parameters

## Usage

The environment variables are automatically sourced by ADORe components and 
build scripts. Modify the values in `adore.env` and the ADORe CLI to apply changes.

See the configuration file for detailed documentation on each variable and its available options.
