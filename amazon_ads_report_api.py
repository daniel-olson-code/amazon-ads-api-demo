"""
This module provides functionality for creating and managing Amazon Ads reports.

It includes classes and functions for handling different types of Amazon Ads reports,
making API requests, and processing the report data.
"""

from __future__ import annotations
import dotenv
dotenv.load_dotenv()
import amazon_ads_credentials_api
import class_json_util
import datetime
import uuid
import requests
import gzip
import json
import os
import amazon_ads_api_util

# Load report data from JSON file
with open('amazon_ads_report_api_argument_data.json') as f:
    report_data: list = json.load(f)
    report_data: dict = {row[0]: row for row in report_data}


class AmazonAdType(amazon_ads_api_util.ExtendedEnum):
    """Enumeration of supported Amazon Ad types."""
    SP = 'SPONSORED_PRODUCTS'
    SB = 'SPONSORED_BRANDS'
    SD = 'SPONSORED_DISPLAY'


class ReportType(amazon_ads_api_util.ExtendedEnum):
    """Enumeration of supported report types."""
    CAMPAIGN = 'campaign'
    ADGROUP = 'ad_group'
    AD = 'ad'
    KEYWORDS = 'keywords'
    TARGETS = 'targets'
    TARGETING = 'targeting'
    ADVERTISED_PRODUCTS = 'advertised_products'
    PURCHASED_PRODUCTS = 'purchased_products'
    SEARCH_TERM = 'search_term'


class Version2ReportTypes(amazon_ads_api_util.ExtendedEnum):
    """Enumeration of Version 2 report types."""
    CAMPAIGN = 'campaign'
    ADGROUP = 'adgroup'
    AD = 'ad'
    KEYWORDS = 'keywords'
    TARGETS = 'targets'
    ADVERTISED_PRODUCTS = 'advertisedProducts'
    PURCHASED_PRODUCTS = 'purchasedProducts'
    SEARCH_TERM = 'searchTerm'


def create_async_report(
        profile_id: str,
        ad_type: AmazonAdType,
        report_type: ReportType,
        start_date: datetime.date,
        end_date: datetime.date
) -> Report:
    """
    Creates an asynchronous report for Amazon Ads.

    Args:
        profile_id: The Amazon Ads profile ID.
        ad_type: The type of ad (SP, SB, or SD).
        report_type: The type of report to generate.
        start_date: The start date for the report data.
        end_date: The end date for the report data.

    Returns:
        A Report object representing the created report.
    """
    return Report.create({
        'profile_id': profile_id,
        '_ad_type': ad_type.value,
        '_report_type': report_type.value,
        '_start_date': start_date.strftime('%Y-%m-%d'),
        '_end_date': end_date.strftime('%Y-%m-%d'),
    })


class Report(class_json_util.JsonObject):
    """
    Represents an Amazon Ads report.

    This class handles the creation, status checking, and data retrieval for Amazon Ads reports.
    """

    report_id: str | None = None
    profile_id: str | None = None
    _ad_type: str | None = None
    _report_type: str | None = None
    _start_date: str | None = None
    _end_date: str | None = None
    status: str | None = None
    download_url: str | None = None
    data_path: str | None = None

    @property
    def ad_type(self) -> AmazonAdType:
        """Returns the ad type as an AmazonAdType enum."""
        return AmazonAdType(self._ad_type)

    @property
    def report_type(self) -> ReportType:
        """Returns the report type as a ReportType enum."""
        return ReportType(self._report_type)

    @property
    def start_date(self) -> datetime.datetime:
        """Returns the start date as a datetime object."""
        return datetime.datetime.strptime(self._start_date, '%Y-%m-%d')

    @property
    def end_date(self) -> datetime.datetime:
        """Returns the end date as a datetime object."""
        return datetime.datetime.strptime(self._end_date, '%Y-%m-%d')

    def request(self, tokens: amazon_ads_credentials_api.Tokens) -> None:
        """
        Requests the report from Amazon Ads API.

        Args:
            tokens: The authentication tokens for the API.
        """
        self.report_id = request_report(
            self.profile_id,
            tokens,
            self.ad_type,
            self.report_type,
            self.start_date,
            self.end_date,
        )

    def is_ready(self) -> bool:
        """Checks if the report is ready for download."""
        return self.status == 'COMPLETED' and self.download_url

    def fetch_status(self, tokens: amazon_ads_credentials_api.Tokens) -> bool:
        """
        Fetches the current status of the report.

        Args:
            tokens: The authentication tokens for the API.

        Returns:
            True if the report is ready, False otherwise.
        """
        data = get_report_status_and_download_url(self.profile_id, tokens, self.report_id)
        self.status = data['status']
        self.download_url = data['url']
        if self.is_ready():
            self.download_data()
            return True
        return False

    def download_data(self) -> list[dict]:
        """
        Downloads and saves the report data.

        Returns:
            The report data as a list of dictionaries.
        """
        report_data = download_report(self.download_url)

        save_dir = 'report-data'
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)

        self.data_path = os.path.join(save_dir, f'{uuid.uuid4()}.json')
        with open(self.data_path, 'w') as f:
            f.write(json.dumps(report_data, indent=4))

        return report_data

    def get_report_data(self) -> list[dict]:
        """
        Retrieves the report data.

        Returns:
            The report data as a list of dictionaries.
        """
        if not isinstance(self.data_path, str):
            return self.download_data()

        with open(self.data_path) as f:
            return json.load(f)


def get_report_type_name(
        ad_type: AmazonAdType,
        report_type: ReportType | Version2ReportTypes
) -> str:
    """
    Gets the report type name based on ad type and report type.

    Args:
        ad_type: The type of ad (SP, SB, or SD).
        report_type: The type of report.

    Returns:
        The report type name as a string.

    Raises:
        KeyError: If no report data is found for the given combination.
    """
    _ad_type = {AmazonAdType.SP.value: 'sp', AmazonAdType.SB.value: 'sb', AmazonAdType.SD.value: 'sd'}[ad_type.value]
    key = f'{_ad_type}_{report_type.value}'
    if key not in report_data:
        raise KeyError(f'No report data found for key {key}({ad_type.value}, {report_type.value})')
    return key


def get_report_type_id(
        ad_type: AmazonAdType,
        report_type: ReportType | Version2ReportTypes
) -> str:
    """
    Gets the report type ID based on ad type and report type.

    Args:
        ad_type: The type of ad (SP, SB, or SD).
        report_type: The type of report.

    Returns:
        The report type ID as a string.
    """
    if ad_type == AmazonAdType.SP:
        return report_type.value
    return f'{report_type.value}s'


def get_request_args(
        ad_type: AmazonAdType,
        report_type: ReportType | Version2ReportTypes,
        start_date: datetime.date,
        end_date: datetime.date
) -> dict:
    """
    Prepares the arguments for a report request.

    Args:
        ad_type: The type of ad (SP, SB, or SD).
        report_type: The type of report.
        start_date: The start date for the report data.
        end_date: The end date for the report data.

    Returns:
        A dictionary containing the request arguments.
    """
    key = get_report_type_name(ad_type, report_type)
    data = report_data[key]

    (table_name,
     __ad_type,  # <- not used here
     column_ids,
     report_type_id,
     data_retention,
     max_date_range,
     time_unit,
     group_by,
     filters,
     metrics) = tuple(data)

    metrics = metrics + (['date'] if time_unit == 'DAILY' else ['startDate', 'endDate'])

    return {
        "name": f'{table_name}-{uuid.uuid4()}',
        "startDate": start_date.strftime('%Y-%m-%d'),
        "endDate": end_date.strftime('%Y-%m-%d'),
        "configuration": {
            "adProduct": ad_type.value,
            "columns": metrics,
            "reportTypeId": report_type_id,
            "format": "GZIP_JSON",
            "groupBy": group_by,
            "timeUnit": time_unit,
            **filters
        },
    }


def request_report(
        profile_id: str,
        tokens: amazon_ads_credentials_api.Tokens,
        ad_type: AmazonAdType,
        report_type: ReportType | Version2ReportTypes,
        start_date: datetime.date,
        end_date: datetime.date
) -> str:
    """
    Requests a report from the Amazon Ads API.

    Args:
        profile_id: The Amazon Ads profile ID.
        tokens: The authentication tokens for the API.
        ad_type: The type of ad (SP, SB, or SD).
        report_type: The type of report to generate.
        start_date: The start date for the report data.
        end_date: The end date for the report data.

    Returns:
        The report ID as a string.

    Raises:
        requests.exceptions.RequestException: If the API request fails.
    """
    api_url = amazon_ads_api_util.join_url(
        amazon_ads_credentials_api.get_api_url(tokens.region),
        '/reporting/reports'
    )

    auth_headers = amazon_ads_credentials_api.get_authorization_headers(profile_id, tokens)

    r = requests.post(
        api_url,
        headers={
            **auth_headers,
            'Content-Type': 'application/vnd.createasyncreportrequest.v3+json',
            'Accept': 'application/vnd.createasyncreportrequest.v3+json',
        },
        data=json.dumps(
            get_request_args(
                ad_type,
                report_type,
                start_date,
                end_date
            )
        ),
    )

    if amazon_ads_api_util.rate_limit(r):
        return request_report(
            profile_id,
            tokens,
            ad_type,
            report_type,
            start_date,
            end_date
        )

    # TODO: check for errors

    return r.json()['reportId']


def get_report_status_and_download_url(
        profile_id: str,
        tokens: amazon_ads_credentials_api.Tokens,
        report_id: str
) -> dict[str, str]:
    """
    Retrieves the status and download URL for a report.

    Args:
        profile_id: The Amazon Ads profile ID.
        tokens: The authentication tokens for the API.
        report_id: The ID of the report to check.

    Returns:
        A dictionary containing the status and download URL of the report.

    Raises:
        requests.exceptions.RequestException: If the API request fails.
    """
    api_url = amazon_ads_api_util.join_url(
        amazon_ads_credentials_api.get_api_url(tokens.region),
        f'/reporting/reports/{report_id}'
    )

    auth_headers = amazon_ads_credentials_api.get_authorization_headers(profile_id, tokens)

    r = requests.get(
        api_url,
        headers={
            **auth_headers,
            'Content-Type': 'application/vnd.getasyncreportrequeststatus.v3+json',
            'Accept': 'application/vnd.getasyncreportrequeststatus.v3+json',
        },
    )

    if amazon_ads_api_util.rate_limit(r):
        return get_report_status_and_download_url(profile_id, tokens, report_id)

    json_response = r.json()

    # TODO: check for errors

    status = json_response['status']
    url = json_response.get('url', None)

    return {'status': status, 'url': url}


def download_report(url: str) -> list[dict]:
    """
    Downloads and decompresses a report from the given URL.

    Args:
        url: The URL to download the report from.

    Returns:
        The report data as a list of dictionaries.

    Raises:
        TimeoutError: If the request has expired.
        requests.exceptions.RequestException: If the download fails.
    """
    r = requests.get(url)

    if 'Request has expired' in r.text:
        raise TimeoutError('Request has expired')

    # TODO: check for errors

    # TODO: check format requested, currently only GZIP but to make this future proof
    table = json.loads(gzip.decompress(r.content))

    return amazon_ads_api_util.fix_table(table)
