import argparse
import os
import json
import requests
from lxml import etree as ET

google_sheet_id = '1QCllfVqvAB08cBltn-iM3gogJYBMyRv2iBy8C3XytFU'
gid='1225980718'

android_language_mapper = {
    'INGLES': 'values-en',
    'CASTELLANO': 'values',
    'FRANCÉS': 'values-fr'
    # Adjust keys as needed
}

texts_android = {}
changes_android = {}


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
        for column_name, lang in android_language_mapper.items():

            if column_name in header:
                language_indices[lang] = header.index(column_name)

        # Iterate over rows to populate texts_android
        for row in data:
            if row:
                key = row[0]
                translations = {}
                # Iterate over languages to get translations
                for lang, index in language_indices.items():
                    translation = row[index].strip() if index < len(row) else None
                    translations[lang] = translation
                    texts_android[key] = translations


def create_update_xml_file():
    xml_file = os.path.join(android_lang, 'strings.xml')

    if not os.path.exists(xml_file):
        # Create a new XML file and write translations from the Excel sheet
        root = ET.Element('resources')
        for key, value in texts_android.items():
            if android_lang in value and value[android_lang] != 'UNTRANSLATED':
                string_elem = ET.SubElement(root, 'string', name=key)
                string_elem.text = value[android_lang]

        tree = ET.ElementTree(root)
        with open(xml_file, 'wb') as file:
            tree.write(file, encoding='utf-8', xml_declaration=True, pretty_print=True)

        print(f"\nCreated and populated file: {xml_file}")
    else:
        print(f"\nFile: {xml_file}")
        tree = ET.parse(xml_file)
        root_elem = tree.getroot()

        if android_lang not in changes_android:
            changes_android[android_lang] = {}

        existing_keys = {string_elem.get('name') for string_elem in root_elem.findall('.//string')}

        for key, value in texts_android.items():
            if android_lang in value and key not in existing_keys:
                # If the key does not exist, add a new line with the translation from the Excel sheet
                excel_value = value[android_lang].strip() if value[android_lang] else None
                if excel_value is not None:
                    if android_lang in value and excel_value != 'UNTRANSLATED':
                        new_string_elem = ET.Element('string', name=key)
                        new_string_elem.text = excel_value
                        root_elem.append(new_string_elem)
                        changes_android[android_lang][key] = excel_value
                        print(f"Added new key \"{key}\" to {android_lang} with value {excel_value}")

        if changes_android[android_lang]:
            ET.indent(tree, space="\t", level=0)
            with open(xml_file, 'w', encoding='utf-8') as file:
                file.write(ET.tostring(tree, encoding='utf-8', xml_declaration=True, pretty_print=True).decode())

        for string_elem in root_elem.findall('.//string'):
            key = string_elem.get('name')
            if key in texts_android and android_lang in texts_android[key]:
                xml_value = string_elem.text.strip() if string_elem.text else None
                excel_value = texts_android[key][android_lang].strip() if texts_android[key][android_lang] else None
                if excel_value is not None:
                    if excel_value != 'UNTRANSLATED' and (xml_value is None or excel_value != xml_value):
                        print(f"Updated {key} in {android_lang} to {excel_value}")
                        changes_android[android_lang][key] = excel_value
                        string_elem.text = excel_value

        if changes_android[android_lang]:
            ET.indent(tree, space="\t", level=0)
            with open(xml_file, 'w', encoding='utf-8') as file:
                file.write(ET.tostring(tree, encoding='utf-8', xml_declaration=True, pretty_print=True).decode())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Import android translations from Google Sheets.')
    parser.add_argument('-spreadsheetId', type=str, help='URL of the public Google Sheet', default=google_sheet_id)
    parser.add_argument('-gid', type=str, help='URL of the public Google Sheet', default=gid)

    args = parser.parse_args()

    # Main script
    load_translations(args.spreadsheetId, args.gid)

    print("Processing localization files for Android:")

    for android_lang in android_language_mapper.values():
        if not os.path.exists(android_lang):
            os.makedirs(android_lang)

        create_update_xml_file()

    # Print information about the changes
    print("\nChanges:")
    if all(not changes for changes in changes_android.values()):
        print("No changes")
    else:
        print(json.dumps(changes_android, indent=2, ensure_ascii=False).encode('utf-8').decode())

    print("\nFinished successfully!")
