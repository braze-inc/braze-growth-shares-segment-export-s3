# Braze User Export Extract from AWS S3
This is a python 3 script which simplifies the process of getting Braze Segment export data from AWS S3, combined them, and converting it into a csv file.

## Requirements
The following are required:
* Access Id and Secret Key from [Amazon AWS S3](https://console.aws.amazon.com/console/) with read permission to the necessary bucket
* Access to the Braze dashboard with a segment already created for the desire audience
* A [Braze API key](https://www.braze.com/docs/api/api_key/) with segment export permissions.
* [python3](https://www.python.org/) installed
	* Optional, [venv](https://docs.python.org/3/library/venv.html) installed

## Process Steps
The following is an outline of the process:
* Make an API call to the [Braze User by Segment Export](https://www.braze.com/docs/api/endpoints/export/user_data/post_users_segment/) endpoint using a predefined [segment](https://www.braze.com/docs/user_guide/engagement_tools/segments/creating_a_segment/).
	* Example Curl request: ```curl --location --request POST 'https://rest.iad-01.braze.com/users/export/segment' \
--header 'Content-Type: application/json' \
--header 'Authorization: Bearer [API-KEY]' \
--data-raw '{
    "segment_id" : "[SEGMENT-ID],
    "fields_to_export" : ["external_id","email","first_name"]
}
'```
	* Example Response: ``` {
    "object_prefix": "[export_object_prefix]",
    "url": null,
    "message": "success"
} ```
* Edit the `.env` with the credentials if not already done
	* The `s3bucketname` and `s3path` maps to the `AWS S3 Bucket Name` and `AWS S3 Bucket Folder` respectively in the AWS S3 partner setup.
	* ![braze_s3_setup](/img/braze_s3_setup.png)
* Edit the `.env` file with the `segment_id`
	* Example:  `segmentid: "3jah21m-f10b-45c1-8a29-mm3mamaj"`
* Optionally, copy the `object_prefix` from the api call to filter the results
	* Edit `.env` file's `s3exportpath` value to filter for the `object_prefix`
	* Format will be `/[YYYY-MM-DD]/[export_object_prefix]`
	* If set to blank `""`, then all output files in the folder will be processed
	* If set to today `/[YYYY-MM-DD]`, all exports for that date will be processed
* Edit the `.env` with any custom `segmentexportfields` for output if using `convertcsv` ie `external_id,email`
* Run the script using `python3 process_s3.py` to read the export and convert it a csv format.
 	* Results are saves it to the `outpath`
	* If `convertcsv` is disabled, then results will just be combined
* If `outputlog` is enabled, then a log file will also be generate with additional information

# Setup instructions
To run the script, [python3](https://www.python.org/) is required to be installed. Optionally, having [venv](https://docs.python.org/3/library/venv.html) installed is recommended.

## Configuration
The easiest way to setup the configuration is to create a `.env` file in the same path as the script. See [.sample_env](.sample_env) for an example to copy and `rename`.

### Configuration Settings
|Setting|Description|Example value|
|----|----|----|
|s3accessid|AWS S3 Access ID|s3access_abc123|
|s3secretkey|AWS S3 Secret Key|s3key_abc123|
|s3bucketname|AWS Bucket Name|s3bucketname|
|s3path|AWS Bucket Path|s3_bucket_folder|
|segmentid|Braze Segment Id|braze_export_segment_id|
|s3exportpath|S3 Export path. Braze generates this using export date `YYYY-MM-DD` and the `export_object_prefix` from the api export. Use this to filter the results. Some `/[YYYY-MM-DD]/` or `/` may also be use but be aware of the data that would be filtered when using this.|"/[YYYY-MM-DD]/[export_object_prefix]"|
|segmentexportfields|Fields to convert from json to csv comma separated|external_id,attr_1,attr_2|
|convertcsv|Boolean - true, enable to convert the json to csv. Otherwise the files will just be combined. Use with `segmentexportfields`.|true|
|outputpath|Folder to place the results in. Make sure the folder exist.|done|
|outputname|Output File prefix name|braze_export|
|outputlog|Boolean - false, set to output an log file for additional error checking|true|

# Running the Script
To run the script use `python3 process_s3.py`. This will read each export zip file from s3, convert from json format to csv(unless `convertcsv` is disabled), and place the resulting file into the `outputpath` folder.

## Install dependency
Use `pip3 install -r requirements.txt` to installed the dependencies. See [Using Virtual environment](#using-virtual-environment) below to avoid dependency issues.

## Using Virtual environment
To avoid dependency issues, it's recommend to use venv.
* `python3 -m venv ./.export` - creates the virtual environment
* `source .export/bin/activate` - activate the virtual environment
* `pip3 install -r requirements.txt` - install dependency if not already installed
* `python3 process_s3.py` - runs the script for processing the s3 bucket
