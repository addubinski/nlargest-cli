# N Largest CLI

An intuitive CLI to receive id, number pairs from a remote text file and print the ids of the highest N numbers in
the file.

:warning: This application currently relies on http header ```Range``` in order to protect available memory when dealing
 with very large files. When providing a url for a remote file, you must ensure the remote file's host supports
 ```Range``` headers. Known hosts which support such headers are AWS S3
 and GCP Cloud Storage.

## How It Works
The N Largest CLI was built to minimize data transfer over the internet and memory usage while sorting an arbitrarily
large dataset from a remote repository. Using http ```Range``` header only a small portion of the file is ever stored in
memory. This behavior is also configurable via the CLI options, as large files will benefit from processing larger
 chunks at a time, granted there is enough available memory. Each remote file is compressed and cached on disk to
to prevent potentially very large files from needing to be repeatedly sent over the network just to do the same
 (or similar) computation on them. The cache is also configurable (see the [clear-cache](#clear-cache) and 
 [set-cache-dir](#set-cache-directory) commands). The sorting mechanism for the data received from the remote file uses
 a priority queue algorithm (also known as heap queue) to report the ids of the top N numbers. This has the benefit of
 being running in order of ![big O n log n](https://render.githubusercontent.com/render/math?math=O(n{log(n)}))
  in the worst case and ![big O n](https://render.githubusercontent.com/render/math?math=O(n)) for certain choices of N.
   See the [complexity](#complexity) for more on this.

## Commands

#### Top Level Command 
```
nlargest [OPTIONS] COMMAND [ARGS]
```
> The top level command from which all [sub commands](#sub-commands) will be invoked.
##### Options

* ```--help``` : display help information.

<br />

#### Sub Commands

##### Get
```
nlargest get [OPTIONS] URL N
```
> Get a text file from the specific remote ```URL``` and print the ```N``` ids corresponding to the ```N``` largest
 number found in the text file.

##### Arguments
* ```URL``` : The url starting with http(s) and using a fully qualified domain name leading to a text file. (Required)
* ```N``` : The N number of ids corresponding to the N highest numbers in the remote text file. This number
must be 1 or greater. If a N is greater than the number of ids in the text file, ```min(N, T)``` ids will be returned
where ```T``` refers to the total number of entries in the remote text file. (Required) 
###### Options
* ```--help``` : Display help information.
* ```--no-cache``` : A flag, when present, will prevent the remote file from be cached on the local filesystem.
 Furthermore, if a cached version of the remote file already exists it will be discarded.
* ```--refresh-cache``` : A flag, when present, will ignore the cache and replace the cached file with whatever is
 received from the remote repository. If the specified remote file did not already have an entry in the cache the
  behavior is the same as without the flag.
* ```-c, --chunk-size``` : The chunk size option takes an argument for the size in bytes for each request to the remote
 file. The default is 256kb and chunk size can be a minimum of 1024 bytes. <b>For files over a few MB the chunk size
  option should be used to maintain good performance.</b> This feature exists to protect available memory. At most the
   remote file will only take up an amount of memory equal to the chunk size. This is to accommodate very large files
    which will not fit into memory. If the chunk size is too small performance will be impacted due to small 
    portions of the file being sent over the network synchronously. For more details see [How it Works](#how-it-works).

<br />
<br />

##### Set Cache Directory
```
nlargest set-cache-dir [OPTIONS] ABSOLUTE_PATH
```
> Sets the directory within the local file system used for cached files to ```ABSOLUTE_PATH```.

##### Arguments
* ```ABSOLUTE_PATH``` : Absolute path within the local filesystem where compressed cached files will be
 stored. When set, all existing cache files will be moved to the new cache directory. Must be a directory, not a file.
 If the specified directory does not exist, it will be created if permissible. (Required) 
###### Options
* ```--help``` : display help information.

<br />
<br />

##### Clear Cache
```
nlargest clear-cache [OPTIONS]
```
> Clears all content from the cache. <b>Cache cannot be recovered after running this command.</b>

###### Options
* ```--help``` : display help information.

<br />
<br />

## Usage and Deployment
The CLI can be used on a local machine without Docker or in a docker container. For usage on a local machine, see the
[local development](#local-development) section.

#### Deployment with Docker
First build and image with the provided Dockerfile and make sure it is built in the root directory.
```
docker build . -t <image tag name>
```
After building you can run it and the attached console will put you in the root directory of the CLI code.
```
docker run -it <image tag name or id>
```
Commands can be ran from anywhere in the container using bash or can be ran externally from the container with
 ```docker exec```
```
docker exec -it <container name or id> nlargest get https://alexander-dubinski.com 5
```

<br />
<br />

## Local Development

<br />
<br />

## Complexity


<br />
<br />

## Possible Improvements