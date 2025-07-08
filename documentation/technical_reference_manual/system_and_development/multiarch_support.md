## Multi-Architecture Support

The ADORe CLI supports both **native** and **cross-compilation** workflows for 
`x86_64` and `arm64` architectures.

### Native Build

To build and run ADORe CLI **natively** on your current architecture:

```bash
make build
make cli
```

This will build and run the CLI on your host architecture 
(`x86_64` or `arm64` depending on your system).

### Cross-Compilation

To **cross-compile** the CLI for `arm64` from an `x86_64` host (or vice versa),
set the `ARCH` environment variable during build and run:

```bash
ARCH=arm64 make build
ARCH=arm64 make cli
```

This compiles the CLI binary for the specified target architecture 
(`arm64` in this case) and runs it using emulation if needed (e.g., with QEMU 
if running on `x86_64`).

### Supported Architectures

- `x86_64` (native or host)
- `arm64` (native or cross-compiled)

### Notes
When running `make cli` or `make build` with `ARCH=arm64` on an `x86_64` host
necessary system dependencies for docker will be automatically installed 
including Docker QEMU.

### Cross Compiling

```bash
# Cross-compile and run ADORe CLI for ARM64 on an x86_64 host
ARCH=arm64 make build
ARCH=arm64 make cli
```


