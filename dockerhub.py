#!/usr/bin/env python3
import requests
import json
import collections
import time
import os
import re
import argparse


DOCKERHUB_URL = "https://hub.docker.com/v2"
time_format = '%Y-%m-%dT%H:%M:%S.%fZ'
os.environ['TZ'] = 'UTC'
images = {}
AUTH_SERVICE = "registry.docker.io"
AUTH_OFFLINE_TOKEN = "1"
AUTH_CLIENT_ID = "shell"
AUTH_DOMAIN = "https://auth.docker.io"
API_DOMAIN = "https://registry-1.docker.io"


def epoch_converter(timestamp):
    epoch = int(time.mktime(time.strptime(timestamp, time_format)))
    return epoch


def get_hub_token(username, password, path):
    url = DOCKERHUB_URL + path
    payload = {
        "username": username,
        "password": password
    }
    r = requests.post(
        url,
        data=payload
    )
    if r.status_code != 200:
        print("Bad Status: %i" % (r.status_code))
        print("Returned: %s" % (r.text))
        exit(-2)
    else:
        return json.loads(r.text)


def dockerhub_api(path, token, method):
    url = DOCKERHUB_URL + path
    if method is "get":
        header = {
            "content-type": "application/json",
            "Authorization": "Bearer " + token,
        }
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
        header = {
            "Accept": "application/json",
            "Authorization": "JWT " + token,
        }
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
    results = data['results']
    for tag in results:
        if re.match("\d+", tag['name']):
            print("matched tag with re to build-number(s): %s" % (tag['name']))
            images[tag['name']] = {
                "tag": tag['name'],
                "last_modified": epoch_converter(tag['last_updated']),
                "image_id": tag['image_id']
            }
    return True


def parse_tags(images, max_images, token):
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
            if del_counter < images_to_delete and images[k]['tag'] != 'latest':
                del_counter += 1
                print("\tDeleting Tag: %s" % (images[k]['tag']))
                dockerhub_api("/repositories/" + args.org + "/" + args.repo + "/tags/" + images[k]['tag'] + "/", token, "delete")
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--repo',
        default=os.environ['REPO'],
        help="dockerhub repo"
    )
    parser.add_argument(
        '--org',
        default=os.environ['ORG'],
        help="org"
    )
    parser.add_argument(
        '--username',
        default=os.environ['DOCKERHUB_USER'],
        help="username"
    )
    parser.add_argument(
        '--password',
        default=os.environ['DOCKERHUB_PASSWORD'],
        help="password"
    )
    parser.add_argument(
        '--max_images',
        default=int(os.environ['MAX_IMAGES']),
        help="max images to keep"
    )
    args = parser.parse_args()
    args.max_images = int(args.max_images)
    auth_scope = "repository:" + args.org + "/" + args.repo + ":push,pull"
    if not args.username or not args.password or not args.repo or not args.org or not args.max_images:
        print("Args are missing")
        exit(-3)
    if args.max_images > 0:
        token = get_hub_token(args.username, args.password, "/users/login/")['token']
        get_tags(
            dockerhub_api("/repositories/" + args.org + "/" + args.repo + "/tags/", token, "get")
        )
        if len(images) > 0:
            parse_tags(images, args.max_images, token)
    else:
        print("Value less than '1' is not allowed")
        exit(-1)
    exit(0)
