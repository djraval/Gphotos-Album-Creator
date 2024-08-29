# Google Photos Album Creator (Limited Functionality)

## Project Status: Discontinued

This project was an evening endeavor aimed at organizing a personal Google Photos library. However, due to limitations in the Google Photos API, the project's functionality is severely restricted and is no longer being actively developed.

### The Issue

Google Photos API has restrictions on how third-party applications can interact with user data:

1. Applications can only add media items that they have uploaded to albums they have created.
2. Existing media items in a user's library cannot be added to new albums created by third-party applications.

These limitations effectively prevent this application from organizing existing photos into new albums, which was the primary goal of this project.

### Current Functionality

Due to these API limitations, the current script can only:
1. Authenticate with Google Photos
2. Fetch existing media items for a specified year
3. Create a new album

However, it cannot add the fetched media items to the newly created album.

### Why This Matters

This situation highlights the challenges users face when trying to gain more control over their personal data stored in cloud services. While Google Photos provides a great service for storing and viewing photos, the restrictions on the API make it difficult for users to organize their libraries in ways that best suit their needs using third-party tools.

For more details on the API limitations, see this [issue tracker discussion](https://issuetracker.google.com/u/1/issues/132274769).

## Original Project Description

This project aimed to organize existing media items in a user's Google Photos library into albums based on the year they were taken.

## Usage

1. Set up Google Cloud project and enable the Photos Library API.
2. Install required dependencies:
   ```
   pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client
   ```
3. Run the script:
   ```
   python photo_album_creator.py <year> [--no-dryrun] [-v] [--include-archived]
   ```

   Options:
   - `<year>`: The year for which to create the album (required)
   - `--no-dryrun`: Perform actual write operations (default is dry run)
   - `-v`: Increase output verbosity
   - `--include-archived`: Include archived media items

## Setup Instructions

1. **Create a Google Cloud Project**:
   - Go to the [Google Cloud Console](https://console.cloud.google.com/).
   - Click on the project dropdown at the top and select "New Project".
   - Give your project a name and click "Create".

2. **Enable the Google Photos Library API**:
   - In the Google Cloud Console, go to the [API Library](https://console.cloud.google.com/apis/library).
   - Search for "Google Photos Library API" or use this [direct link](https://console.cloud.google.com/marketplace/product/google/photoslibrary.googleapis.com).
   - Click the "Enable" button.

3. **Create OAuth 2.0 credentials**:
   - Go to the [Credentials page](https://console.cloud.google.com/apis/credentials).
   - Click "Create Credentials" and select "OAuth client ID".
   - If prompted, configure the OAuth consent screen:
     - Choose "External" as the user type.
     - Fill in the required fields.
     - Add "localhost" to "Authorized domains" for testing.
     - Add the scope: `https://www.googleapis.com/auth/photoslibrary.readonly`
     - Save and continue.
   - Choose "Desktop app" as the application type.
   - Give your OAuth 2.0 client a name and click "Create".

4. **Download the client configuration**:
   - After creating the OAuth client ID, download the client configuration file.
   - Rename it to `client_secret.json` and place it in the project directory.

5. **Set up the Python environment**:
   - Ensure Python 3.7+ is installed.
   - Create a virtual environment:
     ```
     python -m venv venv
     ```
   - Activate the virtual environment:
     - Windows: `venv\Scripts\activate`
     - macOS/Linux: `source venv/bin/activate`
   - Install required packages:
     ```
     pip install -r requirements.txt
     ```

6. **Add yourself as a test user**:
   - Go to the [Google Cloud Console](https://console.cloud.google.com/).
   - Select your project.
   - Navigate to "APIs & Services" > "OAuth consent screen".
   - Scroll down to the "Test users" section.
   - Click "Add Users".
   - Add your Google email address.
   - Save the changes.

7. **Run the script**:
   ```
   python photo_album_creator.py <year> [--no-dryrun] [-v] [--include-archived]
   ```

   The script will provide a URL and a code. You need to:
   - Visit the URL on a device with a web browser.
   - You may see a warning about the app being unverified. Click "Continue" to proceed.
   - Enter the code provided by the script.
   - Complete the authentication process in the browser.
   - Return to the CLI, where the script will continue execution once authentication is complete.

8. **Subsequent runs** will use saved credentials in `token.pickle`.

## Project Structure

- `photo_album_creator.py`: Main script for the application.
- `requirements.txt`: List of Python package dependencies.
- `.gitignore`: Specifies intentionally untracked files to ignore.
- `README.md`: This file, containing setup instructions and project overview.

## Security Note

Keep your `client_secret.json` file secure and never share it publicly. The `.gitignore` file is set up to prevent accidental commitment of sensitive files.