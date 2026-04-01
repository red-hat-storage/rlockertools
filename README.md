Useful tools to work with [Rlocker project API](https://github.com/red-hat-storage/rlocker.git)


# Quick Start

## Normal installation

```bash
pip install rlockertools
```

## Setup

```bash
git clone https://github.com/red-hat-storage/rlockertools.git
cd rlockertools
python -m venv venv
source venv/bin/activate
pip install ./
rlock --help
```

usage: rlock [-h] --server-url SERVER_URL --token TOKEN [--release] [--lock] [--resume-on-connection-error] [--signoff SIGNOFF]
             [--priority PRIORITY] [--search-string SEARCH_STRING] [--link LINK] [--interval INTERVAL] [--attempts ATTEMPTS]

optional arguments:
  -h, --help            show this help message and exit
  --server-url SERVER_URL
                        The URL of the Resource Locker Server
  --token TOKEN         Token of the user that creates API calls
  --release             Use this argument to release a resource
  --lock                Use this argument to lock a resource
  --resume-on-connection-error
                        Use this argument in case you don't want to break queue execution in the middle of waiting for queue status
                        being FINISHED
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
rlock --lock --server-url=your.rlocker.instance.com --token=YOURTOKEN --search-string=nameorlabel --signoff=YOURUNIQUESIGNOFF --priority=3 --interval=15 --attempts=15
```

### To release a locked resource (filtration by signoff only)
```bash
rlock --release --server-url=your.rlocker.instance.com --token=YOURTOKEN --signoff=YOURUNIQUESIGNOFF
```

## Logging Configuration

The rlockertools library uses Python's standard logging module. By default, logging is disabled (NullHandler). To enable logging output, configure it in your application:

### Basic Configuration

```python
import logging

# Configure logging at the start of your application
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### Advanced Configuration

```python
import logging

# Create a logger for rlockertools
logger = logging.getLogger('rlockertools')
logger.setLevel(logging.DEBUG)

# Create console handler with a higher log level
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)

# Create formatter and add it to the handler
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)

# Add the handler to the logger
logger.addHandler(ch)
```

### Log Levels

- `DEBUG`: Detailed information, typically for diagnosing problems (includes API responses)
- `INFO`: General informational messages (connection status, resource operations)
- `WARNING`: Warning messages (retries, timeouts)
- `ERROR`: Error messages (failures, connection errors)
