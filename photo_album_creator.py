import os
import pickle
import argparse
import traceback
import time
import threading
from google_auth_oauthlib.flow import InstalledAppFlow, Flow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from datetime import datetime
import logging

SCOPES = ['https://www.googleapis.com/auth/photoslibrary']

def setup_logging(verbose):
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

def activity_indicator(stop):
    animation = "|/-\\"
    idx = 0
    while not stop():
        print(f"\rFetching media items... {animation[idx % len(animation)]}", end="", flush=True)
        idx += 1
        time.sleep(0.1)

def get_authenticated_service():
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = Flow.from_client_secrets_file(
                'client_secret.json', SCOPES, redirect_uri='urn:ietf:wg:oauth:2.0:oob')
            auth_url, _ = flow.authorization_url(prompt='consent')
            
            logging.info(f'Please go to this URL and authorize the application: {auth_url}')
            code = input('Enter the authorization code: ')
            flow.fetch_token(code=code)
            creds = flow.credentials
        
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    return creds

def get_media_items_for_year(service, year, verbose, include_archived=False):
    results = []
    page_token = None
    stop_indicator = False
    
    def stop():
        return stop_indicator

    indicator_thread = threading.Thread(target=activity_indicator, args=(stop,))
    indicator_thread.start()
    
    try:
        while True:
            body = {
                "pageSize": 100,
                "pageToken": page_token,
                "filters": {
                    "dateFilter": {
                        "ranges": [{
                            "startDate": {"year": year, "month": 1, "day": 1},
                            "endDate": {"year": year+1, "month": 1, "day": 1}
                        }]
                    },
                    "includeArchivedMedia": include_archived,
                    "mediaTypeFilter": {
                        "mediaTypes": ["ALL_MEDIA"]
                    }
                }
            }
            response = service.mediaItems().search(body=body).execute()
            
            items = response.get('mediaItems', [])
            valid_items = [item for item in items if 'id' in item]
            results.extend(valid_items)
            logging.info(f"Fetching media items... Found {len(results)} items")
            
            page_token = response.get('nextPageToken')
            if not page_token:
                break
    except Exception as e:
        logging.error(f"Error in get_media_items_for_year: {str(e)}")
        traceback.print_exc()
    finally:
        stop_indicator = True
        indicator_thread.join()
        logging.info("Media item fetching completed")
    
    return results

def create_album(service, title, dry_run, verbose):
    if dry_run:
        logging.info(f"Dry run: Would create album '{title}'")
        return {"id": "dry_run_album_id", "title": title}
    try:
        if verbose:
            logging.info(f"Creating album '{title}'")
        album = service.albums().create(body={"album": {"title": title}}).execute()
        if verbose:
            logging.info(f"Album created with ID: {album['id']}")
        return album
    except HttpError as error:
        logging.error(f'An error occurred while creating the album: {error}')
        return None

def add_media_items_to_album(service, album_id, media_items, dry_run, verbose):
    if dry_run:
        logging.info(f"Dry run: Would add {len(media_items)} items to album {album_id}")
        return

    batch_size = 50
    for i in range(0, len(media_items), batch_size):
        batch = media_items[i:i+batch_size]
        media_item_ids = [item['id'] for item in batch]
        
        request_body = {
            'mediaItemIds': media_item_ids
        }
        
        try:
            response = service.albums().batchAddMediaItems(albumId=album_id, body=request_body).execute()
            if verbose:
                logging.info(f"Added {len(media_item_ids)} items to album")
        except HttpError as error:
            logging.error(f'Error adding items to album: {error}')
            # You might want to add more detailed error handling here

def get_album_item_count(service, album_id):
    try:
        response = service.mediaItems().search(body={"albumId": album_id, "pageSize": 1}).execute()
        return response.get('totalMediaItems', 0)
    except HttpError as error:
        logging.error(f'An error occurred while getting album item count: {error}')
        return 0

def main():
    parser = argparse.ArgumentParser(description="Google Photos Album Creator")
    parser.add_argument("year", type=int, help="Year for which to create the album")
    parser.add_argument("--no-dryrun", action="store_true", help="Perform actual write operations")
    parser.add_argument("-v", "--verbose", action="store_true", help="Increase output verbosity")
    parser.add_argument("--include-archived", action="store_true", help="Include archived media items")
    args = parser.parse_args()

    year = args.year
    dry_run = not args.no_dryrun
    verbose = args.verbose

    setup_logging(verbose)

    logging.info("Welcome to the Google Photos Album Creator!")
    logging.info("Authenticating...")
    creds = get_authenticated_service()
    logging.info("Authentication successful!")

    try:
        service = build('photoslibrary', 'v1', credentials=creds, static_discovery=False)
        
        default_album_title = f"Photos from {year}"
        
        if verbose:
            logging.info("Checking for existing albums...")
        results = service.albums().list(pageSize=50).execute()
        albums = results.get('albums', [])
        existing_album = next((album for album in albums if album['title'] == default_album_title), None)
        
        if existing_album:
            item_count = get_album_item_count(service, existing_album['id'])
            if item_count > 0:
                logging.info(f"Album '{default_album_title}' already exists and contains {item_count} items.")
                album_title = input("Enter a new album name (or press Enter to use the existing album): ").strip()
                if not album_title:
                    album_title = default_album_title
                    album_id = existing_album['id']
                else:
                    new_album = create_album(service, album_title, dry_run, verbose)
                    if new_album:
                        logging.info(f"{'Dry run: Would create' if dry_run else 'Created'} new album: {album_title}")
                        album_id = new_album['id']
                    else:
                        logging.error("Failed to create the album. Exiting.")
                        return
            else:
                logging.info(f"Empty album '{default_album_title}' already exists. Using this album.")
                album_title = default_album_title
                album_id = existing_album['id']
        else:
            album_title = default_album_title
            new_album = create_album(service, album_title, dry_run, verbose)
            if new_album:
                logging.info(f"{'Dry run: Would create' if dry_run else 'Created'} new album: {album_title}")
                album_id = new_album['id']
            else:
                logging.error("Failed to create the album. Exiting.")
                return

        logging.info(f"Fetching media items for {year}...")
        media_items = get_media_items_for_year(service, year, verbose, args.include_archived)
        
        if not media_items:
            logging.info(f"No media items found for {year}.")
        else:
            logging.info(f"Found {len(media_items)} media items.")
            try:
                add_media_items_to_album(service, album_id, media_items, dry_run, verbose)
            except KeyboardInterrupt:
                logging.info("Operation interrupted by user. Exiting...")
            if not dry_run:
                logging.info(f"Successfully added {len(media_items)} items to the album '{album_title}'.")
            else:
                logging.info(f"Dry run: Would add {len(media_items)} items to the album '{album_title}'.")

    except Exception as error:
        logging.error(f'An error occurred: {str(error)}')
        traceback.print_exc()
    except KeyboardInterrupt:
        logging.info("Operation interrupted by user. Exiting...")

if __name__ == '__main__':
    main()