#!/usr/bin/env python3

from argparse import ArgumentParser
from os import path
from pprint import pformat
from sys import exit
from urllib.error import HTTPError
import base64
import datetime
import json
import urllib.request
import logging

def main(filename: str, url: str, credentials: str, subdomains: list, dbg: bool, shush: bool, isCron: bool):
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
    logging.debug(f"    Zone File: {filename}")
    logging.debug(f"          Url: {url}")
    logging.debug(f"  Credentials: {credentials}")
    logging.debug(f"   Subdomains: {subdomains}")
    logging.debug(f"        Debug: {dbg}")
    logging.debug(f"        Quiet: {shush}")

    if filename[:2] == "..":
        zoneFilePath = path.abspath(path.dirname(path.abspath(__file__))
                                    + "/"
                                    + filename)
    else:
        zoneFilePath = path.abspath(filename)

    logging.debug(f"Fetching {zoneFilePath}")

    zoneFile = GetZoneFile(zoneFilePath)
    
    ipToTest = GetNewIPAddress(url, credentials)
    
    logging.debug(f"IPs to test:\n{pformat(ipToTest)}")

    updatedZoneFile = UpdateZoneFile(zoneFile, ipToTest, subdomains)
    
    logging.debug(f"Updated zone file:\n{pformat(updatedZoneFile)}")
    
    if updatedZoneFile is zoneFile:        
        retval = 1
        logging.info("Zone file unchanged, exiting.")
    else:
        retval = 0
        logging.info("Zone file changed, writing new zone file!")
        WriteZoneFile(zoneFilePath, updatedZoneFile)
    exit(retval)

def GetZoneFile(filename: str):
    try:
        with open(filename, 'r') as file:
            fileContents = file.readlines()
    except FileNotFoundError:
        raise
    return fileContents


def WriteZoneFile(filename: str, contents: list):
    with open(filename, 'w') as file:
        file.writelines(contents)


def GetNewIPAddress(url: str, credentials: str):

    try:
        headers = {"Authorization": "Basic " + base64.b64encode(credentials.encode("ascii"))
                                                     .decode("ascii")}
        with urllib.request.urlopen(
            urllib.request.Request(url, headers=headers, method="GET")) as response:
            responseBody = response.read()
            logging.debug(f"Response Body:\n{responseBody}")
            newIPs = json.loads(responseBody)
    except HTTPError as err:
        if err.code == 401:
            logging.error("HTTP Authentication failed. Quitting")
            exit(2)

    return newIPs


def UpdateZoneFile(zoneFile, ipsToTest, subdomains):
    newZoneFile = []
    zoneFileUpdated = False

    foundSubdomain = False
    if len([item for item in ipsToTest if item["subdomain"] in subdomains]) > 0:
        foundSubdomain = True

    if not foundSubdomain:
        logging.debug("Subdomain not found in list from server")
        return zoneFile
    
    updatedSerial = False
    now = datetime.datetime.now()
    newSerial = "".join([str(now.year)
                         , str(now.month).zfill(2)
                         , str(now.day).zfill(2)
                        ])
    for line in zoneFile:
        lineParts = line.split()
        
        if line[0] == ";" or len(lineParts) == 0:
            newZoneFile.append(line)
            continue
        
        if len(lineParts) == 1 and not updatedSerial:
            if str(lineParts[0]).startswith(newSerial):
                # we need to update the serial number
                newSerial += str(int(str(lineParts[0])[-2:]) + 1).zfill(2)
            else:
                newSerial += "01"
            updatedSerial = True
            newZoneFile.append(line.replace(lineParts[0], newSerial))
    
        elif lineParts[0] in subdomains:
            logging.debug("Found a subdomain we want to change!")
            newIP = next(item for item in ipsToTest if item["subdomain"] == lineParts[0])
            newZoneFile.append(line.replace(lineParts[3], newIP["ip"]))
            if newZoneFile[-1] != line:
                zoneFileUpdated = True
        
        else:
            newZoneFile.append(line)
    
    if zoneFileUpdated:
        return newZoneFile
    else:
        return zoneFile


if __name__ == "__main__":
    parser = ArgumentParser(description="Updates a BIND9/NSD zone file's subdomains")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-v", "--verbose", action="store_true", help="Show verbose output")
    group.add_argument("-q", "--quiet", action="store_true", help="Suppress all output")
    parser.add_argument("-u", "--url", help="URL from which to fetch the data")
    parser.add_argument("-c", "--credentials", help="Credentials to use in the HTTP Authorization header (username:password)")
    parser.add_argument("-s", "--subdomains", help="Subdomains to update")
    parser.add_argument("-t", "--timer-job", action="store_true", help="Indicate that this is running from a cron job/systemd timer")
    parser.add_argument("zonefile", help="Zone file to update")
    args = parser.parse_args()
    main(args.zonefile, args.url, args.credentials, str(args.subdomains).split(","), args.verbose, args.quiet, args.timer_job)