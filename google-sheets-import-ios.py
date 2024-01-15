import argparse
import codecs
import os
import json
import requests
from lxml import etree as ET

google_sheet_id = '1QCllfVqvAB08cBltn-iM3gogJYBMyRv2iBy8C3XytFU'
gid='375629473'

ios_language_mapper = {
    'ENGLISH': 'en.lproj',
    'SPANISH': 'es.lproj',
    'FRENCH': 'fr.lproj'
    # Add more mappings as needed
}

texts_ios = {}
changes_ios = {}


def load_translations(spreadsheet_id, worksheet_id):
    # Download CSV content from the Google Sheet
    csv_url = f'https://docs.google.com/spreadsheets/d/{spreadsheet_id}/export?format=csv&gid={worksheet_id}'
    response = requests.get(csv_url)

    if response.status_code == 200:
        # Split the content into lines
        csv_content = response.content.decode('utf-8')
        lines = csv_content.split('\n')

        # Extract header and data
        header = list(h.rstrip('\r') for h in lines[0].split(','))
        data = [line.split(',') for line in lines[1:]]

        # Find the column indices for each language
        language_indices = {}
        for column_name, lang in ios_language_mapper.items():

            if column_name in header:
                language_indices[lang] = header.index(column_name)

        # Iterate over rows to populate texts_ios
        for row in data:
            if row:
                key = row[0]
                translations = {}
                # Iterate over languages to get translations
                for lang, index in language_indices.items():
                    translation = row[index].strip() if index < len(row) else None
                    translations[lang] = translation
                    texts_ios[key] = translations


def create_update_xml_file():
    strings_file = os.path.join(ios_lang, 'Localizable.strings')

    if not os.path.exists(strings_file):
        # Create a new .strings file and write translations from the Excel sheet
        with open(strings_file, 'w', encoding='utf-8') as ios_file:
            for key, value in texts_ios.items():
                if ios_lang in value and value[ios_lang] != 'UNTRANSLATED':
                    ios_file.write("\"{}\" = \"{}\";\n".format(key, value[ios_lang]))
        print(f"\nCreated and populated file: {strings_file}")
    else:
        # Update existing .strings file with new translations
        print(f"\nFile: {strings_file}")
        with open(strings_file, 'r', encoding='utf-8') as ios_file:
            content = ios_file.readlines()

        # Initialize changes_ios[ios_lang] if not exists
        if ios_lang not in changes_ios:
            changes_ios[ios_lang] = {}

        # Create a set of existing keys in the .strings file
        existing_keys = {line.split('=')[0].strip()[1:-1] for line in content if '=' in line}

        with open(strings_file, 'a', encoding='utf-8') as ios_file:
            for key, value in texts_ios.items():
                # Check if the key already exists in the .strings file
                if key not in existing_keys:
                    # If the key does not exist, add a new line with the translation from the Excel sheet
                    excel_value = value[ios_lang].strip() if value[ios_lang] else None
                    if excel_value is not None:
                        if ios_lang in value and excel_value != 'UNTRANSLATED':
                            ios_file.write("\"{}\" = \"{}\";\n".format(key, excel_value))
                            changes_ios[ios_lang][key] = excel_value
                            print(f"Added new key \"{key}\" to {ios_lang} with value {excel_value}")
            ios_file.close()

        # Continue with updating translations in an existing .strings file
        with open(strings_file, 'r', encoding='utf-8') as ios_file:
            content = ios_file.readlines()

        for i in range(len(content)):
            line = content[i]
            parts = line.split("=")
            if len(parts) == 2:
                key = parts[0].strip()[1:-1]

                if key in texts_ios and ios_lang in texts_ios[key]:
                    strings_value = parts[1].strip()[1:-2].strip() if parts[1].strip() else None
                    excel_value = texts_ios[key][ios_lang].strip() if texts_ios[key][ios_lang] else None
                    if excel_value is not None:
                        if strings_value is None or (excel_value != strings_value and excel_value != 'UNTRANSLATED'):
                            print(f"Updating {key} in {ios_lang} to {excel_value}")
                            content[i] = "\"{}\" = \"{}\";\n".format(key, excel_value)

                            # Record the change
                            if ios_lang not in changes_ios:
                                changes_ios[ios_lang] = {}
                            if key not in changes_ios[ios_lang]:
                                changes_ios[ios_lang][key] = excel_value

        if len(changes_ios) != 0:
            output = ''.join(content)
            with codecs.open(strings_file, 'w', 'utf-8') as ios_file:
                ios_file.write(output)
                ios_file.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Import ios translations from Google Sheets.')
    parser.add_argument('-spreadsheetId', type=str, help='URL of the public Google Sheet', default=google_sheet_id)
    parser.add_argument('-gid', type=str, help='URL of the public Google Sheet', default=gid)
    args = parser.parse_args()

    # Main script
    load_translations(args.spreadsheetId, args.gid)

    print("Processing localization files for iOS:")

    for ios_lang in ios_language_mapper.values():
        if not os.path.exists(ios_lang):
            os.makedirs(ios_lang)

        create_update_xml_file()

    # Print information about the changes
    print("\nChanges:")
    if all(not changes for changes in changes_ios.values()):
        print("No changes")
    else:
        print(json.dumps(changes_ios, indent=2, ensure_ascii=False).encode('utf-8').decode())

    print("\nFinished successfully!")
