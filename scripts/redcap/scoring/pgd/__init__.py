#!/usr/bin/env python
 
##
##  See COPYING file distributed along with the ncanda-data-integration package
##  for the copyright and license terms
##

import pandas
from sibispy import utils as sutils


#
# Variables from surveys needed for PGD
#

# LimeSurvey field names
lime_fields = [ "PGD_sec1 [pgd1]", "PGD_sec1 [pgd2]", "PGD_sec1 [pgd3]", "PGD_sec1 [pgd4]", "PGD_sec1 [pgd5]", "PGD_sec1 [pgd6]", "PGD_sec2 [pgd7]", 
                "PGD_sec2 [pgd8]", "PGD_sec2 [pgd9]", "PGD_sec2 [pgd10]", "PGD_sec2 [pgd11]", "PGD_sec2 [pgd12]" ]

# Dictionary to recover LimeSurvey field names from REDCap names
rc2lime = dict()
for field in lime_fields:
    rc2lime[sutils.label_to_limesurvey_to_redcap( 'youthreport2', field )] = field

# REDCap fields names
input_fields = { 'mrireport' : [ 'youth_report_2_complete',  'youthreport2_missing' ] + rc2lime.keys() }

#
# This determines the name of the form in REDCap where the results are posted.
#
output_form = 'clinical'

#
# PGD field names mapping from R to REDCap
#
R2rc = { 'PGD.SUM' : 'pgd_score' }

#
# Scoring function - take requested data (as requested by "input_fields") for each (subject,event), and demographics (date of birth, gender) for each subject.
#
def compute_scores( data, demographics ):
    # Get rid of all records that don't have YR2
    data.dropna( axis=1, subset=['youth_report_2_complete'] )
    data = data[ data['youth_report_2_complete'] > 0 ]
    data = data[ ~(data['youthreport2_missing'] > 0) ]

    # If no records to score, return empty DF
    if len( data ) == 0:
        return pandas.DataFrame()

    # Replace all column labels with the original LimeSurvey names
    data.columns = sutils.map_labels_to_dict( data.columns, rc2lime )

    # Call the scoring function for all table rows
    scores = data.apply( sutils.run_rscript, axis=1, Rscript='pgd/PGD.R' )

    # Replace all score columns with REDCap field names
    scores.columns = sutils.map_labels_to_dict( scores.columns, R2rc )

    # Simply copy completion status from the input surveys
    scores['pgd_complete'] = data['youth_report_2_complete'].map( int )

    # Make a proper multi-index for the scores table
    scores.index = pandas.MultiIndex.from_tuples(scores.index)
    scores.index.names = ['study_id', 'redcap_event_name']

    # Return the computed scores - this is what will be imported back into REDCap
    outfield_list = [ 'pgd_complete' ] + R2rc.values()
    return scores[ outfield_list ]

