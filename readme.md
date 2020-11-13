# N Largest CLI

An intuitive CLI to receive id, number pairs from a remote text file and print the ids of the highest N numbers in
the file.

:warning: This application currently relies on the ```Range``` http header in order to protect available memory when
 dealing with very large files. When providing a url for a remote file, you must ensure the remote file's host supports
 ```Range``` headers. Known hosts which support such headers are AWS S3
 and GCP Cloud Storage.

## How It Works
The N Largest CLI was built to minimize data transfer (over the network) as well as memory usage while sorting an
 arbitrarily large dataset from a remote repository. Using the ```Range``` http header, only a small portion of the file 
 is ever stored in memory. This behavior is also configurable via the CLI options, as large files will benefit from
 processing larger chunks at a time, granted there is enough available memory. Each remote file is compressed and 
 cached on disk to prevent potentially very large files from needing to be repeatedly sent over the network just to do
 the same (or similar) computation on them. The cache is also configurable (see the [clear-cache](#clear-cache) and 
 [set-cache-dir](#set-cache-directory) commands). The sorting mechanism for the data received from the remote file uses
 a priority queue algorithm (also known as heap queue) to report the ids of the top N numbers. This has the benefit of
 running in order of 
 <img alt="big O n log n" src="https://render.githubusercontent.com/render/math?math=O(n\log(n))">
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
must be 1 or greater. If N is greater than the number of ids in the text file, ```min(N, T)``` ids will be returned
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
[local development](#usage-and-deployment) section.

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
docker exec -it <container name or id> nlargest get <remote file url> 5
```

<br />
<br />

## Usage on Local Machine or for Development
The N largest CLI can also be ran on your local machine without the use of docker. All you need is to have python 3
 installed or create a virtualenv. It is recommended you use a virtualenv however because you will be installing a
 local package from ```setup.py``` and if a virtualenv is not used it will be installed globally.
 To get started, first install all dependencies
```
pip install -r requirements.txt
```
Next you will need install the local package defined in ```setup.py```. The following command should be ran from the
root directory of the project.
```
pip install .
```
If installing for local development, you will need to run a different version of the above command in order to make the
local package update when the code is changed without re-installing each time.
```
pip install --editable .
```
From this point on, the commands can be ran anywhere on the local machine. The only caveat is that the python
interpreter which was used to install the local package must be available to run the commands. So for example, if you
used a virtualenv to install, that virtualenv must be activated in order for the commands to be in your ```PATH```

<br />
<br />

## Complexity

#### Space
Space complexity was front and center when designing this CLI in order to accommodate machines with limited memory but
which need to process arbitrarily large files. There are two points in the execution of an ```nlargest get``` command in
which space complexity is concerned. First is when the remote file is requested from the repository and cached on disk.
In this case the space complexity is equal to the fraction of the file specified with the ```--chunk-size``` option.
In the worst case the user will specify a chunk size greater than or equal to the size of the file, in which case it
take up ![big O n](https://render.githubusercontent.com/render/math?math=O(n)) in memory. If chunk size is less than the
size of the whole file, space complexity is equal to 
<img alt="big O n over cs" src="https://render.githubusercontent.com/render/math?math=O(\frac{n}{chunksize})" >.
The second point is when the n largest ids are computed. Generators are used to iterate through all id, number tuples
which puts it at 
![big O constant](https://render.githubusercontent.com/render/math?math=O(1)). However, the priority queue algorithm
 will store ```m``` tuples where ```m``` refers to the top ```N``` ids requested in the command. This means space
 complexity at this step will be ![big O n](https://render.githubusercontent.com/render/math?math=O(n)) for choices of
 ```N``` which are close to the number of lines in the remote text file and will be 
 ![big O constant](https://render.githubusercontent.com/render/math?math=O(1)) for choices of ```N``` which are close to
 ```N = 1```. Therefore in the worst case, space complexity is 
 ![big O n](https://render.githubusercontent.com/render/math?math=O(n)). It is worth noting too that each remote file is
 compressed and cached on disk unless specified otherwise in the command.

#### Time
The sorting algorithm for the CLI uses a priority queue algorithm in which a min heap is populated with the first
 ```N``` elements in the collection of id, number pairs. The root of the heap is checked against the remaining numbers
 and replaced if the new number is greater than the root. This means the complexity is of order
<img alt="big O log n m" src="https://render.githubusercontent.com/render/math?math=O(m\log(n)" > where ```n``` is the
number of top ids requested in the command and ```m``` is the number of lines in the remote file. You may recognize that
this gives the algorithm the property of running in 
![big O n](https://render.githubusercontent.com/render/math?math=O(n)) time for choices of ```n``` which are close to
1, and <img alt="big O log n m" src="https://render.githubusercontent.com/render/math?math=O(n\log(n)" > for choices of
```n``` which are close to ```m```.

#### Data Transfer
The complexity of data transfer (over the network) is more straight forward as it occurs only once for each file unless
the cache is cleared or ```--refresh-cache``` is specified. Therefore, each subsequent computation on a file after the
initial transfer is much quicker and requires zero data transfer.

<br />
<br />

## Testing
Existing tests are located in the ```test``` directory in the root directory of the project. Inside is a single test
file, ```test.py```. To run all tests and get results, navigate to the test folder and simply run:
```
python test.py
```
This can be done within the docker container or on your local machine.

<br />
<br />

## Possible Improvements
#### Check disk space
Currently the application does not check for available disk space or warn when disk space is becoming depleted after a 
remote file is cached. Therefore a good improvement would be to at least warn the user if, after caching a remote 
file, disk space is close to max capacity.

#### Have memory only option
Currently, if available memory is not an issue and the user would prefer to receive the entire remote file in one call
they would need to specify the ```--chunk-size``` to be greater than the size of the file, which sometimes may be
 unknown. Therefore an improvement would be to add a flag which will force the entire remote file to be downloaded at
 once, regardless of size.

#### Reliance on Range headers
The functionality of receiving only a portion of a potentially large file is currently achieved with http ```Range```
headers. This is efficient but requires the file's host to support such headers. Therefore it would be a good
improvement which is more host agnostic such as using sockets to request part of the file instead of http headers.

#### Add Cache for Top N Id Results
Currently the cache only stores the actual file to optimize data transfer (and also runtime), but computation could be sped
up even more if the cache also stored the results of computations, making requests for the same N on the a cached remote
file run in ![big O constant](https://render.githubusercontent.com/render/math?math=O(1)) time.
