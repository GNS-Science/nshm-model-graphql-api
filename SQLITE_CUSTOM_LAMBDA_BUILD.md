# Building a modern SQLite3 library for Django 4 for AWS lambda + Python 3.10 

Chris B Chamberlain, August 31, 2023.

## Why we're even trying this

We want a light weight, read-only sql database for django, that we can run in an AWS lambda function. It has been done, and the zappa project even make a read-write version, which gives some valuable tips:

- https://github.com/FlipperPA/django-s3-sqlite
- https://github.com/FlipperPA/django-s3-sqlite/tree/main/shared-objects/python-3-8 

## Issue 1) AWS lambda sqlite3 libary is outdated.

Modern django expects `sqlite3>=3.83`. But currently the AWS python10 lambda environment offers us `sqlite3 version: 3.7.17`

So, following this guide https://charlesleifer.com/blog/compiling-sqlite-for-use-with-python-applications/

we're able to build and test a modern sqlite (currenlty 3.44), but unfortunately this still doesn't work on lambda...

## Issue 2) the custom sqlite3 libary must be linked against the `libc` version available on AWS lambda.

So, while our locally compiled sqlite3 library works locally, in lambda we get:

```ImportError: /lib64/libm.so.6: version `GLIBC_2.29' not found (required by /var/task/_sqlite3.cpython-310-x86_64-linux-gnu.so)```. 

NB. the version above may vary from system to system, since it's based on the local build environment.

Currently, AWS lambda provides us with `GLIBC_2.26`.

The recipe below resolved this problem for us.

### Background reading, tips & techniques

I found these articles very helpful with figuring out what was actually going on here.

 - https://www.cyberithub.com/solved-glibc-2-29-not-found-error-on-ubuntu-linux/ good, but not a workable fix for lambda
 - https://stackoverflow.com/questions/4032373/linking-against-an-old-version-of-libc-to-provide-greater-application-coverage
 - https://stackoverflow.com/questions/69692703/compiling-python-3-10-at-amazon-linux-2 
 - https://stackoverflow.com/a/69879426
 - https://stackoverflow.com/a/851229 very useful big-picture 
 - https://stackoverflow.com/a/49355708 same issue, it's not easy
  -https://unix.stackexchange.com/questions/487303/how-to-find-the-name-of-the-so-file-which-contains-the-code-for-a-specific-funct

## A Recipe for running sqlite3 on AWS lambda

To get a build that works on AWS lambda we can use a suitable EC2 Linux2 instance and the following steps:

### 1) Launch an AWS EC2 instance

This is a simple way to get a lambda-compatible build enivironment: 

I used a T2.medium instance, it's a bit faster than the smaller instances. Use the  [AWS Linux 2 image](https://ap-southeast-2.console.aws.amazon.com/ec2/home?region=ap-southeast-2#Images:visibility=public-images;imageId=ami-0dab9ecf8f21f9ff3) or whatever is currently equivalent to the lambda OS.

The thing that really matters is the version of libc that's installed. We want to see `ldd (GNU libc) 2.26` which is exactly what we see on lambda:

```
$> ldd --version
ldd (GNU libc) 2.26
...
```

NB We've added a check for the current version in the projects' lambda startup function (wsgi.py) which is enabled when the environment varaible `DEBUG` is True.

### 2) install the build tools

with a console, e.g. `ssh`` or the AWS web ui.

```
sudo yum groupinstall "Development Tools"
sudo yum -y install bzip2-devel libffi-devel openssl11 openssl11-devel
sudo yum install tcl
```

### 3) install python 3.10.x

```
wget https://www.python.org/ftp/python/3.10.13/Python-3.10.13.tgz
tar xzf Python-3.10.13.tgz
cd Python-3.10.13/
./configure --enable-optimizations
sudo make altinstall
```

And now check that you have a working **python3.10** and **pip3**:

```
which python3.10
python3.10 --version
pip3.10 --version
```

### 4) install virtualenv

```
pip3.10 install virtualenv
virtualenv --help
```

### 5) install & configure sqlite

At this time the latest version is 3.44. Recall that we need >= 3.8.3 for django compatablity, and to avoid the original `deterministic=True requires SQLite 3.8.3 or higher` error.

```
wget https://www.sqlite.org/src/tarball/sqlite.tar.gz
tar xzf sqlite.tar.gz
cd sqlite
./configure
make sqlite3.c
```

### 6) build the custom sqlite library (via pysqlite build script)

The basis fo this recipe is [laid out here](https://charlesleifer.com/blog/compiling-sqlite-for-use-with-python-applications/) by the maintainer of pysqlite, Charles Liefer.

Note that it's not stricly necessary to use the virtualenv option , but I chose that path.

**6.1)** Create and activate a virtual environment
```
virtualenv -p /usr/local/bin/python3.10 sqlite344
cd sqlite344
source bin/activate
```


**6.2)** Clone the repo to a different name (avoids import issues)

```
git clone https://github.com/coleifer/pysqlite3 pysqlite3-build
cd pysqlite3-build
```

**6.3)** build library using the src and header files from the sqlite config in step 5.
```
cp ../../sqlite/sqlite3.[ch] .
python setup.py build_static
```

**6.4** check the libary locally
```
python setyp.py install
$ python
>>> from pysqlite3 import dbapi2 as sqlite3 
>>> sqlite3.sqlite_version
'3.44.0'
```

**6.5** Indentify and copy the library binary
```
ls ~/sqlite344/pysqlite3-build/build/lib.linux-x86_64-cpython-310/pysqlite3/_sqlite3.cpython-310-x86_64-linux-gnu.so
```

This file you'll want to transfer from ec2 to your dev system, e.g.
```
scp -i "~/.aws/aws_ec2_keypair.pem" ec2-user@ec2-13-55-81-80.ap-southeast-2.compute.amazonaws.com:/home/ec2-user/sqlite344/pysqlite3/build/lib.linux-x86_64-cpython-310/pysqlite3/_sqlite3.cpython-310-x86_64-linux-gnu.so .
```

the `_sqllite3.*.so` file needs to be in the root of our django lamdba project. See [serverless.yml](serverless.yml) which defines the contents of our lambda package.