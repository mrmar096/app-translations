import fnmatch
import os
import xlsxwriter
import xml.etree.ElementTree as ET
import argparse

excelPath = "app_translations.xlsx"

# Mapping of language names for Android
android_language_mapper = {
    'values': 'SPANISH',
    'values-en': 'ENGLISH',
    'values-fr': 'FRENCH'
    # Add more mappings as needed
}

# Mapping of language names for iOS
ios_language_mapper = {
    'es.lproj': 'SPANISH',
    'en.lproj': 'ENGLISH',
    'fr.lproj': 'FRENCH'
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

def export_translations(android_sources, ios_sources, excel_file):
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

    # Export to Excel file
    COL = [chr(i) for i in range(ord('A'), ord('Z') + 1)] + ['A' + chr(i) for i in range(ord('A'), ord('Z') + 1)]

    workbook = xlsxwriter.Workbook(excel_file)

    # Android sheet
    worksheet_android = workbook.add_worksheet('Android')

    # Write Android headers
    lang_index_android = 1
    for lang_key in android_language_mapper.values():
        col = COL[lang_index_android] + "1"
        worksheet_android.write(col, lang_key)
        lang_index_android += 1

    # Write Android data
    for i, _key in enumerate(texts_android.keys()):
        worksheet_android.write(COL[0] + str(i + 2), _key)
        for j, lang_key in enumerate(android_language_mapper.values()):
            col = COL[j + 1] + str(i + 2)
            if _key in texts_android and lang_key in texts_android[_key]:
                worksheet_android.write(col, texts_android[_key][lang_key])
            else:
                worksheet_android.write(col, "UNTRANSLATED")

    # iOS sheet
    worksheet_ios = workbook.add_worksheet('iOS')

    # Write iOS headers
    lang_index_ios = 1
    for lang_key in ios_language_mapper.values():
        col = COL[lang_index_ios] + "1"
        worksheet_ios.write(col, lang_key)
        lang_index_ios += 1

    # Write iOS data
    for i, _key in enumerate(texts_ios.keys()):
        worksheet_ios.write(COL[0] + str(i + 2), _key)
        for j, lang_key in enumerate(ios_language_mapper.values()):
            col = COL[j + 1] + str(i + 2)
            if _key in texts_ios and lang_key in texts_ios[_key]:
                worksheet_ios.write(col, texts_ios[_key][lang_key])
            else:
                worksheet_ios.write(col, "UNTRANSLATED")

    workbook.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Export translations to Excel.')
    parser.add_argument('-androidSources', type=str, help='Path to Android resources folder', default='./')
    parser.add_argument('-iosSources', type=str, help='Path to iOS resources folder', default='./')
    parser.add_argument('-excelFile', type=str, help='Path to iOS resources folder', default=excelPath)
    args = parser.parse_args()

    export_translations(args.androidSources, args.iosSources, args.excelFile)
