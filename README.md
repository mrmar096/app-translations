# Internationalization Project

This project aims to streamline the internationalization of mobile applications by exporting and importing translations between Excel spreadsheets and resource files for Android and iOS.

## Features

### 1. Export to Excel

The export script gathers translations from Android and iOS resource files and saves them in a combined Excel file.
Each platform's translations are organized into separate sheets within the Excel file.

The cells are filled with the "UNTRANSLATED" word when the key is not found in the other resource language files.

The identifiers of the translations are listed in the first column, and each subsequent column represents a different language.
In the Excel file, the structure follows this format:

Sample Excel:

![excel-sample.png](docs%2Fexcel-sample.png)

Android Sheet:
The script skip keys with translatable="false"

Column A: Translation Identifiers.

Column B and onward: Translations in respective languages based on the Android language mapper.
``` python
# Mapping of language names for Android
android_language_mapper = {
    'values-en': 'INGLES',
    'values': 'CASTELLANO',
    'values-eu': 'EUSKERA',
    'values-gl': 'GALLEGO',
    'values-it': 'ITALIANO',
    'values-ca': 'CATALÁN',
    'values-fr': 'FRANCÉS',
    'values-pt': 'PORTUGUÉS'
    # Add more mappings as needed
}
```
iOS Sheet:

Column A: Translation Identifiers.

Column B and onward: Translations in respective languages based on the iOS language mapper.

``` python
# Mapping of language names for iOS
ios_language_mapper = {
    'en.lproj': 'INGLES',
    'es.lproj': 'CASTELLANO',
    'eu-ES.lproj': 'EUSKERA',
    'gl-ES.lproj': 'GALLEGO',
    'ca-ES.lproj': 'CATALÁN',
    'fr.lproj': 'FRANCÉS',
    'pt-PT.lproj': 'PORTUGUÉS'
    # Add more mappings as needed
}
```
Feel free to modify the language mappers and add more mappings according to your project's requirements.

#### Execution:

```bash
python export-translation.py
```

### 2. Import to Android (strings.xml)
The Android import script reads translations from an Excel file and updates or creates strings.xml files for different languages.

Execution:
```bash
python3 import-android.py
```
Sample Output:

![import-android-output.png](docs%2Fimport-android-output.png)

### 3. Import to iOS (Localizable.strings)
The iOS import script reads translations from an Excel file and updates or creates Localizable.strings files for different languages.

Execution:

```bash
python3 import-ios.py
```
Sample Output:

![import-ios-output.png](docs%2Fimport-ios-output.png)

## Directory Structure
To successfully execute the import and export scripts, adhere to the following directory structure.
![directory-structure.png](docs%2Fdirectory-structure.png)

For exporting, ensure that language resource folders with names corresponding to those declared in the script's mapper exist.

For importing, at a minimum, you need the app_translations.xlsx file. If language resource files are missing, the script will create the necessary files or update existing ones.

## Requirements
Python 3
Libraries specified in each script's requirements (openpyxl, xlsxwriter, lxml)

```bash
pip3 install openpyxl lxml xlsxwriter
```