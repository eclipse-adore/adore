# Helix Editor Docker Installation

This docker file sets up and build the 25.01.1 version of the Helix Editor if the host system is x86_64.

Link to the helix editor website:
~~~
https://github.com/helix-editor/helix
~~~

## How to install
To build the amd64 debian file of Helix use the make file

~~~
make build
~~~
This will output the debian file in build/helix folder.

To cleanup afterwards, use

~~~
make clean
~~~

To manually install the build debian file, use the command.

~~~
sudo apt-get install ./<debian_output_file_name>
~~~
