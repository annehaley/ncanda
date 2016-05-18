#!/usr/bin/env python

##
##  See COPYING file distributed along with the ncanda-data-integration package
##  for the copyright and license terms
##

fields_list = dict()
functions = dict()
output_form = dict()
instrument_list = []

import os
module_dir = os.path.dirname(os.path.abspath(__file__))

import glob
import stat
instruments = [ os.path.basename( d ) for d in glob.glob( os.path.join( module_dir, '*' ) ) if stat.S_ISDIR( os.stat( d ).st_mode ) and os.path.exists( os.path.join( d, '__init__.py' ) ) ]

import sys
sys.path.append( os.path.abspath( os.path.dirname( __file__ ) ) )

import imp
for i in instruments:
#    try:
        module_found = imp.find_module( i, [module_dir] )
        module = imp.load_module( i, module_found[0], module_found[1], module_found[2] )

        instrument_list.append( i )
        fields_list[i] =  module.input_fields
        functions[i] = module.compute_scores
        output_form[i] = module.output_form
#    except:
#        sys.exit( "ERROR: could not import scoring module '%s'" % i )
