# $ dell_api
A command-line interface (CLI) for fetching Dell APIs ([TechDirect](https://techdirect.dell.com/portal/AboutAPIs.aspx) asset warranty service) data and present them in a human-friendly view.

Based on given service tag the application provides the following information:
- Warranty status details, such as: service tag assigned country, warranty level, warranty time remaining and end date.
- Part details
# Client_ID & Client_Secret
User has to retrieve “client_id” and ”client_secret” from TechDirect API [portal](https://techdirect.dell.com/portal.30/Login.aspx).

From Dell API Outh doc - ***API key = Client ID***

This data is used for receiving an access token for the Resource (API)

# Installation 
`pip install dell-warranty-api`

OR you can install the application manually. Example with virtual environment:
```
https://github.com/karma-git/dell_warranty_status_api.git && cd dell_warranty_status_api;
python3 -m venv venv;
source venv/bin/activate;
python -m pip install -r requirements.txt;
python dell_api/__main__.py -h;
# OR
python -m dell_api -h;  
```
____
# Usage 
You'll be asked to insert Client ID and Client Secret during the first launch.

Secrets will be stored into your home directory in the file ***secrets.ini***.
Also, when you use application it generates ***access token (OAuth - it is valid only for one hour)*** and saves it in the hidden file ***.cache.json*** inside your home directory.
```
$ dell_api -w 1234567
2021-05-10 06:48:54.521 | WARNING  | dell_api.__main__:_load_secrets:73 - Secrets file is not exist! Creating ...
Please specify client_id:
Please specify client_secret:
```
# Simple example
```
$ dell_api -w 1234567,2345678,3456789
+-------------+---------------+------------+------------------------------+------------+
| Service Tag |    Country    |  Warranty  |            Remain            |  End Date  |
+-------------+---------------+------------+------------------------------+------------+
|   2345678   | United States |   Basic    |           Expired            | 2011-10-06 |
|   3456789   |     Sweden    |   Basic    |           Expired            | 2007-11-03 |
|   1234567   | United States | ProSupport | 4 years, 2 months and 0 days | 2025-07-10 |
+-------------+---------------+------------+------------------------------+------------+
```
Check more usage cases -> [examples](https://github.com/karma-git/dell_warranty_status_api/blob/master/EXAMPLES.md)


                                                                
