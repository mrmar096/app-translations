import fnmatch
import os
import xml.etree.ElementTree as ET
import argparse
import time
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from gspread.exceptions import APIError

# Google Sheet ID
google_sheet_id = '1QCllfVqvAB08cBltn-iM3gogJYBMyRv2iBy8C3XytFU'
google_sheet_url = f'https://docs.google.com/spreadsheets/d/{google_sheet_id}'

# Mapping of language names for Android
android_language_mapper = {
    'values': 'CASTELLANO',
    'values-en': 'INGLES',
    'values-fr': 'FRANCÉS'
    # Add more mappings as needed
}

# Mapping of language names for iOS
ios_language_mapper = {
    'es.lproj': 'CASTELLANO',
    'en.lproj': 'INGLES',
    'fr.lproj': 'FRANCÉS'
    # Add more mappings as needed
}

texts_android = {}
texts_ios = {}


def process_android_file(file_path, language_name):
    tree = ET.parse(file_path)
    root = tree.getroot()

    for string_elem in root.findall('.//string[@name]'):
        key = string_elem.get('name')

        # Check if the translatable attribute is present and set to "false"
        translatable_attr = string_elem.get('translatable')
        if translatable_attr and translatable_attr.lower() == 'false':
            continue

        value = string_elem.text.strip() if string_elem.text else "UNTRANSLATED"

        if key not in texts_android:
            texts_android[key] = {}

        texts_android[key][language_name] = value


def process_ios_file(file_path, language_name):
    with open(file_path, encoding='utf-8') as f:
        content = f.readlines()
        for item in content:
            parts = item.split("=")
            if len(parts) == 2:
                key = parts[0].strip()[1:-1]
                value = parts[1].strip()[1:-2].strip() if parts[1].strip() else "UNTRANSLATED"

                if key not in texts_ios:
                    texts_ios[key] = {}

                texts_ios[key][language_name] = value

def safe_gspread_request(func, *args, **kwargs):
    try:
        return func(*args, **kwargs)
    except APIError as e:
        if 'RATE_LIMIT_EXCEEDED' in str(e):
            # Pause for 60 seconds if rate limit is exceeded
            print("Rate limit exceeded. Pausing for 60 seconds.")
            time.sleep(60)
            return safe_gspread_request(func, *args, **kwargs)
        else:
            raise e


def export_translations(android_sources, ios_sources, spreadsheet_id):
    # Use credentials JSON file for authentication (replace 'secure/service_account.json' with your actual JSON file)
    credentials = ServiceAccountCredentials.from_json_keyfile_name('secure/service_account.json',
                                                                   ['https://spreadsheets.google.com/feeds',
                                                                    'https://www.googleapis.com/auth/drive'])
    gc = gspread.authorize(credentials)

    # Open an existing spreadsheet by key
    spreadsheet_key = spreadsheet_id
    spreadsheet = safe_gspread_request(gc.open_by_key, spreadsheet_key)

    try:
        worksheet_android = spreadsheet.get_worksheet(0)
    except gspread.exceptions.WorksheetNotFound:
        worksheet_android = safe_gspread_request(spreadsheet.add_worksheet, title='Android', rows=1000,
                                                 cols=1000)

    try:
        worksheet_ios = spreadsheet.get_worksheet(1)
    except gspread.exceptions.WorksheetNotFound:
        worksheet_ios = safe_gspread_request(spreadsheet.add_worksheet, title='iOS', rows=1000,
                                             cols=1000)

    keys_from_android_sheet = set(worksheet_android.col_values(1)[1:])
    keys_from_ios_sheet = set(worksheet_ios.col_values(1)[1:])

    if keys_from_android_sheet is not None:
        # Process Android files
        for root, dirnames, filenames in os.walk(android_sources):
            for filename in fnmatch.filter(filenames, 'strings.xml'):
                dirs = root.split("/")
                lang = dirs[len(dirs) - 1]
                language_name = android_language_mapper.get(lang, lang.capitalize())
                process_android_file(os.path.join(root, filename), language_name)

        # Write Android headers if not exists
        lang_index_android = 2
        row_sheet_values = set(filter(None, safe_gspread_request(worksheet_android.row_values, 1)))
        if row_sheet_values != set(android_language_mapper.values()):
            for lang_key in android_language_mapper.values():
                safe_gspread_request(worksheet_android.update_cell, 1, lang_index_android, lang_key)
                lang_index_android += 1

        # Compare keys with the ones from the spreadsheet
        new_keys_android = set(texts_android.keys()) - keys_from_android_sheet

        if len(new_keys_android) != 0:
            print("New keys detected in Android Resources")
            print(new_keys_android)

            # Write new keys to the spreadsheet
            for i, key in enumerate(new_keys_android):
                safe_gspread_request(worksheet_android.update_cell,
                                     len(keys_from_android_sheet) + i + 2, 1, key)
                for j, lang_key in enumerate(android_language_mapper.values()):
                    if lang_key in texts_android[key]:
                        safe_gspread_request(worksheet_android.update_cell,
                                             len(keys_from_android_sheet) + i + 2, j + 2, texts_android[key][lang_key])
                    else:
                        safe_gspread_request(worksheet_android.update_cell, len(keys_from_android_sheet) + i + 2, j + 2,
                                             "UNTRANSLATED")

            print(f'Android keys exported to Google Sheets: {google_sheet_url}')
        else:
            print("0 new keys found for Android")

    else:
        print("Can't download keys from google sheet")

    if keys_from_ios_sheet is not None:
        # Process iOS files
        for root, dirnames, filenames in os.walk(ios_sources):
            for filename in fnmatch.filter(filenames, 'Localizable.strings'):
                dirs = root.split("/")
                lang = dirs[len(dirs) - 1]
                language_name = ios_language_mapper.get(lang, lang.capitalize())
                process_ios_file(os.path.join(root, filename), language_name)

        # Write iOS headers if not exists
        lang_index_ios = 2
        row_sheet_values = set(filter(None, safe_gspread_request(worksheet_ios.row_values, 1)))
        if set(row_sheet_values) != set(ios_language_mapper.values()):
            for lang_key in ios_language_mapper.values():
                safe_gspread_request(worksheet_ios.update_cell, 1, lang_index_ios, lang_key)
                lang_index_ios += 1

        # Compare keys with the ones from the spreadsheet
        new_keys_ios = set(texts_ios.keys()) - keys_from_ios_sheet

        if len(new_keys_ios) != 0:
            print("\nNew keys detected in iOS Resources")
            print(new_keys_ios)

            for i, key in enumerate(new_keys_ios):
                safe_gspread_request(worksheet_ios.update_cell,
                                     len(keys_from_ios_sheet) + i + 2, 1, key)
                for j, lang_key in enumerate(ios_language_mapper.values()):
                    if lang_key in texts_ios[key]:
                        safe_gspread_request(
                            worksheet_ios.update_cell, len(keys_from_ios_sheet) + i + 2, j + 2,
                            texts_ios[key][lang_key])
                    else:
                        safe_gspread_request(worksheet_ios.update_cell, len(keys_from_ios_sheet) + i + 2, j + 2,
                                             "UNTRANSLATED")

            print(f'iOS keys exported to Google Sheets: {google_sheet_url}')
        else:
            print("0 new keys found for iOS")

    else:
        print("Can't download keys from google sheet")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Export translations to Google Sheets.')
    parser.add_argument('-androidSources', type=str, help='Path to Android resources folder', default='./')
    parser.add_argument('-iosSources', type=str, help='Path to iOS resources folder', default='./')
    parser.add_argument('-spreadsheetId', type=str, help='URL of the public Google Sheet', default=google_sheet_id)
    args = parser.parse_args()

    export_translations(args.androidSources, args.iosSources, args.spreadsheetId)
