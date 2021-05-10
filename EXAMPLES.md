# Asset Warranty
This method receives data about warranty status.
Note: Asset-entitlements endpoint could receive up to 100 service tags during one request. 
### Fetch warranty in table view format
Several service tags should be separated with comma
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
Service tags(argument) could be passed from a file.
```
$ dell_api -fw /Users/ah/st_example.txt
OR w/o home 
$ dell_api -fw ~/st_example.txt
+-------------+---------------+------------+------------------------------+------------+
| Service Tag |    Country    |  Warranty  |            Remain            |  End Date  |
+-------------+---------------+------------+------------------------------+------------+
|   2345678   | United States |   Basic    |           Expired            | 2011-10-06 |
|   3456789   |     Sweden    |   Basic    |           Expired            | 2007-11-03 |
|   1234567   | United States | ProSupport | 4 years, 2 months and 0 days | 2025-07-10 |
+-------------+---------------+------------+------------------------------+------------+
# file contents 
$ cat st_example.txt
1234567
2345678
3456789
```
### Fetch warranty in JSON format
```
$ dell_api -fj ~/st_example.txt 
OR
$ dell_api -j 1234567,2345678,3456789      
[{'Service Tag': '2345678', 'Country': 'United States', 'Warranty': 'Basic', 'Remain': 'Expired', 'End Date': '2011-10-06'}, 
{'Service Tag': '3456789', 'Country': 'Sweden', 'Warranty': 'Basic', 'Remain': 'Expired', 'End Date': '2007-11-03'}, 
{'Service Tag': '1234567', 'Country': 'United States', 'Warranty': 'ProSupport', 'Remain': '4 years, 2 months and 1 days', 'End Date': '2025-07-10'}]
```
## [NetBox](https://github.com/netbox-community/netbox) case
```
$ nb -c device site=ACAE device_type.manufacturer.name=Dell | awk '{print $2}' | sed '1,2d;$d' > st_example.txt
$ dell_api -fw ~/st_example.txt
...
```
___
# Asset Details
This method receives data about part details. 
Note: Asset-components endpoint could receive only one service tag during one request.
### Fetch details in table view format
```
$ dell_api -d 1234567
OR
$ dell_api -d $(head -n1 ~/st_example.txt)
+------------+------------+--------------+--------------------------------------+----------------------------------+
| itemNumber | partNumber | partQuantity |           partDescription            |         itemDescription          |
+------------+------------+--------------+--------------------------------------+----------------------------------+
|   J6VTW    |   RX9D6    |      1       |     PRC,CML-U,I7-10510U,1.8G,4C      |    PWA,PLN,U,T,I7-10510U,3X10    |
|   J6VTW    |   JJ5RV    |      1       |           SW,BIOS,LAT,3X10           |    PWA,PLN,U,T,I7-10510U,3X10    |
|   J6VTW    |   YJCJD    |      1       |        DGPM,PCB,MKB,L,MB,UMA         |    PWA,PLN,U,T,I7-10510U,3X10    |
|  210-AVTI  |   4P9FX    |      1       |            INFO,HASH,BIOS            |        Dell Latitude 3510        |
|   0PYG4    |   7RMPY    |      1       | Tool,Syringe,Thermal Grease,1.5GRAMS | Service Kit,ALSOSHIP,7RMPY,06335 |
|   6VDX7    |   6VDX7    |      1       |    DIMM,8GB,3200,1RX8,8G,DDR4,NS     |  DIMM,8GB,3200,1RX8,8G,DDR4,NS   |
|   0PYG4    |   06335    |      1       |      PAD,THRM INTFC CLNG,SINGLE      | Service Kit,ALSOSHIP,7RMPY,06335 |
|   4P9FX    |   4P9FX    |      1       |            INFO,HASH,BIOS            |          INFO,HASH,BIOS          |
+------------+------------+--------------+--------------------------------------+----------------------------------+
```
### Fetch details in JSON format
```
$ dell_api -ad $(head -n1 ~/st_example.txt)
{
   "id":115282514,
   "serviceTag":"1234567",
   "orderBuid":11,
   "shipDate":"2020-10-19T20:10:01.409Z",
   "productCode":">/108",
   "localChannel":"73",
   "productId":"None",
   "productLineDescription":"LATITUDE 3510",
   "productFamily":"None",
   "systemDescription":"None",
   "productLobDescription":"Latitude",
   "countryCode":"US",
   "duplicated":true,
   "invalid":false,
   "components":[
   {
         "itemNumber":"J6VTW",
         "partNumber":"RX9D6",
         "partQuantity":1,
         "partDescription":"PRC,CML-U,I7-10510U,1.8G,4C",
         "itemDescription":"PWA,PLN,U,T,I7-10510U,3X10"
      },
      {
         "itemNumber":"J6VTW",
         "partNumber":"YJCJD",
         "partQuantity":1,
         "partDescription":"DGPM,PCB,MKB,L,MB,UMA",
         "itemDescription":"PWA,PLN,U,T,I7-10510U,3X10"
      },
      ...
   ]
}
```
