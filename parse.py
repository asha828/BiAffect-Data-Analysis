# Author: Loran Knol
import os
from os.path import join, isfile
import zipfile
import json
from datetime import datetime
import logging
import glob
from tqdm import tqdm
import synapseclient
import pandas as pd


def now_str():
    """
    Returns the current date and time as a string.

    For example: 2024-10-23 11:12:54
    """
    
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def parse_kp(
    zip_ref: zipfile.ZipFile, 
    health_code: str, 
    phone_info: str, 
    app_version: str, 
    session_timestamp: pd.Timestamp, 
    tz: str
) -> pd.DataFrame:
    session = json.loads(zip_ref.open('Session.json').read())
    
    df_kp = pd.DataFrame(session['keylogs'])
    
    df_kp['timestamp'] = pd \
        .to_datetime(df_kp['timestamp'], unit='s', utc=True) \
        .dt.tz_convert(session_timestamp.tz)
    
    df_kp = df_kp.rename(columns={
        'value': 'keypress_type',
        'timestamp': 'keypress_timestamp'
    })
    df_kp = df_kp.drop('uptime', axis='columns')
    
    df_kp['healthCode'] = health_code
    df_kp['phoneInfo'] = phone_info
    df_kp['appVersion'] = app_version
    df_kp['session_timestamp'] = session_timestamp
    df_kp['timezone'] = tz
    
    first_cols = [
        'healthCode',
        'phoneInfo',
        'appVersion',
        'session_timestamp',
        'keypress_timestamp',
        'timezone'
    ]
    df_kp = df_kp[
        [c for c in first_cols if c in df_kp] +
        [c for c in df_kp if c not in first_cols]
    ]
    
    return df_kp


def parse_acc(
    zip_ref: zipfile.ZipFile, 
    health_code: str, 
    phone_info: str, 
    app_version: str, 
    session_timestamp_acc: pd.Timestamp, 
    tz: str
) -> pd.DataFrame:
    motion = json.loads(zip_ref.open('motion.json').read())
    
    df_acc = pd.DataFrame(motion)
    
    df_acc['timestamp'] = pd.to_timedelta(df_acc['timestamp'], unit='s')
    
    df_acc['timestamp'] = pd.to_datetime(df_acc['timestampDate'])[0] \
        + pd.to_timedelta(df_acc['timestamp'], unit='s')
    
    df_acc = df_acc.drop([
        'uptime',
        'timestampDate',
        'stepPath',
        'sensorType'
    ], axis='columns')
    
    df_acc['healthCode'] = health_code
    df_acc['phoneInfo'] = phone_info
    df_acc['appVersion'] = app_version
    df_acc['session_timestamp'] = session_timestamp_acc
    df_acc['timezone'] = tz
    
    first_cols = [
        'healthCode',
        'phoneInfo',
        'appVersion',
        'session_timestamp',
        'timestamp',
        'timezone'
    ]
    df_acc = df_acc[
        [c for c in first_cols if c in df_acc] +
        [c for c in df_acc if c not in first_cols]
    ]
    
    df_acc = df_acc.dropna()
    
    return df_acc


def parse_file(
    zip_path: str,
    health_code: str
) -> tuple[pd.DataFrame, pd.DataFrame] | None:
    """
    Parse BiAffect KeyboardSession zip file downloaded from Synapse.

    Parameters
    ----------
    zip_path: str
        Path to the zip file.
    health_code: str
        Health code of the user that generated the data in the zip file.

    Returns
    -------
    dat_tuple: tuple[pd.DataFrame, pd.DataFrame] | None
        A tuple of the key press and accelerometer data frames, respectively.
        If an error occurred during parsing, returns None instead.
    """
    
    try:
        zip_ref = zipfile.ZipFile(zip_path)
        
        # Retrieve and parse metadata
        metadata = json.loads(zip_ref.open('metadata.json').read())
        meta_files_df = pd.DataFrame(metadata['files'])
        
        app_version = metadata['appVersion'].replace(',', ';')
        phone_info = metadata['deviceInfo']
        
        # Should be timezone-aware
        session_timestamp = pd.to_datetime(
            meta_files_df.loc[
                meta_files_df['identifier'] == 'KeyboardSession', 
                'timestamp'
            ].values[0]
        )
        session_timestamp_acc = pd.to_datetime(
            meta_files_df.loc[
                meta_files_df['identifier'] == 'motion', 
                'timestamp'
            ].values[0]
        )
        tz = session_timestamp.tzname()

        # Retrieve and parse keypress and accelerometer data, then return
        dat_kp = parse_kp(
            zip_ref, health_code, phone_info,
            app_version, session_timestamp, tz)

        dat_acc = parse_acc(
            zip_ref, health_code, phone_info,
            app_version, session_timestamp_acc, tz)

        return dat_kp, dat_acc
    except Exception:
        # Logs the current exception, including traceback
        logging.exception(f"{now_str()}: Exception for {zip_path}. Skipping.")
        return None
    finally:
        try:
            zip_ref.close()
        except Exception:
            # Logs the current exception, including traceback
            logging.exception(f"{now_str()}: Exception for {zip_path} while closing file.")
            return None


# Pulls files one by one. Slow and error-prone.
def pull_file(
    # syn: synapseclient.Synapse, 
    file_id: str,
    iteration: int
) -> tuple[pd.DataFrame, pd.DataFrame] | None:
    print(f"{now_str()}: Parsing file {iteration}...")
    
    try:
        syn = synapseclient.Synapse()
        syn.login(silent=True)
        
        file = syn.get(file_id, downloadLocation=os.environ['TMPDIR'], 
                       ifcollision='keep.local')
        
        health_code = file.healthCode[0]
        
        zip_path = join(os.environ['TMPDIR'], file.name)
        zip_ref = zipfile.ZipFile(zip_path)
        
        # Retrieve and parse metadata
        metadata = json.loads(zip_ref.open('metadata.json').read())
        meta_files_df = pd.DataFrame(metadata['files'])
        
        app_version = metadata['appVersion'].replace(',', ';')
        phone_info = metadata['deviceInfo']
        
        # Should be timezone-aware
        session_timestamp = pd.to_datetime(
            meta_files_df.loc[
                meta_files_df['identifier'] == 'KeyboardSession', 
                'timestamp'
            ].values[0]
        )
        session_timestamp_acc = pd.to_datetime(
            meta_files_df.loc[
                meta_files_df['identifier'] == 'motion', 
                'timestamp'
            ].values[0]
        )
        tz = session_timestamp.tzname()

        # Retrieve and parse keypress and accelerometer data, then return
        dat_kp = parse_kp(
            zip_ref, health_code, phone_info,
            app_version, session_timestamp, tz)
        # dat_kp.to_parquet(
        #     join(out_path, 'keypress', f"alex_kp_{file.name}"))

        dat_acc = parse_acc(
            zip_ref, health_code, phone_info,
            app_version, session_timestamp_acc, tz)
        # dat_acc.to_parquet(
        #     join(out_path, 'accelerometer', f"alex_acc_{file.name}"))

        return dat_kp, dat_acc
    except Exception:
        # Logs the current exception, including traceback
        logging.exception(f"{now_str()}: Exception for {file.name}. Skipping.")
        return None
    finally:
        try:
            zip_ref.close()
        except Exception:
            # Logs the current exception, including traceback
            logging.exception(f"{now_str()}: Exception for file {iteration} while closing zip file.")
            return None


def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


# Legacy code
def bundle_files(file_ids: str, chunk: int):
    print(f"{now_str()}: Working on chunk {chunk}...")

    try:
        chunk_path = join(out_path, f"dat_acc_chunk_{chunk}.parquet")
    
        if isfile(chunk_path):
            print(f"{now_str()}: Chunk {chunk} has already been downloaded. Skipping.")
            return
    
        offset = chunk * len(file_ids)
        dats = [pull_file(fid, i + offset) for i, fid in enumerate(file_ids)]
    
        dats_kp = [df_tup[0] for df_tup in dats if df_tup is not None]
        df_kp = pd.concat(dats_kp)
        df_kp.to_parquet(join(out_path, f"dat_kp_chunk_{chunk}.parquet"))
    
        dats_acc = [df_tup[1] for df_tup in dats if df_tup is not None]
        df_acc = pd.concat(dats_acc)
        df_acc.to_parquet(chunk_path)
    
        print(f"{now_str()}: Finished chunk {chunk}.")
    except Exception:
        logging.exception(f"{now_str()}: Exception for chunk {chunk}. Skipping.")


if __name__ == '__main__':
    download_dir = TMPDIR  # TMPDIR is specific to the Donders HPC
    dat_dir = TMPDIR

    # Filter files to parse
    # Not all files are zip files, make selection based on hc_df below
    print('Collecting zip paths...')
    zip_paths = glob.glob(join(download_dir, '**'), recursive=True)
    zip_paths = [zp for zp in tqdm(zip_paths) if isfile(zp)]

    # Get a list of health codes based on file names
    hc_df = pd.read_parquet(join(download_dir, 'hc_df.parquet'))
    # Throw away rows with duplicated file names
    hc_df = hc_df[~hc_df.index.duplicated(keep='first')]

    # Merge health codes and paths based on file names
    zip_names = [os.path.basename(zp) for zp in zip_paths]
    zip_df = pd.DataFrame({'path': zip_paths}, index=zip_names)
    zip_df = zip_df[~zip_df.index.duplicated(keep='first')]

    hc_zip_df = hc_df.merge(zip_df, left_index=True, right_index=True)
    hcs = hc_zip_df['healthCode']
    zps = hc_zip_df['path']

    # Parse all files to (dat_kp, dat_acc) DataFrame tuple
    print('Parsing zip files...')
    parsed_tups = [parse_file(zp, hc) for zp, hc in zip(tqdm(zps), hcs)]

    # Concatenate key press and accelerometer data to single data frames
    dats_kp = [df_tup[0] for df_tup in parsed_tups if df_tup is not None]
    df_kp = pd.concat(dats_kp)
    
    dats_acc = [df_tup[1] for df_tup in parsed_tups if df_tup is not None]
    df_acc = pd.concat(dats_acc)

    # Save them to file
    df_kp.to_parquet(join(dat_dir, 'dat_kp.parquet'))
    df_acc.to_parquet(join(dat_dir, 'dat_acc.parquet'))
