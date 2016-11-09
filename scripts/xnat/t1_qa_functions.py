#!/usr/bin/env python

##
##  See COPYING file distributed along with the ncanda-data-integration package
##  for the copyright and license terms
##

import os
import re
import json
import shutil
import tempfile
import subprocess
import hashlib

import sibis

# Check the phantom XML file for various thresholds
def check_xml_file( xml_file, project, session, label ):
    xml = open( xml_file, 'r' )

    warnings = []
    try:
        for line in xml:
            # Check fallbacks triggered
            if 'fallbackOrientationCNR' in line:
                warnings.append( "CNR spheres used for orientation - problem detecting 15mm spheres?" )
            if 'fallbackCentroidCNR' in line:
                match = re.match( '^.*distance="([0-9]+\.[0-9]+)".*$', line )
                distance = float( match.group(1) )
                if distance > 3.0:
                    warnings.append( "CNR spheres used for centroid location (distance to SNR center = %f mm) - problem with the SNR sphere?" % distance )

            # Check number of landmarks
            match = re.match( '<landmarkList.*count="([0-9]+)">', line )
            if match:
                count = int( match.group(1) )
                if ( count < 165 ):
                    warnings.append( "Landmark count=%d" % (project,session,count) )

            # Check SNR
            match = re.match( '<snr>([0-9]*\.[0-9]*)</snr>', line )
            if match:
                snr = float( match.group(1) )
                if ( snr < 50 ):
                    warnings.append( "Low SNR=%f" % (project,session,snr) )

            # Check scale
            match = re.match( '<scale>([0-9]*\.[0-9]*)\s+([0-9]*\.[0-9]*)\s+([0-9]*\.[0-9]*)</scale>', line )
            if match:
                for idx in [0,1,2]:
                    scale = float( match.group( idx+1 ) )
                    if ( (scale < 0.99) or (scale > 1.01) ):
                        warnings.append( "Non-unit scale[%d]=%f" % (project,session,idx,scale) )

            # Check nonlinearity
            match = re.match( '<nonlinear>([0-9]*\.[0-9]*)\s+([0-9]*\.[0-9]*)\s+([0-9]*\.[0-9]*)</nonlinear>', line )
            if match:
                for idx in [0,1,2]:
                    nonlinear = float( match.group( idx+1 ) )
                    if ( (nonlinear > 0.5) ):
                        warnings.append( "Nonlinearity[%d]=%f" % (project,session,idx,nonlinear) )
    except:
         error='Could not open XML file for experiment.'
         sibis.logging(session,error,
                     project_id=project)


    finally:
        xml.close()

    # Print warnings if there were any
    if len( warnings ) > 0:
        warning = " ".join(warnings)
        sibis.logging(label, warning,
                      session_id=session,
                      project=project,
                      script='t1_qa_functions')


# Run ADNI Phantom QA procedure on a single scan series
def run_phantom_qa( interface, project, subject, session, label, dicom_path ):
    # Make a temporary directory
    temp_dir = tempfile.mkdtemp()

    # Switch to temp directory
    original_wd = os.getcwd()
    os.chdir( temp_dir )

    # Create NIFTI file from the DICOM files
    nii_file = 't1.nii.gz'
    subprocess.call( 'cmtk dcm2image --tolerance 1e-3 -rO %s %s >& /dev/null' % ( nii_file, dicom_path ), shell=True )
    if not os.path.exists( nii_file ):
        error = "ERROR: NIFTI file was not created from DICOM files experiment"
        sibis.logging('{}/{}'.format(project,session),error,
                         session = session,
                         project = project,
                         nii_file = nii_file,
                         dicom_path = dicom_path)
        return

    # Upload NIFTI file
    try:
        file = interface.select.project( project ).subject( subject ).experiment( session ).resource('QA').file( nii_file )
        file.insert( nii_file, format='nifti_gz', tags='qa,adni,nifti_gz', content='ADNI Phantom QA File', overwrite=True )
    except:
        print "Something bad happened uploading file %s to Experiment %s/%s/%s" % (nii_file,project,session,label)

    # Run the PERL QA script and capture its output
    xml_file = 'phantom.xml'
    lbl_file = 'phantom.nii.gz'
    subprocess.call( 'cmtk detect_adni_phantom --tolerant --refine-xform --erode-snr 15 --write-labels %s %s %s' % ( lbl_file, nii_file, xml_file ), shell=True )
    if not os.path.exists( xml_file ) or not os.path.exists( lbl_file ):
        error = "ERROR: mandatory output file (either xml or label image) was not created from file %s, experiment %s/%s/%s" % ( nii_file,project,session,label )
        sibis.logging('{}/{}/{}'.format(project,session,label),error,
                       nii_file=nii_file,
                       project = project,
                       session = session,
                       label= label)
        return

    # Upload phantom files to XNAT
    for (fname,fmt) in [ (xml_file, 'xml'), (lbl_file, 'nifti_gz') ]:
        try:
            file = interface.select.project( project ).subject( subject ).experiment( session ).resource('QA').file( fname )
            file.insert( fname, format=fmt, tags='qa,adni,%s' % fmt, content='ADNI Phantom QA File', overwrite=True )
        except:
            print "Something bad happened uploading file %s to Experiment %s/%s" % (fname,project,session)

    # Read and evaluate phantom XML file
    check_xml_file( xml_file, project, session, label )

    # Clean up - remove temp directory
    os.chdir( original_wd )
    shutil.rmtree( temp_dir )


# Process a phantom MR imaging session
def process_phantom_session( interface, project, subject, session, label, force_updates=False ):
    # Get the experiment object
    experiment = interface.select.experiment( session )
    # First, see if the QA files are already there
    files = experiment.resources().files().get()
    if force_updates or not (('t1.nii.gz' in files) and ('phantom.xml' in files) and ('phantom.nii.gz' in files)):
        dicom_path=''

        # Get list of all scans in the session
        scans = experiment.scans().get()
        for scan in scans:
            # Check only 'usable' scans with the proper name
            [scan_type,quality] = experiment.scan( scan ).attrs.mget( ['type', 'quality'] )
            if ('mprage' in scan_type) or ('t1spgr' in scan_type):
                # Extract the DICOM file directory from the XML representation
                match = re.match( '.*(/fs/storage/XNAT/.*)scan_.*_catalog.xml.*', experiment.scan( scan ).get(), re.DOTALL )
                if match:
                    dicom_path = match.group(1)

        if dicom_path:
            # If we found a matching scan, run the QA
            run_phantom_qa( interface, project, subject, session, label, dicom_path )
        else:
            # If there was no matching scan in the session, print a warning
            warning = "WARNING: ADNI phantom session: {}, experiment: {}, subject: {} does not have \
                       a usable T1-weighted scan".format(session, experiment, subject)
            sibis.logging(hashlib.sha1('t1_qa_functions').hexdigest()[0:6], warning,
                          script='t1_qa_functions')
