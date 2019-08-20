#!/usr/bin/env python3
import requests
import json
import re
import collections
import time
import os
import argparse


QUAY_URL = "https://quay.io/api/v1"
time_format = '%a, %d %b %Y %H:%M:%S %z'
os.environ['TZ'] = 'UTC'
images = {}


def epoch_converter(timestamp):
    epoch = int(time.mktime(time.strptime(timestamp, time_format)))
    return epoch


def quay_api(url, token, method):
    header = {
        "content-type": "application/json",
        "Authorization": "Bearer " + token,
    }
    if method is "get":
        r = requests.get(
            url,
            headers=header
        )
        if r.status_code != 200:
            print("Bad Status: %i" % (r.status_code))
            print("Returned: %s" % (r.text))
            exit(-2)
        else:
            return json.loads(r.text)
    if method is "delete":
        r = requests.delete(
            url,
            headers=header
        )
        if r.status_code != 204:
            print("Bad Status: %i" % (r.status_code))
            print("Returned: %s" % (r.text))
            exit(-2)
        else:
            return True


def get_tags(data):
    name = data['name']
    namespace = data['namespace']
    print("checking tags in -> quay.io/%s/%s" % (namespace, name))
    for tag in data['tags']:
        if re.match("\d+", tag):
            print("matched tag with re to build-number(s): %s" % (data['tags'][tag]['name']))
            images[tag] = {
                "tag": data['tags'][tag]['name'],
                "last_modified": epoch_converter(data['tags'][tag]['last_modified']),
                "image_id": data['tags'][tag]['image_id']
            }
    return True


def delete_tags(images, max_images):
    if len(images) > max_images:
        del_counter = 0
        images_to_delete = len(images) - max_images
        print("\t> Delete %i tags" % (images_to_delete))
        od = collections.OrderedDict(
            sorted(
                images.items(),
                key=lambda x: x[1]['last_modified'],
                reverse=False
            )
        )
        for k, v in od.items():
            if del_counter < images_to_delete and images[k]['tag'] != 'latest' and images[k]['tag'] != 'master' and images[k]['tag'] != 'staging' and images[k]['tag'] != 'deployed' and "branch." not in images[k]['tag']:
                del_counter += 1
                if quay_api(QUAY_URL + "/repository/" + args.org + "/" + args.repo + "/tag/" + images[k]['tag'], args.token, "delete"):
                    print("\tDeleted Tag: %s" % (images[k]['tag']))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--repo',
        default=os.environ['REPO'],
        help="Quay repo"
    )
    parser.add_argument(
        '--org',
        default=os.environ['ORG'],
        help="blockstack"
    )
    parser.add_argument(
        '--token',
        default=os.environ['TOKEN'],
        help="token"
    )
    parser.add_argument(
        '--max_images',
        default=int(os.environ['MAX_IMAGES']),
        help="max images to keep"
    )
    args = parser.parse_args()
    if not args.token or not args.repo or not args.org or not args.max_images:
        print("Args are missing")
        exit(-3)
    if args.max_images > 0:
        get_tags(
            quay_api(QUAY_URL + "/repository/" + args.org + "/" + args.repo, args.token, "get")
        )
        if len(images) > 0:
            delete_tags(images, args.max_images)
    else:
        print("Value of 0 is not allowed")
        exit(-1)
    exit(0)
