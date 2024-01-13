import fnmatch
import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import xml.etree.ElementTree as ET
import argparse
import time
from gspread.exceptions import APIError

# Mapping of language names for Android
android_language_mapper = {
    'values-en': 'INGLES',
    'values': 'CASTELLANO',
    'values-eu': 'EUSKERA',
    'values-gl': 'GALLEGO',
    'values-it': 'ITALIANO',
    'values-ca': 'CATALÁN',
    'values-fr': 'FRANCÉS',
    'values-pt': 'PORTUGUÉS',
    'values-zh': 'VALENCIANO'
    # Add more mappings as needed
}

# Mapping of language names for iOS
ios_language_mapper = {
    'en.lproj': 'INGLES',
    'es.lproj': 'CASTELLANO',
    'eu-ES.lproj': 'EUSKERA',
    'gl-ES.lproj': 'GALLEGO',
    'ca-ES.lproj': 'CATALÁN',
    'fr.lproj': 'FRANCÉS',
    'pt-PT.lproj': 'PORTUGUÉS',
    'va-ES.lproj': 'VALENCIANO'
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
            # Retardo de 30 segundos si se alcanza el límite de cuota
            print("Rate limit exceeded. Pausing for 60 seconds.")
            time.sleep(60)
            return safe_gspread_request(func, *args, **kwargs)
        else:
            raise e

def export_translations(android_sources, ios_sources):
    # Process Android files
    for root, dirnames, filenames in os.walk(android_sources):
        for filename in fnmatch.filter(filenames, 'strings.xml'):
            dirs = root.split("/")
            lang = dirs[len(dirs) - 1]
            language_name = android_language_mapper.get(lang, lang.capitalize())
            process_android_file(os.path.join(root, filename), language_name)

    # Process iOS files
    for root, dirnames, filenames in os.walk(ios_sources):
        for filename in fnmatch.filter(filenames, 'Localizable.strings'):
            dirs = root.split("/")
            lang = dirs[len(dirs) - 1]
            language_name = ios_language_mapper.get(lang, lang.capitalize())
            process_ios_file(os.path.join(root, filename), language_name)

    # Use credentials JSON file for authentication (replace 'your-credentials.json' with your actual JSON file)
    credentials = ServiceAccountCredentials.from_json_keyfile_name('secure/service_account.json', ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive'])
    gc = gspread.authorize(credentials)

    # Create a new Google Sheets spreadsheet or open an existing one by key
    spreadsheet_key = '1-NMqveM5i1MUGNQITxJ7Kk_kk71YMUaUTvzIAEuDTp8'
    spreadsheet = safe_gspread_request(gc.open_by_key, spreadsheet_key)

    # Android sheet
    worksheet_android = spreadsheet.get_worksheet(0)
    if worksheet_android is None:
        worksheet_android = safe_gspread_request(spreadsheet.add_worksheet, title='Android', rows=1, cols=1)

    # Write Android headers
    lang_index_android = 2
    for lang_key in android_language_mapper.values():
        safe_gspread_request(worksheet_android.update_cell, 1, lang_index_android, lang_key)
        lang_index_android += 1

    # Write Android data
    for i, _key in enumerate(texts_android.keys()):
        safe_gspread_request(worksheet_android.update_cell, i + 2, 1, _key)
        for j, lang_key in enumerate(android_language_mapper.values()):
            if _key in texts_android and lang_key in texts_android[_key]:
                safe_gspread_request(worksheet_android.update_cell, i + 2, j + 2, texts_android[_key][lang_key])
            else:
                safe_gspread_request(worksheet_android.update_cell, i + 2, j + 2, "UNTRANSLATED")

    # iOS sheet
    worksheet_ios = spreadsheet.get_worksheet(1)
    if worksheet_ios is None:
        worksheet_ios = safe_gspread_request(spreadsheet.add_worksheet, title='iOS', rows=1, cols=1)

    # Write iOS headers
    lang_index_ios = 2
    for lang_key in ios_language_mapper.values():
        safe_gspread_request(worksheet_ios.update_cell, 1, lang_index_ios, lang_key)
        lang_index_ios += 1

    # Write iOS data
    for i, _key in enumerate(texts_ios.keys()):
        safe_gspread_request(worksheet_ios.update_cell, i + 2, 1, _key)
        for j, lang_key in enumerate(ios_language_mapper.values()):
            if _key in texts_ios and lang_key in texts_ios[_key]:
                safe_gspread_request(worksheet_ios.update_cell, i + 2, j + 2, texts_ios[_key][lang_key])
            else:
                safe_gspread_request(worksheet_ios.update_cell, i + 2, j + 2, "UNTRANSLATED")

    print(f'Data exported to Google Sheets: {spreadsheet.url}')

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Export translations to Google Sheets.')
    parser.add_argument('-androidSources', type=str, help='Path to Android resources folder', default='./')
    parser.add_argument('-iosSources', type=str, help='Path to iOS resources folder', default='./')
    args = parser.parse_args()

    export_translations(args.androidSources, args.iosSources)
