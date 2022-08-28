#!/usr/bin/env python3

from argparse import ArgumentParser
from urllib.error import HTTPError
from furl import furl
import base64
import json
import urllib.request
import logging

def main(url: str, credentials: str, subdomains: list, dbg: bool, shush: bool, isCron: bool):
    level = logging.INFO
    if dbg:
        level = logging.DEBUG
    if shush:
        level = logging.CRITICAL

    fmt = '%(asctime)s [%(levelname)s] %(message)s'

    if isCron:
        fmt = '[%(levelname)s] %(message)s'

    logging.basicConfig(level=level, format=fmt)

    logging.debug(f"Starting application from {__file__}")
    logging.debug("INPUTS:")
    logging.debug(f"          Url: {url}")
    logging.debug(f"  Credentials: {credentials}")
    logging.debug(f"   Subdomains: {subdomains}")
    logging.debug(f"        Debug: {dbg}")
    logging.debug(f"        Quiet: {shush}")

    results = []
    for subdomain in subdomains:
        results.append(TriggerIPUpdate(url, credentials, subdomain))


def TriggerIPUpdate(url: str, credentials: str, subdomain: str):
    try:
        headers = {"Authorization": "Basic " + base64.b64encode(credentials.encode("ascii"))
                                                     .decode("ascii")}

        f = furl(url)
        f.args['action'] = 'auto-update'
        f.args['subdomain'] = subdomain
        url = f.url
        logging.debug(f"Final URL: {url}")

        result = type('', (), {})()
        with urllib.request.urlopen(
            urllib.request.Request(url, headers=headers, method="GET")) as response:
            responseBody = response.read()
        # logging.debug(f"Response Body:\n{responseBody}")
        # logging.debug(f"Response Code: {response.getcode()}")
        # if response.getcode() == 304:
        #     result = type('', (), {})()
        #     result.subdomain = subdomain
        #     result.ip = ''
        #     result.result = 304
        # else:
            result = json.loads(responseBody)
    except HTTPError as err:
        if err.code == 401:
            logging.error("HTTP Authentication failed. Quitting")
            exit(2)
        if err.code == 304:
            logging.debug("Received HTTP 304-NOT MODIFIED")
            result = type('', (), {})()
            result.subdomain = subdomain
            result.ip = ''
            result.result = 304
    return result

if __name__ == "__main__":
    parser = ArgumentParser(description="Initiates an auto-update of a TF-Dyn controlled subdomain")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-v", "--verbose", action="store_true", help="Show verbose output")
    group.add_argument("-q", "--quiet", action="store_true", help="Suppress all output")
    parser.add_argument("-u", "--url", help="URL to trigger the update")
    parser.add_argument("-c", "--credentials", help="Credentials to use in the HTTP Authorization header (username:password)")
    parser.add_argument("-s", "--subdomains", help="Subdomains to update")
    parser.add_argument("-t", "--timer-job", action="store_true", help="Indicate that this is running from a cron job/systemd timer")
    args = parser.parse_args()
    main(args.url, args.credentials, str(args.subdomains).split(","), args.verbose, args.quiet, args.timer_job)