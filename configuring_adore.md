# Configuring ADORe

ADORe and the ADORe CLI can be configured through environment variables defined in [`adore.env`](./adore.env).

## Configuration File

The configuration file can be used to configure control ADORe's behavior:

- **Build Configuration**: Control parallel vs sequential builds
- **API Configuration**: Enable/disable and configure the ADORe API server
- **Logging Configuration**: Configure rsyslog server and forwarding
- **General Settings**: File size limits, paths, and other runtime parameters
- **ROS Settings**:  ROS Domain ID, ROS logging directory

## Usage

The environment variables are automatically sourced by ADORe components and 
build scripts. Modify the values in `adore.env` and restart the ADORe CLI with 
`make stop && make start` or `make restart` to apply changes.

See the `adore.env` configuration file for detailed documentation on each 
variable and its available options.
