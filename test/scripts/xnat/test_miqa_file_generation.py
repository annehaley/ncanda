#!/usr/bin/env python

##
##  Copyright 2017 SRI International
##  See COPYING file distributed along with the package for the copyright and license terms
##

from __future__ import print_function
from builtins import next
import os
import sys
import filecmp
import glob
import re
from tabnanny import verbose
import pandas as pd 
from unittest.mock import patch
import pytest
import sibispy
from sibispy.tests.utils import get_session
current_dir=os.path.dirname(__file__)
# sys.path.append(os.path.join(current_dir, '../../../'))
sys.path.append(os.path.join(current_dir, '../../../scripts/xnat'))
# import miqa_file_generation_ as miqa_file_generation
import miqa_file_generation
import upload_visual_qc


@pytest.fixture
def project_list():
    return ["DUKE", "OHSU", "SRI", "UCSD", "UPMC"]


@pytest.fixture
def sibis_session():
    sibispy.sibislogger.init_log(verbose=True)

    sibis_session = sibispy.Session()
    if not sibis_session.configure():
        print("Error: session configure file was not found")
        sys.exit()
    
    return sibis_session

@pytest.mark.parametrize("file_prefix",
                         ["test_miqa_file_generation",
                          "test_miqa_file_generation_2"])
def test_read_write_json(file_prefix, sibis_session, project_list):
    # Read Json file
    file_name=file_prefix +".json"
    orig_file=os.path.join(current_dir,file_name)
    assert(os.path.exists(str(orig_file)))    
    json_dict = miqa_file_generation.read_miqa_import_file(file_name, current_dir)

    # Write out Json File
    created_file=os.path.join("/tmp",file_name)
    if os.path.exists(created_file):
        os.remove(created_file)
        
    miqa_file_generation.write_miqa_import_file(json_dict, file_name, "/tmp")
     
    # Compare_File
    # print(orig_file,created_file)
    assert(filecmp.cmp(orig_file,created_file))


@pytest.mark.parametrize("file_prefix",
                         ["test_miqa_file_generation_bad"])
def test_read_bad_json(file_prefix, sibis_session, project_list):
    # Read Json file
    file_name=file_prefix +".json"
    orig_file=os.path.join(current_dir,file_name)
    assert(os.path.exists(str(orig_file)))    
    json_dict = miqa_file_generation.read_miqa_import_file(file_name, current_dir)
    assert json_dict == {}, "Json dict should be empty bc read from bad file"
 
@pytest.mark.parametrize("file_prefix",
                        [
                            "test_miqa_file_generation",
                            "test_miqa_file_generation_2"
                        ])
def test_json_convert_check_new_sessions_df(file_prefix):
    # Read Json file
    # print(" test_json_convert_check_new_sessions_df", file_prefix)
    file_name=file_prefix +".json"
    orig_file=os.path.join(current_dir,file_name)
    assert(os.path.exists(str(orig_file)))    
    json_dict = miqa_file_generation.read_miqa_import_file(file_name, current_dir)
    json_df: pd.DataFrame = miqa_file_generation.convert_json_to_check_new_sessions_df(json_dict)

    # Read legacy CSV file
    csv_file=os.path.join(current_dir,file_prefix + ".csv")
    csv_df: pd.DataFrame = upload_visual_qc.read_csf_file(csv_file)
    
    # sort so we are comparing similar thing
    dataframe_cols = csv_df.columns.to_list()
    json_df = json_df.sort_values(by=dataframe_cols).reset_index(drop=True)
    csv_df = csv_df.sort_values(by=dataframe_cols).reset_index(drop=True)
    
    df_diffs = csv_df.compare(json_df)
    assert len(df_diffs) == 0, "DataFrames should be identical."

    


@pytest.mark.parametrize("file_name",
                        [
                            "test_miqa_file_generation_write.json"
                        ])
def test_write_to_json_(file_name):

    scans_to_qc = ['xnat_experiment_id,nifti_folder,scan_id,scan_type,experiment_note,decision,scan_note\n', 'NCANDA_E11640,/fs/storage/XNAT/archive/ohsu_incoming/arc001/D-00155-M-0-20220818/RESOURCES/nifti,2,ncanda-t2fse-v1,"",0,"UF(2022-09-01): uf UF(2022-09-01): this person&apos;s white matter looks unusual (torn and falling apart)"\n', 'NCANDA_E11640,/fs/storage/XNAT/archive/ohsu_incoming/arc001/D-00155-M-0-20220818/RESOURCES/nifti,3,ncanda-mprage-v1,"",0,"UF(2022-09-01): this person&apos;s white matter looks unusual (torn and falling apart)"\n', 'NCANDA_E11640,/fs/storage/XNAT/archive/ohsu_incoming/arc001/D-00155-M-0-20220818/RESOURCES/nifti,4,ncanda-dti6b500pepolar-v1,"",0,"UF(2022-09-01): this person&apos;s T1/T2 white matter looks unusual (torn and falling apart)"\n', 'NCANDA_E11640,/fs/storage/XNAT/archive/ohsu_incoming/arc001/D-00155-M-0-20220818/RESOURCES/nifti,6,ncanda-dti60b1000-v1,"",0,"UF(2022-09-01): this person&amp;apos;s T1/T2 white matter looks unusual (torn and falling apart)"\n', 'NCANDA_E11640,/fs/storage/XNAT/archive/ohsu_incoming/arc001/D-00155-M-0-20220818/RESOURCES/nifti,12,ncanda-dti30b400-v1,"",0,"UF(2022-09-01): this person&apos;s T1/T2 white matter looks unusual (torn and falling apart)"\n', 'NCANDA_E11640,/fs/storage/XNAT/archive/ohsu_incoming/arc001/D-00155-M-0-20220818/RESOURCES/nifti,18,ncanda-grefieldmap-v1,"",0,"UF(2022-09-01): this person&apos;s T1/T2 white matter looks unusual (torn and falling apart)"\n', 'NCANDA_E11640,/fs/storage/XNAT/archive/ohsu_incoming/arc001/D-00155-M-0-20220818/RESOURCES/nifti,19,ncanda-grefieldmap-v1,"",0,"UF(2022-09-01): this person&apos;s T1/T2 white matter looks unusual (torn and falling apart)"\n', 'NCANDA_E11640,/fs/storage/XNAT/archive/ohsu_incoming/arc001/D-00155-M-0-20220818/RESOURCES/nifti,20,ncanda-rsfmri-v1,"",0,"UF(2022-09-01): this person&apos;s T1/T2 white matter looks unusual (torn and falling apart)"\n', 'NCANDA_E11678,/fs/storage/XNAT/archive/ucsd_incoming/arc001/E-99999-P-9-20220831/RESOURCES/nifti,3,ncanda-t1spgr-v1,"",0,"MP(2022-09-16): Hole in the phantom"\n', 'NCANDA_E11718,/fs/storage/XNAT/archive/duke_incoming/arc001/C-00000-P-0-20220906/RESOURCES/nifti,3,ncanda-rsfmri-v1,"",0,"MP(2022-09-16): Damaged Phantom"\n', 'NCANDA_E11749,/fs/storage/XNAT/archive/duke_incoming/arc001/C-00000-P-0-20220912/RESOURCES/nifti,3,ncanda-rsfmri-v1,"",0,"UF(2022-09-22): damaged phantom"\n', 'NCANDA_E11782,/fs/storage/XNAT/archive/sri_incoming/arc001/B-00000-P-0-20221006/RESOURCES/nifti,3,ncanda-rsfmri-v1,"",0,"UF(2022-10-10): UF: damaged phantom"\n', 'NCANDA_E11788,/fs/storage/XNAT/archive/duke_incoming/arc001/C-00000-P-0-20221006/RESOURCES/nifti,3,ncanda-rsfmri-v1,"",0,"UF(2022-10-10): phantom damaged"\n']
        
     # "xnat_experiment_id,nifti_folder,scan_id,scan_type,experiment_note,decision,scan_note\n"]
    #scans_to_qc.append('NCANDA_E11836,/fs/storage/XNAT/archive/sri_incoming/arc001/B-00350-M-2-20221014/RESOURCES/nifti,3,ncanda-t2fse-v1,"",,""\n')
    created_file=os.path.join("/tmp",file_name)
    if os.path.exists(created_file):
        os.remove(created_file)

    successFlag = miqa_file_generation.write_miqa_import_file(scans_to_qc, file_name, "/tmp")

    assert successFlag == False, "Writing Json file should have failed bc it is not correct dictionary" 

    # turn into json dictionary
    rows_cols = [row.split(',') for row in scans_to_qc]
    df = pd.DataFrame(rows_cols[1:], columns=rows_cols[0])
    new_df = miqa_file_generation.convert_dataframe_to_new_format(df)
    scans_to_qc_json_dict = miqa_file_generation.import_dataframe_to_dict(new_df)

    successFlag = miqa_file_generation.write_miqa_import_file(scans_to_qc_json_dict, file_name, "/tmp")

    assert successFlag == True, "Writing Json file should have been successsfull " 
