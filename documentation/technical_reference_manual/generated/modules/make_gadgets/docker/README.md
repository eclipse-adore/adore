# Make Gadgets docker Makefile

This directory contains a Makefile with docker helper targets.  They can be
imported to extend your makefile or called directly.

## Docker tools Makefile
This directory contains a Makefile that enhance vanilla docker with make.

The Makefile also provides several practical targets that wrap the functionality of the docker-image-cacher.sh tool
provided in this project.

To consume the provided targets/recipes from the project you can directly import the desired module to your Makefile 
such as follows: 
```make
include make_gadgets/docker/docker-tools.mk
```

To include the docker-image-cacher target/recipes add the following to the top of your Makefile:
```bash
include make_gadgets/docker/docker-image-cacher.mk
```


You can directly call the provided targets/recipes by calling make directly on this directory:
```bash
cd make_gadgets/docker
make docker_save
...
make docker_load
...
make docker_orbital_cannon
```

## docker-image-cacher.sh
The docker-image-cacher.sh is a utility script for batch caching/saving and loading docker images to archives with the
goal of saving network resources and quotas.

There are several major functions this script offers namely fetching, saving, loading, and printing.  All of these
will be discussed in the coming sections.

### Image Discovery
The docker-image-cacher.sh uses a very simple strategy for discovering docker images to fetch and cache:
1. The image search path is searched and scraped recursively for Dockerfiles containing 'from <repository:tag>'
- If no search path is provided then the docker image list is assumed from the docker local registry e.g., everything in 'docker image ls'
- If the local registry is empty then only images provided in the inclusion list are added
2. All images provided in the inclusion list are appended to the found images
3. All images from the exclusion list are removed from the found images

Image discovery is used for fetching, caching/saving, and printing. 

### Printing
you can call docker-image-cacher.sh with the -p or --print flag to perform a print operation.

The print operation or action simply prints the docker image list that will be fetched and cached/saved with their respective
operations.

Printing preempts all other actions, the list of docker images will be printed and the program will exit.

### Fetching
You can call docker-image-cacher.sh with the -f or --fetch flag to perform a fetch operation.

There are two ways this can be done. The fist way provides a docker image search path as a basis
to collect a list of images to fetch as in the following example:
```bash
bash docker-image-cacher.sh --docker-image-search-path "<some search path>" --fetch
```
All Dockerfiles in the search path provided will be recursively searched for the docker key word "FROM". Any image 
that is referenced by "FROM IMAGE:TAG" in any Dockerfile within the search path will be fetched with docker using 
the docker pull command.

The second way to fetch docker images is to provide no search path such as follows:
```bash
bash docker-image-cacher.sh --fetch
```
This will effectively update every image already loaded into docker on your host.

### Saving/Caching
Saving can be called in several ways.  The first way is providing a cache directory and search path:
```bash
bash docker-image-cacher.sh --docker-image-search-path "<some search path>" --docker-image-cache-directory "<cache dir to save images to>" --save
```
resulting in every discovered docker image will be saved into the default docker image cache directory as an archive 
for each image. 

Another way save can be called is providing a search path but no cache directory:
```bash
bash docker-image-cacher.sh --docker-image-search-path "<some search path>" --save
```
The image archives will be saved to the default cache path.

Another way to call save is without a search path such as follows:
```bash 
bash docker-image-cacher.sh --save
```
Every image in the docker registry will be saved to disk as a tar archive into
the default docker image cache directory.

In order for save to work all docker images in the image list must exist in the docker registry. An image can be added
to the registry in multiple ways:
- Calling 'docker build' on a Dockerfile containing an image reference will pull it to the local registry
- Calling 'docker pull <repository:tag>'
- Using docker-image-cacher.sh with the --fetch flag to batch pull a list of images.

### Loading
All images that are cached as tar archives in the default docker image cache directory will be loaded into the docker registry.
```bash
bash docker-image-cacher.sh --load
```

You can also load all docker images from a specific cache directory:
```bash
bash docker-image-cacher.sh --docker-image-cache-directory "<some cache dir>" --load
```

### Help
To view more documentation on this tool you can run the help flag:
```bash
bash docker-image-cacher.sh --help
```

## Use Cases
This section will give a few practical use cases for the docker-image-cacher.sh tool

### Scrape your home directory for docker images, fetch them, and save them
```bash
bash docker-image-cacher.sh -docker-image-search-path "${HOME}" --fetch --save
```
Your home directory must have at least one Dockerfile somewhere in the directory tree.

### Save all docker images in the local registry to the default cache location
```bash
bash docker-image-cacher.sh --save
```

### Load docker images from the default cache location into the local registry
```bash
bash docker-image-cacher.sh --load
```

### Fetch and save the docker image 'ubuntu:latest'
```bash
bash docker-image-cacher.sh --save --fetch -i 'ubuntu:latest'
```
and later 'ubuntu:latest' can be loaded from disk back into the local registry with:
```bash 
bash docker-image-cacher.sh --load 
```

### Fetch and save the docker image 'ubuntu:latest' and 'alpine:latest'
```bash
bash docker-image-cacher.sh --save --fetch -i 'ubuntu:latest alpine:latest'
```
and later both 'ubuntu:latest' and 'alpine:latest' can be loaded from disk back into the local registry with:
```bash 
bash docker-image-cacher.sh --load 
```


