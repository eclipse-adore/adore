# ADORe Prerequisites
ADORe requires a recent version of make and Docker on your system. ADORe is
officially supported in Ubuntu 20.04, 22.04 and 24.04. The following document applies to
that.

### Check your system
Check to make sure you have a supported system by running the following command:
```bash
cat /etc/os-release | grep "VERSION=" | cut -d"=" -f2
```
should yield something such as the following:
```text
"24.04.2 LTS (Noble Numbat)"
```

In principle, any x86 Linux operating system supporting Docker and Make will run
ADORe however installation steps for all the tooling will differ. 

### Installing make
```
sudo apt-get install -y make
```

### Installing Docker
Review the [Installing Docker 🔗](installing_docker.md) 

### Checking your free space
ADORe and the associated tools require a significant amount of transient storage
It is recommended that you have a **minimum** of 20 GB of free space to work with
ADORe. Optimally, you should have at least 40 GB. To check the amount of free
space on your system you can run the following command:
```bash
df -h . | awk 'NR==2 {print "Available Free Space:", $4}'
```

### Time
On the first build of ADORe you will need ~15-20 minutes to download and clone 
all the sources, dependencies, and context. Subsequent builds are very quick 
after requisite caches (apt, docker) have been established.

> **ℹ️ INFO:**
> Build and fetch times can very greatly depending on system configuration and
> network.

## Conclusion
Once you have the correct operating system, sufficient free disk space,
and both Make and Docker installed, you will be ready to proceed with using ADORe.
