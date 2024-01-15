# Google Sheets Support
The export script gathers translations from Android and iOS resource files and saves them in a combined Google Sheet
Each platform's translations are organized into separate worksheets within the Google Sheet

The cells are filled with the "UNTRANSLATED" word when the key is not found in the other resource language files.

The identifiers of the translations are listed in the first column, and each subsequent column represents a different language.
In the Google Sheet, the structure follows this format:

Sample Excel:

![google-sheets-sample.png](docs%2Fgoogle-sheets-sample.png)

You have a link to this template [here](https://docs.google.com/spreadsheets/d/1QCllfVqvAB08cBltn-iM3gogJYBMyRv2iBy8C3XytFU/edit#gid=1225980718)

Android Sheet:
The script skip keys with translatable="false"

Column A: Translation Identifiers.

Column B and onward: Translations in respective languages based on the Android language mapper.
``` python
# Mapping of language names for Android
android_language_mapper = {
    'values': 'SPANISH',
    'values-en': 'ENGLISH',
    'values-fr': 'FRENCH'
    # Add more mappings as needed
}
```
iOS Sheet:

Column A: Translation Identifiers.

Column B and onward: Translations in respective languages based on the iOS language mapper.

``` python
# Mapping of language names for iOS
ios_language_mapper = {
    'es.lproj': 'SPANISH',
    'en.lproj': 'ENGLISH',
    'fr.lproj': 'FRENCH'
    # Add more mappings as needed
}
```
Feel free to modify the language mappers and add more mappings according to your project's requirements.

#### Execution:
You need a Google Service Account JSON with Google Sheets Api Enabled and provide in secure/service_account.json.
The export script use service account to edit the Google Sheet so you must set Editor permission for this service account on the Google Sheet.

This run attempts to recursively search for strings.xml and Localizable.strings and add the new keys to Google Sheet.

```bash
python3 google-sheets-export.py
```
Or you can pass by parameters the language resources sources for export.

```bash
python3 google-sheets-export.py  -androidSources android/src/main/res/ -iosSources ios/Supporting\ Files/ -spreadsheetId yourGoogleSheetId
```

### 2. Import to Android (strings.xml)
The Android import script reads translations from the Google Sheet and updates or creates strings.xml files for different languages.

Execution:
```bash
python3 google-sheets-import-android.py
```

Or you can pass by parameters the language resources sources for export.

```bash
python3 google-sheets-import-android.py  -spreadsheetId yourGoogleSheetId -gid theIdOfTheWorkSheetTab
```
Sample Output:

![import-android-output.png](..%2Fdocs%2Fimport-android-output.png)

### 3. Import to iOS (Localizable.strings)
The iOS import script reads translations from an Excel file and updates or creates Localizable.strings files for different languages.

Execution:

```bash
python3 google-sheets-import-ios.py
```

Or you can pass by parameters the language resources sources for export.

```bash
python3 google-sheets-import-ios.py  -spreadsheetId yourGoogleSheetId -gid theIdOfTheWorkSheetTab
```

Sample Output:

![import-ios-output.png](..%2Fdocs%2Fimport-ios-output.png)

## Directory Structure
To successfully execute the import and export scripts, adhere to the following directory structure.

![directory-structure.png](docs%2Fdirectory-structure.png)

For exporting, ensure that language resource folders with names corresponding to those declared in the script's mapper exist.

For importing, at a minimum, you need the Google Sheet. If language resource files are missing, the script will create the necessary files or update existing ones.

## Requirements
Python 3
Libraries specified in each script's requirements (oauth2client, lxml, gspread)

```bash
pip3 install oauth2client lxml gspread
```