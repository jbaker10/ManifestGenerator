#!/usr/bin/python

import json
import subprocess
import sys
import os
import plistlib
import requests

###### Global Variables ######
airwatch_server = '' ## Enter your AirWatch server here, for example https://airwatch.com
b64auth = '' ## Base 64 Encoded AirWatch Username and Password here
aw_tenant_code = '' ## Enter the AirWatch API Key from your server here
request_headers = {'aw-tenant-code':'%s' % aw_tenant_code, 'Accept':'application/json', 'Authorization':'Basic %s' % b64auth}
airwatch_devices = []
device_dict = {}
manifest_dict = {}
munki_dir = '/var/www/html/munki_repo/' ## Need the full path to the munki_repo as it will look for the 'manifests' dir within that
manifests_dir = '%s/manifests/' % munki_dir
###### Global Variables ######

r = requests.get('%s/api/mdm/devices/search' % airwatch_server, headers=request_headers)

try:
    parsed_json = r.json()
except ValueError:
    print "\nThe API call failed. Please check your username and password and try again\n"
    sys.exit()

for i in xrange(0, len(parsed_json['Devices'])):
    client_dict = {}
    client_dict['SerialNumber'] = parsed_json['Devices'][i]['SerialNumber']
    client_dict['FriendlyName'] = parsed_json['Devices'][i]['DeviceFriendlyName']
    client_dict['AssetNumber'] = parsed_json['Devices'][i]['AssetNumber']
    client_dict['Username'] = parsed_json['Devices'][i]['UserName']
    airwatch_devices.append(client_dict)

current_device_manifests = os.listdir(manifests_dir)

for manifest in current_device_manifests:
    manifest_dict[manifest] = 1

for device in airwatch_devices:
    try:
        if manifest_dict[device['SerialNumber']]:
            print "Manifest for serial [%s] already exists, skipping" % device['SerialNumber']
    except KeyError:
        if 'Staging' in device['Username']:
            print "Device [%s] has not been fully provisioned yet, skipping manifest creation" % device['SerialNumber']
        elif len(device['AssetNumber']) > 8:
            print "Device [%s] Asset tag has not been updated yet, skipping manifest creation" % device['SerialNumber']
        else:
            print "\tCreating a manifest for device"
            manifest_template = {}
            manifest_template['catalogs'] = ['production']
            manifest_template['included_manifests'] = ['site_default']
            manifest_template['managed_installs'] = []
            manifest_template['optional_installs'] = []
            manifest_template['display_name'] = device['FriendlyName']
            manifest_template['user'] = device['Username']
            plistlib.writePlist(manifest_template, '%s/%s' % (manifests_dir, device['SerialNumber']))
