#!/usr/bin/env python
# -*- coding: utf-8 -*-
import collections
import os

from datetime import datetime, timedelta
import re
import gzip
import json
import requests
import csv
import urllib3
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

import io
import zipfile
import logging
import boto3
import gc

from dotenv import load_dotenv
load_dotenv()

# Method to process s3 bucket, and save to cloud storage
# All files within the data directory will be process then moved to a done folder.
def processS3():
    # Connect to S3
    s3client = boto3.resource('s3',
        aws_access_key_id=os.environ['s3accessid'].strip(),
        aws_secret_access_key=os.environ['s3secretkey'].strip()
        )
    s3bucketname = os.environ['s3bucketname'].strip()
    s3bucket = s3client.Bucket(s3bucketname)
    dateprefix = datetime.utcnow().strftime('%Y-%m-%d_%H%M%S')
    outputlog = False
    if ('outputlog' in os.environ) and (os.environ['outputlog'].strip().lower() in ['true', '1', 't', 'y', 'yes']):
        outputlog = True
    convertcsv = True
    if ('convertcsv' in os.environ) and (os.environ['convertcsv'].strip().lower() in ['false', '0', 'f', 'n', 'no']):
        convertcsv = False

    s3prefix = ''
    if (os.environ['s3path'].strip()):
        s3prefix = os.environ['s3path'].rstrip('/').lstrip('/') + '/'
    segment_id = ''
    segmentprefix = os.environ['segmentid'].strip().rstrip('/').lstrip('/')
    if (os.environ['s3exportpath'].strip()):
        segmentprefix += '/' + os.environ['s3exportpath'].rstrip('/').lstrip('/')
    s3prefix += "segment-export/{}/".format(segmentprefix)
    s3objs = s3bucket.objects.filter(Prefix=s3prefix)
    # Generate header an output string variable
    brazefields = [sf.strip() for sf in os.environ['segmentexportfields'].split(',')]
    fileprefix ="./"
    if ('outputpath' in os.environ) and  (os.environ['outputpath'].strip()):
        fileprefix += os.environ['outputpath'].strip().rstrip('/').lstrip('/') + '/'
    exportfile = open("{}{}_{}_results.csv".format(fileprefix,os.environ['outputname'].strip(),dateprefix), "w")
    if outputlog: logfile = open("{}{}_{}_log.csv".format(fileprefix,os.environ['outputname'].strip(),dateprefix), "w")

    if convertcsv:
        csvwriter = csv.writer(exportfile, delimiter=',')
        exportfile.write(','.join(brazefields) + "\n")

    objcount = 1
    if outputlog: logfile.write("path,file,result,row,error\n")
    for s3obj in s3objs:
        if '.zip' in s3obj.key:
            gc.collect()
            buffer = io.BytesIO(s3obj.get()["Body"].read())
            with zipfile.ZipFile(buffer) as exports:
                for brazefiles in exports.infolist():
                    if '.txt' in brazefiles.filename:
                        print ("Processing file {}: {}".format(objcount, brazefiles.filename))
                        with exports.open(brazefiles, 'r') as brazefile:
                            linecount = 0
                            errcount = 0
                            for line in brazefile:
                                linecount += 1
                                try:
                                    line_utf8 = line.decode("utf-8").rstrip()
                                    if convertcsv:
                                        record_json = json.loads(line_utf8)
                                        record = []
                                        for sfv in brazefields:
                                            if sfv in record_json:
                                                record.append(record_json[sfv])
                                            else:
                                                if 'custom_attributes' in record_json:
                                                    if sfv in record_json['custom_attributes']:
                                                        record.append(record_json['custom_attributes'][sfv])
                                                    else:
                                                        record.append(None)
                                                else:
                                                    record.append(None)
                                        csvwriter.writerow(record)
                                    else:
                                        exportfile.write(line_utf8 + "\n")
                                except Exception as e :
                                    logging.warning("Parse error in {} line {}: {}\n\tError: {}"
                                        .format(brazefiles.filename, linecount, line_utf8, e))
                                    if outputlog: logfile.write("{},{},{},{},{}\n".format(s3obj.key,brazefiles.filename,e,linecount,line_utf8))
                                    errcount += 1
                                    continue
                            if outputlog: logfile.write("{},{},{},{},{}\n".format(s3obj.key,brazefiles.filename,"Processed",linecount,errcount))
                        objcount += 1
            buffer.close()
    if outputlog: logfile.close()
    exportfile.close()
    return exportfile

if __name__ == '__main__':
    processS3()