import configparser
import requests
import json
import datetime
import os
import sys
from pathlib import Path
import pycountry
import re
from prettytable import PrettyTable
import argparse
from getpass import getpass
from humanize import precisedelta
from loguru import logger
import pretty_errors

pretty_errors.configure(
    line_number_first=True,
    stack_depth=1,
    display_link=True,
)

logger.remove(0)
# logger.add(sys.stderr, level="DEBUG")
#logger.add(sys.stderr, level="CRITICAL")


class TooManyServiceTags(Exception):
    pass


class ServiceTagNotValid(Exception):
    pass


class SecretsInvalid(Exception):
    pass


class BearerAuth(requests.auth.AuthBase):
    def __init__(self, token):
        self.token = token

    def __call__(self, r: requests.models.PreparedRequest) -> requests.models.PreparedRequest:
        try:
            r.headers["authorization"] = "Bearer " + self.token
        except TypeError:
            os.remove(f'{str(Path.home())}/.cache.json')
            logger.info('cache file (with bad access token) has just been deleted')
        finally:
            # retry again
            try:
                r.headers["authorization"] = "Bearer " + self.token
            except Exception as e:
                logger('Something goes wrong! Original error {}', e)
                raise SecretsInvalid
        return r


class DellApi:

    def __init__(self):
        self._home = str(Path.home())

    def _create_secrets(self):
        config = configparser.ConfigParser()
        ci = getpass('Please specify client_id: ')
        cs = getpass('Please specify client_secret: ')
        # TODO: validate ci and cs
        config['dell api'] = {'client_id': ci,
                              'client_secret': cs}

        with open(f'{self._home}/secrets.ini', 'w') as configfile:
            config.write(configfile)

    def _load_secrets(self) -> tuple:
        if not os.path.isfile(f"{self._home}/secrets.ini"):
            logger.warning(f"Secrets file is not exist! Creating ...")
            self._create_secrets()

        config = configparser.ConfigParser()
        logger.debug('Files near to {} -> {}', sys.argv[0], os.listdir(self._home))
        config.read(f'{self._home}/secrets.ini')
        return config.get('dell api', 'client_id'), config.get('dell api', 'client_secret')

    def _load_access_token(self) -> dict:
        with open(f"{self._home}/.cache.json") as j:
            logger.debug('Loading access token from cache')
            return json.load(j)

    def _generate_access_token(self):
        ci, cs = self._load_secrets()  # client id; client secret
        client_auth = requests.auth.HTTPBasicAuth(ci, cs)
        response = requests.post('https://apigtwb2c.us.dell.com/auth/oauth/v2/token',
                                 auth=client_auth,
                                 data={"grant_type": "client_credentials"})

        access_token = response.json().get("access_token")
        timestamp = datetime.datetime.now()
        data = {'access_token': access_token,
                'timestamp': timestamp.isoformat()}

        with open(f'{self._home}/.cache.json', 'w') as j:
            json.dump(data, j)
            logger.debug('The access token has just received and saved to cache')

    def _is_token_valid(self, iso_date_string: str) -> bool:
        when_generated = datetime.datetime.fromisoformat(iso_date_string)
        now = datetime.datetime.now()
        diff_seconds = (now - when_generated).seconds
        logger.debug('Token valid for one hour, created at -> {}', when_generated)
        if diff_seconds >= 3600:
            return False
        else:
            return True

    def _get_access_token(self) -> str:
        if not os.path.isfile(f"{self._home}/.cache.json"):
            logger.debug('Did not find cache file')
            self._generate_access_token()

        data = self._load_access_token()
        valid = self._is_token_valid(data['timestamp'])

        if valid:
            logger.debug('Access token is valid')
            return data['access_token']

        elif not valid:
            logger.debug('Access token is invalid, receiving new')
            self._generate_access_token()
            return self._load_access_token()['access_token']

    def asset_warranty(self, service_tags: list) -> list[dict]:
        if len(service_tags) > 99:
            raise TooManyServiceTags(f"Expected less then 100, got {len(service_tags)}")
        else:
            st = ','.join(service_tags)
        auth = BearerAuth(self._get_access_token())
        api_endpoint = f'https://apigtwb2c.us.dell.com/PROD/sbil/eapi/v5/asset-entitlements?servicetags={st}'
        response = requests.get(api_endpoint, auth=auth)
        answer = response.json()
        return answer

    def print_asset_warranty(self, service_tags: list):
        print(self.asset_warranty(service_tags))

    def asset_details(self, service_tag: str) -> dict:
        if isinstance(service_tag, list):
            logger.debug("Wrong type -> {}, {}", service_tag, type(service_tag))
            service_tag = service_tag[0]
        auth = BearerAuth(self._get_access_token())
        api_endpoint = f'https://apigtwb2c.us.dell.com/PROD/sbil/eapi/v5/asset-components?servicetag={service_tag}'
        response = requests.get(api_endpoint, auth=auth)
        answer = response.json()
        return answer

    def print_asset_details(self, service_tag: list):
        print(self.asset_details(service_tag))

    def st_array(self, user_arg: str) -> list:
        if ' ' in user_arg:
            st = user_arg.split()
        elif ',' in user_arg:
            st = user_arg.split(',')
        else:
            st = [user_arg]
        return st

    def _servicetags_from_file(self, abspath: str) -> list:
        with open(f"{abspath}") as f:
            return [st.strip() for st in f]

    def _service_tag_validate(self, service_tag: str) -> bool:
        if isinstance(service_tag, str) and re.match(r'^[\d|A-Z]{7}$', service_tag, re.DOTALL):
            return True
        else:
            return False

    def _service_tags_validate(self, service_tags: list) -> bool:
        for tag in service_tags:
            if not self._service_tag_validate(tag):
                return False
        else:
            return True

    def _strdate_datetime(self, date: str) -> datetime.datetime:
        regex = r'^[\d]{4}-[\d]{2}-[\d]{2}T[\d]{2}:[\d]{2}:[\d]{2}'
        match = re.match(regex, date, re.DOTALL)
        if match:
            return datetime.datetime.strptime(match.group(), '%Y-%m-%dT%H:%M:%S')
        else:
            logger.error("Arg {} does not match str <-> datetime format", date)

    def _warranty_remains(self, expire_date: datetime.datetime) -> str:
        delta: datetime.timedelta = expire_date - datetime.datetime.utcnow()
        logger.debug('Diff between given date <{}-datetime> and today: <{} - timedelta>', expire_date, delta)

        if delta.days >= 0:
            remain = precisedelta(delta, minimum_unit='days', format='%0.0f')
            return remain

        else:
            return 'Expired'

    def _warranty_type_handler(self, services: list) -> str:
        b, p, pp = ('Basic', 'ProSupport', 'ProSupport Plus')
        logger.debug('Warranty services -> {}', services)
        result = []

        for service in services:
            circle = [False, False]
            rp = lambda x: re.match(r'^.+?ProSupport Plus', x, re.DOTALL)
            rs = lambda x: re.match(r'^ProSupport', x, re.DOTALL)
            if rp(service):
                circle[0] = True
            if rs(service):
                circle[1] = True
            result.append(circle)

        pro_plus = [service[0] for service in result]
        pro = [service[1] for service in result]

        if True in pro_plus:
            return pp
        elif (True in pro) and (True not in pro_plus):
            return p
        elif (True not in pro_plus) and (True not in pro):
            return b

    def _warranty_handler(self, resp: list) -> list[dict]:
        data = []  # ServiceTag, Region, Warranty, Elapsed, EndDate

        for tag in resp:

            try:
                st = tag['serviceTag']

                try:
                    region = pycountry.countries.get(alpha_2=tag['countryCode']).name
                except AttributeError:
                    if tag['countryCode'] == 'XM':
                        region = 'Hong Kong'
                    else:
                        region = tag['countryCode']
                        logger.warning('Could not parse country code -> {}', region)

                services = []
                services_start_dates = []
                services_end_dates = []
                # Searching for WarrantyType and End Date:

                for entitlement in tag['entitlements']:

                    if isinstance(entitlement['serviceLevelDescription'], type(None)):
                        continue

                    services_start_dates.append(entitlement['startDate'])
                    services_end_dates.append(entitlement['endDate'])
                    services.append(entitlement['serviceLevelDescription'])

                logger.warning("start dates: {}", services_start_dates)
                highest_date = lambda dates: sorted(list(map(self._strdate_datetime, dates))).pop()
                warranty_start_date = highest_date(services_start_dates)
                warranty_end_date = highest_date(services_end_dates)
                # warranty_end_date: datetime.datetime = sorted(
                # list(map(self._strdate_datetime, services_end_dates))).pop()

                remains = self._warranty_remains(warranty_end_date)
                warranty = self._warranty_type_handler(services)

                data.append({"Service Tag": st,
                             "Country": region,
                             "Warranty": warranty,
                             "Remain": remains,
                             "Start Date": warranty_start_date.strftime('%Y-%m-%d'),
                             "End Date": warranty_end_date.strftime('%Y-%m-%d'),
                             })
            except Exception as e:
                logger.warning("Some error -> {}", e)
                data.append({"Service Tag": tag['serviceTag'],
                             "Country": e,
                             "Warranty": '',
                             "Remain": '',
                             'Start Date': '',
                             "End Date": '',
                             })

        return data

    def servicetags_from_file(self, abspath) -> list:
        with open(f"{abspath}") as f:
            service_tags = [st.strip() for st in f]
            return service_tags

    def warranty_table(self, service_tags: list):

        if not self._service_tags_validate(service_tags):
            logger.error("Service Tags {}", service_tags)
            raise ServiceTagNotValid

        jsons = self.asset_warranty(service_tags)
        data = self._warranty_handler(jsons)
        table = PrettyTable()
        table.field_names = [key for key in data[0]]
        for row in data:
            table.add_row([row[key] for key in row])
        print(table, f'Total: {len(data)}', sep='\n')

    def details_table(self, service_tag: str):
        if isinstance(service_tag, list):
            logger.debug("Wrong type -> {}, {}", service_tag, type(service_tag))
            service_tag = service_tag[0]

        if not self._service_tag_validate(service_tag):
            raise ServiceTagNotValid

        json = self.asset_details(service_tag)
        components = json["components"]
        table = PrettyTable()
        table.field_names = [key for key in components[0]]
        for component in components:
            table.add_row([component[key] for key in component])

        print(table)

    def warranty_json(self, service_tags: list):
        if not self._service_tags_validate(service_tags):
            raise ServiceTagNotValid

        jsons = self.asset_warranty(service_tags)
        data = self._warranty_handler(jsons)
        print(data)
        # return data


def main():
    d = DellApi()

    FUNCS = {
        'warranty': d.warranty_table,
        'warranty_json': d.warranty_json,
        'asset_warranty': d.print_asset_warranty,
        'details': d.details_table,
        'asset_details': d.print_asset_details,
    }
    unif: list = lambda x: x.split(',') if len(x.split(',')) > 1 else [x]

    example_text = """
    $ dell_api -w 1234567,2345678,3456789
    +-------------+---------------+------------+------------------------------+------------+
    | Service Tag |    Country    |  Warranty  |            Remain            |  End Date  |
    +-------------+---------------+------------+------------------------------+------------+
    |   2345678   | United States |   Basic    |           Expired            | 2011-10-06 |
    |   3456789   |     Sweden    |   Basic    |           Expired            | 2007-11-03 |
    |   1234567   | United States | ProSupport | 4 years, 2 months and 0 days | 2025-07-10 |
    +-------------+---------------+------------+------------------------------+------------+
    
    $ dell_api -fw ~/st_example.txt
    +-------------+---------------+------------+------------------------------+------------+
    | Service Tag |    Country    |  Warranty  |            Remain            |  End Date  |
    +-------------+---------------+------------+------------------------------+------------+
    |   2345678   | United States |   Basic    |           Expired            | 2011-10-06 |
    |   3456789   |     Sweden    |   Basic    |           Expired            | 2007-11-03 |
    |   1234567   | United States | ProSupport | 4 years, 2 months and 0 days | 2025-07-10 |
    +-------------+---------------+------------+------------------------------+------------+
    
    """

    parser = argparse.ArgumentParser(description="CLI for fetching data from Dell API",
                                     epilog=example_text,
                                     formatter_class=argparse.RawTextHelpFormatter)

    parser.add_argument('-w', '--warranty', help='Arg=(service tag OR comma separated service tags(up to 100))')
    parser.add_argument('-j', '--warranty_json', help='Arg=(service tag OR comma separated service tags(up to 100))')
    parser.add_argument('-d', '--details', help='Arg=(service tag)')
    parser.add_argument('-aw', '--asset_warranty', help='Arg=(service tag OR comma separated service tags(up to 100))')
    parser.add_argument('-ad', '--asset_details', help='Arg=(service tag)')
    parser.add_argument('-f', '--file', help='Used with -w or -d flag, Arg=(abspath to file with service tag/s)',
                        action='store_true', default=False)

    args = parser.parse_args()
    logger.debug("argparse namespace: {}", args)

    for command in args.__dict__:
        cv = args.__dict__[command]
        if cv is not None:
            cv = d.servicetags_from_file(cv) if args.file == True else d.st_array(cv)
            logger.debug("Service Tag -> {}", cv)
            break

    func = FUNCS[command]
    logger.debug("chosen command -> {}", func.__name__)
    func(cv)


if __name__ == '__main__':
    main()
