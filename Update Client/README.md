# Auto update client

## Requirements

### Dependent packages:
* furl: `pip install furl`

## Usage
```
usage: main.py [-h] [-v | -q] -u URL -c CREDENTIALS -s SUBDOMAINS [-t]

Initiates an auto-update of a TF-Dyn controlled subdomain

optional arguments:
  -h, --help            show this help message and exit
  -v, --verbose         Show verbose output
  -q, --quiet           Suppress all output
  -u URL, --url URL     URL to trigger the update
  -c CREDENTIALS, --credentials CREDENTIALS
                        Credentials to use in the HTTP Authorization header (username:password)
  -s SUBDOMAINS, --subdomains SUBDOMAINS
                        Subdomains to update separated by a comma ","
  -t, --timer-job       Indicate that this is running from a cron job/systemd timer
```