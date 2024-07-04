import datetime
import json
from urllib.error import HTTPError
from toggl.TogglPy import Toggl
from atlassian import Confluence
import requests
import os

# Toggl and Confluence credentials
TOGGL_API_TOKEN = os.getenv('TOGGL_API_TOKEN')
CONFLUENCE_URL = os.getenv('CONFLUENCE_URL')
CONFLUENCE_USERNAME = os.getenv('CONFLUENCE_USERNAME')
CONFLUENCE_API_TOKEN = os.getenv('CONFLUENCE_API_TOKEN')
CONFLUENCE_SPACE_KEY = os.getenv('CONFLUENCE_SPACE_KEY')
CONFLUENCE_PARENT_PAGE_ID = os.getenv('CONFLUENCE_PARENT_PAGE_ID')
CLIENT_ID = os.getenv('CLIENT_ID')
WORKSPACE_ID = os.getenv('WORKSPACE_ID')
SUFFIX = os.getenv('SUFFIX', '')

# Initialize Toggl API
toggl = Toggl()
toggl.setAPIKey(TOGGL_API_TOKEN)

# Initialize Confluence API
confluence = Confluence(
    url=CONFLUENCE_URL,
    username=CONFLUENCE_USERNAME,
    password=CONFLUENCE_API_TOKEN
)

def get_toggl_time_entries(client_id, start_date, end_date, workspace_id):
    params = {
        'user_agent': 'Poespas/ToggleToConfluence/1.0.0',
        'workspace_id': workspace_id,
        'client_ids': project_id,
        'since': start_date.isoformat(),
        'until': end_date.isoformat()
    }
    try:
        response = toggl.request('https://api.track.toggl.com/reports/api/v2/details', parameters=params)
        return response['data']
    except requests.exceptions.HTTPError as e:
        print(f"HTTPError: {e.response.status_code} - {e.response.reason}")
        print(f"URL: {e.request.url}")
        print(f"Headers: {e.request.headers}")
        print(f"Body: {e.response.content}")
        raise

def format_time_entries(time_entries):
    table_rows = []
    total_hours = 0.0
    
    for entry in time_entries:
        date = entry['start'][0:10]
        begin_time = entry['start'][11:16]
        end_time = (datetime.datetime.strptime(entry['start'], "%Y-%m-%dT%H:%M:%S%z") +
                    datetime.timedelta(milliseconds=entry['dur'])).strftime("%H:%M")
        hours = entry['dur'] / 1000 / 60 / 60
        total_hours += hours
        description = entry.get('description', 'No Description')
        
        table_rows.append([date, begin_time, end_time, f"{hours:.2f}", description])
    
    # Total hours row
    total_row = ["", "", "", f"Total Hours: {total_hours:.2f}", ""]
    table_rows.append(total_row)
    
    return table_rows

def create_or_update_confluence_page(space, title, html_table, parent_id):
    existing_pages = confluence.get_all_pages_from_space(space, start=0, limit=100, content_type='page')
    existing_page = None
    
    for page in existing_pages:
        if page['title'] == title and 'ancestors' in page and str(page['ancestors'][0]['id']) == str(parent_id):
            existing_page = page
            break

    page = confluence.update_or_create(parent_id, title, html_table, representation='storage')
    print("Page updated successfully.")

def generate_html_table(rows):
    table_html = """
    <table data-layout="full-width">
        <tbody>
            <tr>
                <th><p><strong>Date</strong></p></th>
                <th><p><strong>Begin Time</strong></p></th>
                <th><p><strong>End Time</strong></p></th>
                <th><p><strong>Total Hours</strong></p></th>
                <th><p><strong>Task Description</strong></p></th>
            </tr>
    """
    
    for row in rows:
        table_html += """
            <tr>
                <td><p>{}</p></td>
                <td><p>{}</p></td>
                <td><p>{}</p></td>
                <td><p>{}</p></td>
                <td><p>{}</p></td>
            </tr>
        """.format(*row)
    
    table_html += """
        </tbody>
    </table>
    """
    
    return table_html

def main():
    now = datetime.datetime.now()
    yesterday = now - datetime.timedelta(days=1)
    first_day_of_month = yesterday.replace(day=1, hour=1)
    last_day_of_month = (first_day_of_month + datetime.timedelta(days=32)).replace(day=1) - datetime.timedelta(days=1)
    
    # Retrieve time entries from Toggl
    time_entries = get_toggl_time_entries(CLIENT_ID, first_day_of_month, last_day_of_month, WORKSPACE_ID)
    
    # Format time entries into HTML table
    formatted_rows = format_time_entries(time_entries)
    html_table = f"Time registered in time logging between {first_day_of_month.strftime('%d %B %Y')} and {last_day_of_month.strftime('%d %B %Y')}. <br /> <br /> {generate_html_table(formatted_rows)}"
    
    # Create or update Confluence page
    page_title = f"{first_day_of_month.strftime('%B %Y')} - Time report {SUFFIX}"
    page_title = page_title.strip()
    create_or_update_confluence_page(CONFLUENCE_SPACE_KEY, page_title, html_table, CONFLUENCE_PARENT_PAGE_ID)
    
    print(f"Confluence page created or updated successfully.")

if __name__ == "__main__":
    main()