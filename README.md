Useful tools to work with [Rlocker project API](https://github.com/jimdevops19/rlocker.git)

# Description
    
It consists of two main modules:

- `rlockertools.resourcelocker`: Utilities to work with Lockable Resources, lock and release
- `rlockertools.exceptions`: Custom Exceptions for lockable resources

# Quick Start
 
## Normal installation

```bash
pip install rlockertools
```

## Setup
```bash
git clone https://github.com/jimdevops19/rlockertools.git
cd rlockertools
python -m venv venv
source venv/bin/activate
python setup.py install 
rlock --help
```
```
usage: rlock [-h] --server-url SERVER_URL --token TOKEN [--release] [--lock] [--signoff SIGNOFF] [--priority PRIORITY] [--search-string SEARCH_STRING] [--link LINK] [--interval INTERVAL]
             [--attempts ATTEMPTS]

optional arguments:
  -h, --help            show this help message and exit
  --server-url SERVER_URL
                        The URL of the Resource Locker Server
  --token TOKEN         Token of the user that creates API calls
  --release             Use this argument to release a resource
  --lock                Use this argument to lock a resource
  --signoff SIGNOFF     Use this when lock=True, locking a resource requires signoff
  --priority PRIORITY   Use this when lock=True, specify the level of priority the resource should be locked
  --search-string SEARCH_STRING
                        Use this when lock=True, specify the lable or the name of the lockable resource
  --link LINK           Use this when lock=True, specify the link of the CI/CD pipeline that locks the resource
  --interval INTERVAL   Use this when lock=True, how many seconds to wait between each call while checking for a free resource
  --attempts ATTEMPTS   Use this when lock=True, how many times to create an API call that will check for a free resource
```

## Usage Examples

### To add a queue for locking a resource

```bash
rlock --lock --server-url=your.rlocker.instance.com --token=YOURTOKEN --signoff=YOURUNIQUESIGNOFF --priority=3 --interval=15 --attempts=15
```

### To release a locked resource (filtration by signoff only)
```bash
rlock --release --server-url=your.rlocker.instance.com --token=YOURTOKEN --signoff=YOURUNIQUESIGNOFF
```