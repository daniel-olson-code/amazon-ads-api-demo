"""A simple web server for authorizing Amazon Ads API accounts.

This server allows users to authorize their Amazon account with the Amazon Ads API.
It provides the necessary auth tokens for API access.

The server includes a home page and a redirect page/URI.
"""

import os
import json
import flask
import datetime
import dotenv
import amazon_ads_credentials_api
import amazon_ads_report_api
import amazon_ads_api_util

# Some packages rely on env vars
dotenv.load_dotenv()

app = flask.Flask(__name__)
app.static_folder = 'static'

REDIRECT_URI = 'amazon-ads-api-redirect'
BASE_URL = 'http://127.0.0.1:7777'
REDIRECT_URL = f'{BASE_URL}/{REDIRECT_URI}'

# The account and region we will be accessing
profile_id = None
profiles = []  # [{'profileId': 123456789, 'accountInfo': {'type': 'seller', 'name': 'yay'}, 'countryCode': 'US'}]
tokens: amazon_ads_credentials_api.Tokens | None = amazon_ads_credentials_api.load_tokens()
reports = []


def create_html(body: str) -> str:
    """Creates an HTML page using a template and the provided body content.

    Args:
        body: A string containing the HTML body content.

    Returns:
        A string containing the complete HTML page.
    """
    with open(os.path.join('static', 'template.html')) as f:
        return f.read().replace('<!--body-->', body)


@app.route('/')
def index():
    """Renders the home page.

    This page allows users to authorize their Amazon account with the Amazon Ads API.
    It displays a button to open the Amazon consent page and shows the authorization status.

    Returns:
        An HTML string for the home page.
    """
    global BASE_URL, REDIRECT_URL, tokens
    tokens = amazon_ads_credentials_api.load_tokens()
    has_tokens = tokens is not None
    button_text = 'Authorize Amazon Ads' if not has_tokens else 'Refresh Tokens'

    if has_tokens:
        communication_elements = f'''
            <p class="communication-text"> 
                You are authorized. 
            </p>
            <p class="communication-text"> 
                Click the button above to re-authorize Amazon Ads. (This shouldn't be needed) 
            </p>
            <div class="top-left-btn">
                <button class="auth-btn" onclick="window.location.href = '/reports';"> Reports </button>
            </div>
        '''
    else:
        communication_elements = f'''
            <p class="communication-text"> 
                Be sure to add "{BASE_URL}" to authorized URIs 
            </p>
            <p class="communication-text"> 
                and "{REDIRECT_URL}" to redirect URIs 
            </p>
        '''

    consent_url = amazon_ads_credentials_api.create_consent_url(
        amazon_ads_credentials_api.AmazonAdsApiRegions.NA,
        REDIRECT_URL
    )

    return create_html(f'''
        <div class="container">
            <script> const openLink = link => window.open(link);</script>
            
            <p> Login with your Amazon account and then click the `Reports` button. </p>
            <br/>
            <button class="auth-btn" onclick="openLink('{consent_url}')"> {button_text} </button>
            {communication_elements}'
        </div>
    ''')


@app.route('/static/<path:path>')
def static_file(path):
    """Serves static files.

    Args:
        path: The path to the requested static file.

    Returns:
        The requested static file.
    """
    return flask.send_from_directory('static', path)


@app.route(f'/{REDIRECT_URI}')
def amazon_redirect():
    """Handles the Amazon redirect after authorization.

    This page receives the code from Amazon, fetches the access and refresh tokens,
    and saves them using the amazon_ads_credentials_api.

    Returns:
        An HTML string confirming successful authorization or an error message.
    """
    global REDIRECT_URL
    if 'code' in flask.request.args:
        code = flask.request.args['code']
        # scope = flask.request.args['scope']  # scope is not currently used

        tokens: amazon_ads_credentials_api.Tokens = amazon_ads_credentials_api.receive_code(
            amazon_ads_credentials_api.AmazonAdsApiRegions.NA,
            code,
            REDIRECT_URL
        )

        amazon_ads_credentials_api.save_tokens(tokens)

        return create_html(f'''
            <div class="container">
                <p class="communication-text"> We received your code! </p>
                <a class="communication-text" href="/">Go Home</a>
            </div>
        ''')

    return create_html(f'''
        <div class="container">
            <p class="communication-text"> 
                Hi, it looks like you came here without Amazon's help!
            </p>
            <a class="communication-text" href="/">
                Go Home
            </a>
        </div>
    ''')


@app.route('/reports-api', methods=['POST', 'GET'])
def report_api():
    """Handles report-related API requests.

    This endpoint processes various operations related to Amazon Ads reports,
    including fetching profiles, selecting profiles, and managing reports.

    Returns:
        A JSON response containing the requested data or error message.
    """
    global profiles, profile_id
    if flask.request.method == 'POST':
        if flask.request.is_json:
            json_data = flask.request.get_json()
            if 'operation' not in json_data:
                return flask.jsonify({'error': 'Must specify operation.'})
            operation = json_data['operation']

            # Handle different operations
            if operation == 'profiles':
                return handle_profiles_operation()
            elif operation == 'select-profile':
                return handle_select_profile_operation(json_data)
            elif operation == 'profile-name':
                return handle_profile_name_operation()
            elif operation == 'available-reports':
                return flask.jsonify({'reports': get_all_reports()})
            elif operation == 'reports':
                return handle_reports()
            elif operation == 'get-values':
                return handle_get_values_operation()
            elif operation == 'request-report':
                return handle_request_report_operation(json_data)
            elif operation == 'report-status':
                return handle_report_status_operation(json_data)
            elif operation == 'download-report':
                pass  # Implement download report functionality
        return flask.jsonify({'error': 'Must post a json.'})
    return create_html('''
        <div class="container">
            <p class="communication-text">
                This is the report api.
            </p>
        </div>
    ''')


def handle_profiles_operation():
    """Handles the 'profiles' operation in the report API."""
    global tokens, profiles
    if not tokens:
        return flask.jsonify({'error': 'Must authorize first.'})
    if not profiles:
        profiles = amazon_ads_credentials_api.fetch_profiles(tokens)
    return flask.jsonify({'profiles': profiles})


def handle_select_profile_operation(json_data):
    """Handles the 'select-profile' operation in the report API."""
    global profile_id
    profile_id = f'{json_data["profile_id"]}'
    return flask.jsonify({'success': True})


def handle_profile_name_operation():
    """Handles the 'profile-name' operation in the report API."""
    global profiles, profile_id
    for profile in profiles:
        if f'{profile["profileId"]}' == f'{profile_id}':
            return flask.jsonify({'name': get_profile_display_name(profile)})
    return flask.jsonify({'error': 'Profile not found.'})


def handle_reports():
    """Retrieves all available reports making headers in readable format"""
    global reports

    def fix_row(row):
        new_row = {}
        for key, value in row.items():
            if key == 'download_url':
                continue
            new_row[key.replace('_', ' ').strip().title()] = value
        return new_row

    _reports = [fix_row(r) for r in amazon_ads_api_util.fix_table(reports)]

    return flask.jsonify({'reports': _reports})


def handle_get_values_operation():
    """Handles the 'get-values' operation in the report API."""
    return flask.jsonify({
        'ad_types': amazon_ads_report_api.AmazonAdType.list(),
        'report_types': amazon_ads_report_api.ReportType.list(),
    })


def handle_request_report_operation(json_data):
    """Handles the 'request-report' operation in the report API."""
    global profile_id, tokens, reports
    report = amazon_ads_report_api.create_async_report(
        profile_id,
        amazon_ads_report_api.AmazonAdType(json_data['ad_type']),
        amazon_ads_report_api.ReportType(json_data['report_type']),
        datetime.datetime.strptime(json_data['start_date'], '%Y-%m-%d').date(),
        datetime.datetime.strptime(json_data['end_date'], '%Y-%m-%d').date(),
    )
    report.request(tokens)
    reports.append(report.json)
    return handle_reports()  # flask.jsonify({'reports': amazon_ads_api_util.fix_table(reports)})


def handle_report_status_operation(json_data):
    """Handles the 'report-status' operation in the report API."""
    global reports, tokens
    for i, report in enumerate(reports):
        if f'{report["report_id"]}' == f'{json_data["report_id"]}':
            r = amazon_ads_report_api.Report.create(report)
            r.fetch_status(tokens)
            reports[i] = r.json
    return handle_reports()  # flask.jsonify({'reports': amazon_ads_api_util.fix_table(reports)})


@app.route('/reports')
def reports_page():
    """Renders the reports page.

    This page displays the reports if the user is authorized and a profile is selected.

    Returns:
        An HTML string for the reports page or a redirect to the home page if not authorized.
    """
    global profile_id, tokens
    if not tokens:
        return create_html('''
            <div class="container">
                <p class="communication-text">
                    You are not authorized.
                </p>
                <a class="communication-text" href="/">Go Home</a>
            <div>
        ''')

    if profile_id is None:
        return flask.send_from_directory('static', 'profiles.html')
    elif dict(flask.request.args).get('profile-html') == 'yes':
        return flask.send_from_directory('static', 'profiles.html')

    return flask.send_from_directory('static', 'reports.html')


def get_profile_display_name(profile):
    """Generates a display name for a profile.

    Args:
        profile: A dictionary containing profile information.

    Returns:
        A string containing the formatted profile display name.
    """
    return (f'{profile["accountInfo"]["name"]}'
            f' ~ {profile["countryCode"]}'
            f' ~ {profile["accountInfo"]["type"]}')


def snake_case_to_readable_text(word: str):
    """Converts a snake_case string to readable text.

    Args:
        word: A string in snake_case format.

    Returns:
        A string with each word capitalized and separated by spaces.
    """
    words = word.split('_')
    return ' '.join([
        f'{_word[0].upper()}{_word[1:]}'
        for _word in words
    ])


def readable_text_to_snake_case(word: str):
    """Converts readable text to snake_case.

    Args:
        word: A string of readable text.

    Returns:
        A string in snake_case format.
    """
    words = word.lower().split(' ')
    return '_'.join(words)


def get_all_reports():
    """Retrieves all available report names.

    Returns:
        A list of report names with capitalized ad types.
    """

    def capitalize_ad_type(word: str):
        ad_type = word[:2]
        rest = word[2:]
        return f'{ad_type.upper()}{rest}'

    return [
        capitalize_ad_type(snake_case_to_readable_text(report_name))
        for report_name in amazon_ads_report_api.report_data
    ]


if __name__ == '__main__':
    app.run(port=5000)


