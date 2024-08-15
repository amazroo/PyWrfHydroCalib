# General function library for creating namelist.hrldas and hydro.namelist 
# files using information the user provided, and basin-specific information.

# Logan Karsten
# National Center for Atmospheric Research 
# Research Applications Laboratory

import os
from yaml import SafeDumper
import yaml
import warnings
warnings.filterwarnings("ignore")
import datetime

def createHrldasNL(statusData,gageData,jobData,outDir,typeFlag,bDate,eDate,genFlag):
    # General function for creation of a namelist.hrldas file.
    
    # NOTE: typeFlag = 1 indicates cold start.
    #       typeFlag = 2 indicates restart.
    #       typeFlag = 3 indicates this is the initialization of a new model
    #                    simulation for either a calibration iteration, or 
    #                    sensitivity simulation, or a validation simulation. 
    # NOTE: genFlag = 0 indicates a spinup - pull all parameter files from 
    #                   gageData
    #       genFlag = 1 indicartes a calibration - pull HYDRO_TBL_2D.nc, Fulldom.nc,
    #                   GWBUCKPARM.nc, and soil_properties.nc from the run directory.
    #       genFlag = 2 Indicates validation CTRL - pull HYDRO_TBL_2D.nc, Fulldom.nc,
    #                   GWBUCKPARM.nc, and soil_properties.nc from calibration output.
    #       genFlag = 3 Indicates validation BEST - pull HYDRO_TBL_2D.nc, Fulldom.nc,
    #                   GWBUCKPARM.nc, and soil_properties.nc from calibration output.
    #       genFlag = 4 Indicates sensitivy analysis - HYDRO_TBL_2D.nc, Fulldom.nc,
    #                   GWBUCKPARM.nc, and soil_properties.nc from run directory
    # Create path for the namelist file
    pathOut = outDir + "/namelist.hrldas"
    if os.path.isfile(pathOut):
        os.remove(pathOut)
    
    # If this is a calibration simulation, we need to check to see if we are 
    # past the date of minimal outputs. If the user specified to turn this optional
    # feature off, then by default, all simulations will produce full outputs
    # for the entire calibration iteration simulation.
    if jobData.optCalStripFlag == 1:
        minOutFlag = 1
        if bDate >= jobData.bCalibFullOutputs:
            minOutFlag = 0
        else:
            minOutFlag = 1
    else:
        minOutFlag = 0
        
    # Write each line of the expected hrldas.namelist file.
    try:
        fileObj = open(pathOut,'w')
        fileObj.write('&NOAHLSM_OFFLINE\n')
        fileObj.write('\n')
        inStr = ' HRLDAS_SETUP_FILE = "' + str(gageData.wrfInput) + '"' + '\n'
        fileObj.write(inStr)
        inStr = ' INDIR = "' + str(gageData.forceDir) + '"' + '\n'
        fileObj.write(inStr)
        if genFlag == 0:
            inStr = ' SPATIAL_FILENAME = "' + str(gageData.soilFile) + '"' + '\n'
        if genFlag == 1:
            pthTmp = str(jobData.outDir) + "/" + str(jobData.jobName) + "/" + \
                     str(gageData.gage) + "/RUN.CALIB/OUTPUT/lis.nc"
            if not os.path.isfile(pthTmp):
                statusData.errMsg = "ERROR: Failure to find: " + pthTmp
                raise Exception()
            inStr = ' SPATIAL_FILENAME = "' + pthTmp + '"' + '\n'
        if genFlag == 2:
            pthTmp = str(jobData.outDir) + "/" + str(jobData.jobName) + "/" + \
                     str(gageData.gage) + "/RUN.VALID/OUTPUT/CTRL/lis.nc"
            if not os.path.isfile(pthTmp):
                statusData.errMsg = "ERROR: Failure to find: " + pthTmp
                raise Exception()
            inStr = ' SPATIAL_FILENAME = "' + pthTmp + '"' + '\n'
        if genFlag == 3:
            pthTmp = str(jobData.outDir) + "/" + str(jobData.jobName) + "/" + \
                     str(gageData.gage) + "/RUN.VALID/OUTPUT/BEST/lis.nc"
            if not os.path.isfile(pthTmp):
                statusData.errMsg = "ERROR: Failure to find: " + pthTmp
                raise Exception()
            inStr = ' SPATIAL_FILENAME = "' + pthTmp + '"' + '\n'
        if genFlag == 4:
            pthTmp = outDir + "/lis.nc"
            if not os.path.isfile(pthTmp):
                statusData.errMsg = "ERROR: Failure to find: " + pthTmp
                raise Exception()
            inStr = ' SPATIAL_FILENAME = "' + pthTmp + '"' + '\n'
        fileObj.write(inStr)
        inStr = ' OUTDIR = "' + outDir + '"' + '\n'
        fileObj.write(inStr)
        fileObj.write('\n')
        if minOutFlag == 1:
            # Only run simulation to the end of the mimimal output time period. 
            # The workflow will then restart the model with full output after 
            # it has seen it's passed this point.
            dt = jobData.bCalibFullOutputs - bDate
        else:
            dt = eDate - bDate
        inStr = ' START_YEAR = ' + bDate.strftime('%Y') + '\n'
        fileObj.write(inStr)
        inStr = ' START_MONTH = ' + bDate.strftime('%m') + '\n'
        fileObj.write(inStr)
        inStr = ' START_DAY = ' + bDate.strftime('%d') + '\n'
        fileObj.write(inStr)
        fileObj.write(' START_HOUR = ' + bDate.strftime('%H') + '\n')
        fileObj.write(' START_MIN = ' + bDate.strftime('%M') + '\n')
        fileObj.write('\n')
        if typeFlag == 2:
            # We are restarting a model simulation that either failed, or was killed. 
            rstFile = outDir + "/RESTART." + bDate.strftime('%Y%m%d') + "00_DOMAIN1"
            if not os.path.isfile(rstFile):
                statusData.errMsg = "ERROR: Failure to find: " + rstFile
                raise Exception()
            inStr = ' RESTART_FILENAME_REQUESTED = ' + "'" + rstFile + "'" + '\n'
        if typeFlag == 1:
            # We are cold-starting this simulation. This will most likely be for
            # spinup purposes.
            inStr = ' RESTART_FILENAME_REQUESTED = ' + "'" + "'" + '\n' 
        if typeFlag == 3:
            # This is the beginning of a new sensitivity/calibration/validation
            # simulation.
            if jobData.coldStart == 1:
                inStr = ' RESTART_FILENAME_REQUESTED = ' + "'" + "'" + '\n'
            if jobData.optSpinFlag == 1:
                inStr = ' RESTART_FILENAME_REQUESTED = ' + "'" + gageData.optLandRstFile + "'\n"
            if jobData.optSpinFlag == 0 and jobData.coldStart == 0:
                rstFile = outDir + "/RESTART." + bDate.strftime('%Y%m%d') + "00_DOMAIN1"
                inStr = ' RESTART_FILENAME_REQUESTED = ' + "'" + rstFile + "'" + '\n'
        fileObj.write(inStr)
        fileObj.write('\n')
        fileObj.write(' ! Specification of simulation length in days OR hours\n')
        inStr = ' KDAY = ' + str(dt.days) + '\n'
        fileObj.write(inStr)
        fileObj.write('\n')
        fileObj.write(' ! Physics options (see the documentation for details)\n')
        inStr = ' DYNAMIC_VEG_OPTION = ' + str(jobData.dynVegOpt) + '\n'
        fileObj.write(inStr)
        inStr = ' CANOPY_STOMATAL_RESISTANCE_OPTION = ' + str(jobData.canStomOpt) + '\n'
        fileObj.write(inStr)
        inStr = ' BTR_OPTION = ' + str(jobData.btrOpt) + '\n'
        fileObj.write(inStr)
        inStr = ' RUNOFF_OPTION = ' + str(jobData.runOffOpt) + '\n'
        fileObj.write(inStr)
        inStr = ' SURFACE_DRAG_OPTION = ' + str(jobData.sfcDragOpt) + '\n'
        fileObj.write(inStr)
        inStr = ' FROZEN_SOIL_OPTION = ' + str(jobData.frzSoilOpt) + '\n'
        fileObj.write(inStr)
        inStr = ' SUPERCOOLED_WATER_OPTION = ' + str(jobData.supCoolOpt) + '\n'
        fileObj.write(inStr)
        inStr = ' RADIATIVE_TRANSFER_OPTION = ' + str(jobData.radTOpt) + '\n'
        fileObj.write(inStr)
        inStr = ' SNOW_ALBEDO_OPTION = ' + str(jobData.snAlbOpt) + '\n'
        fileObj.write(inStr)
        inStr = ' PCP_PARTITION_OPTION = ' + str(jobData.pcpPartOpt) + '\n'
        fileObj.write(inStr)
        inStr = ' TBOT_OPTION = ' + str(jobData.tbotOpt) + '\n'
        fileObj.write(inStr)
        inStr = ' TEMP_TIME_SCHEME_OPTION = ' + str(jobData.timeSchmOpt) + '\n'
        fileObj.write(inStr)
        inStr = ' GLACIER_OPTION = ' + str(jobData.glacier) + '\n'
        fileObj.write(inStr)
        inStr = ' SURFACE_RESISTANCE_OPTION = ' + str(jobData.sfcResOpt) + '\n'
        fileObj.write(inStr)
        #inStr = ' IMPERV_OPTION = ' + str(jobData.IMPERV_OPTION) + '\n'
        #fileObj.write(inStr)
        #fileObj.write('\n')
        fileObj.write(' ! Timestep in units of seconds\n')
        inStr = ' FORCING_TIMESTEP = ' + str(jobData.fDT) + '\n'
        fileObj.write(inStr)
        inStr = ' NOAH_TIMESTEP = ' + str(jobData.lsmDt) + '\n'
        fileObj.write(inStr)
        if minOutFlag == 1:
            # Produce minimal monthly outputs
            inStr = ' OUTPUT_TIMESTEP = 2592000\n'
        else:
            inStr = ' OUTPUT_TIMESTEP = ' + str(jobData.lsmOutDt) + '\n'
        fileObj.write(inStr)
        fileObj.write('\n')
        fileObj.write(' ! Land surface model restart file write frequency\n')
        if minOutFlag == 1:
            inStr = ' RESTART_FREQUENCY_HOURS = -9999\n'
        else:
            if int(jobData.lsmRstFreq) == -9999:
                inStr = ' RESTART_FREQUENCY_HOURS = -9999\n'
            else:
                inStr = ' RESTART_FREQUENCY_HOURS = ' + str(int(jobData.lsmRstFreq/3600.0)) + '\n'
        fileObj.write(inStr)
        fileObj.write('\n')
        fileObj.write(' ! Split output after split_output_count output times\n')
        inStr = ' SPLIT_OUTPUT_COUNT = ' + str(int(jobData.lsmSplitOutputCount)) + '\n'
        fileObj.write(inStr)
        fileObj.write('\n')
        fileObj.write(' ! Soil layer specification\n')
        fileObj.write(' NSOIL = 4\n')
        inStr = ' soil_thick_input(1) = ' + str(jobData.soilThick[0]) + '\n'
        fileObj.write(inStr)
        inStr = ' soil_thick_input(2) = ' + str(jobData.soilThick[1]) + '\n'
        fileObj.write(inStr)
        inStr = ' soil_thick_input(3) = ' + str(jobData.soilThick[2]) + '\n'
        fileObj.write(inStr)
        inStr = ' soil_thick_input(4) = ' + str(jobData.soilThick[3]) + '\n'
        fileObj.write(inStr)
        fileObj.write('\n')
        fileObj.write(' ! Forcing data measurement height for winds, temp, humidity\n')
        inStr = ' ZLVL = ' + str(jobData.zLvl) + '\n'
        fileObj.write(inStr)
        fileObj.write('\n')
        fileObj.write(' ! Restart file format options\n')
        fileObj.write(' rst_bi_in = 0\n')
        fileObj.write(' rst_bi_out = 0\n')
        fileObj.write('\n')
        fileObj.write('/\n')
        fileObj.write('\n')
        fileObj.write('&WRF_HYDRO_OFFLINE\n')
        inStr = ' !Specifications of forcing data: 1=HRLDAS-hr format, 2=HRLDAS-min format ' + \
                '3=WRF, 4=Idealized, 5=Ideal w/ Spec.Precip., 6=HRLDAS-hrl y format w/ Spec. Precip.\n'
        fileObj.write(inStr)
        inStr = ' FORC_TYP = ' + str(jobData.fType) + '\n'
        fileObj.write(inStr)
        fileObj.write('/\n')
        fileObj.write('\n')

        if(jobData.crocusFlag == 1):
            inStr = '&CROCUS_nlist'
            fileObj.write(inStr)
            fileObj.write('\n')
            inStr = ' crocus_opt = %s  ! 0 model is off, 1 model is on' %(str(jobData.crocusOpt))
            fileObj.write(inStr)
            fileObj.write('\n')
            inStr = ' act_lev = %s     ! 1-50, 20-40 normal options' %(str(jobData.actLev))
            fileObj.write(inStr)
            fileObj.write('\n')
            fileObj.write('/\n')
            fileObj.write('\n')
        fileObj.close
    except:
        if len(statusData.errMsg) == 0:
            statusData.errMsg = "ERROR: Failure to create: " + pathOut
        raise
    
def createHydroNL(statusData,gageData,jobData,outDir,typeFlag,bDate,eDate,genFlag):
    # General function for creation of a hydro.namelist file.
    # NOTE: typeFlag = 1 indicates cold start.
    #       typeFlag = 2 indicates restart.
    # NOTE: genFlag = 0 indicates a spinup - pull all parameter files from 
    #                   gageData
    #       genFlag = 1 indicartes a calibration - pull HYDRO_TBL_2D.nc, Fulldom.nc,
    #                   GWBUCKPARM.nc, and soil_properties.nc from the run directory.
    #       genFlag = 2 Indicates validation CTRL - pull HYDRO_TBL_2D.nc, Fulldom.nc,
    #                   GWBUCKPARM.nc, and soil_properties.nc from calibration output.
    #       genFlag = 3 Indicates validation BEST - pull HYDRO_TBL_2D.nc, Fulldom.nc,
    #                   GWBUCKPARM.nc, and soil_properties.nc from calibration output.
    #       genFlag = 4 Indicates sensitivy analysis - HYDRO_TBL_2D.nc, Fulldom.nc,
    #                   GWBUCKPARM.nc, and soil_properties.nc from run directory
    # Create path for the namelist file.
    pathOut = outDir + "/hydro.namelist"
    if os.path.isfile(pathOut):
        os.remove(pathOut)
        
    # If this is a calibration simulation, we need to check to see if we are 
    # past the date of minimal outputs. If the user specified to turn this optional
    # feature off, then by default, all simulations will produce full outputs
    # for the entire calibration iteration simulation.
    if jobData.optCalStripFlag == 1:
        minOutFlag = 1
        if bDate >= jobData.bCalibFullOutputs:
            minOutFlag = 0
        else:
            minOutFlag = 1
    else:
        minOutFlag = 0
        
    # Write each line of the hydro namelist file.
    try:
        fileObj = open(pathOut,'w')
        fileObj.write('&HYDRO_nlist\n')
        fileObj.write('!!!! ---------------------- SYSTEM COUPLING ---------------------- !!!!\n')
        fileObj.write('!Specify what is being coupled: 1=HRLDAS (offline Noah-LSM), 2=WRF, 3=NASA/LIS, 4=CLM\n')
        fileObj.write('\n')
        fileObj.write('sys_cpl = 3\n')
        fileObj.write('\n')
        fileObj.write('!!!! ---------------------- MODEL INPUT DATA FILES ---------------------- !!!!\n')
        fileObj.write('\n')
        fileObj.write('!Specify land surface model gridded input data file...(e.g.: "geo_em.d01.nc")\n')
        inStr = 'GEO_STATIC_FLNM = "' + str(gageData.geoFile) + '"' + '\n'
        fileObj.write(inStr)
        fileObj.write('\n')
        fileObj.write('!Specify the high-resolution routing terrain input data file...(e.g.: "Fulldom_hires.nc")\n')
        if genFlag == 0:
            inStr = 'GEO_FINEGRID_FLNM = "' + str(gageData.fullDom) + '"' + '\n'
        if genFlag == 1:
            pthTmp = str(jobData.outDir) + "/" + str(jobData.jobName) + "/" + \
                     str(gageData.gage) + "/RUN.CALIB/OUTPUT/Fulldom.nc"
            if not os.path.isfile(pthTmp):
                statusData.errMsg = "ERROR: Failure to find: " + pthTmp
                raise Exception()
            inStr = 'GEO_FINEGRID_FLNM = "' + pthTmp + '"\n'
        if genFlag == 2:
            pthTmp = str(jobData.outDir) + "/" + str(jobData.jobName) + "/" + \
                     str(gageData.gage) + "/RUN.VALID/OUTPUT/CTRL/Fulldom.nc"
            if not os.path.isfile(pthTmp):
                statusData.errMsg = "ERROR: Failure to find: " + pthTmp
                raise Exception()
            inStr = 'GEO_FINEGRID_FLNM = "' + pthTmp + '"\n'
        if genFlag == 3:
            pthTmp = str(jobData.outDir) + "/" + str(jobData.jobName) + "/" + \
                     str(gageData.gage) + "/RUN.VALID/OUTPUT/BEST/Fulldom.nc"
            if not os.path.isfile(pthTmp):
                statusData.errMsg = "ERROR: Failure to find: " + pthTmp
                raise Exception()
            inStr = 'GEO_FINEGRID_FLNM = "' + pthTmp + '"\n'
        if genFlag == 4:
            pthTmp = outDir + "/Fulldom.nc"
            if not os.path.isfile(pthTmp):
                statusData.errMsg = "ERROR: Failure to find: " + pthTmp
                raise Exception()
            inStr = 'GEO_FINEGRID_FLNM = "' + pthTmp + '"' + '\n'
        fileObj.write(inStr)
        fileObj.write('\n')
        fileObj.write('! Specify the spatial hydro parameters file (e.g.: "hydro2dtbl.nc")\n')
        fileObj.write('! If you specify a filename and the file does not exist, it will be created for you.\n')
        if genFlag == 0:
            # Spinup
            inStr = 'HYDROTBL_F = "' + str(gageData.hydroSpatial) + '"' + '\n'
        if genFlag == 1:
            # Calibration run with updated parameter dataset
            pthTmp = str(jobData.outDir) + "/" + str(jobData.jobName) + "/" + \
                     str(gageData.gage) + "/RUN.CALIB/OUTPUT/HYDRO_TBL_2D.nc"
            if not os.path.isfile(pthTmp):
                statusData.errMsg = "ERROR: Failure to find: " + pthTmp
                raise Exception()
            inStr = 'HYDROTBL_F = "' + pthTmp + '"\n'
        if genFlag == 2:
            # Control validation simulation
            pthTmp = str(jobData.outDir) + "/" + str(jobData.jobName) + "/" + \
                     str(gageData.gage) + "/RUN.VALID/OUTPUT/CTRL/HYDRO_TBL_2D.nc"
            if not os.path.isfile(pthTmp):
                statusData.errMsg = "ERROR: Failure to find: " + pthTmp
                raise Exception()
            inStr = 'HYDROTBL_F = "' + pthTmp + '"\n'
        if genFlag == 3:
            # Best validation simulation
            pthTmp = str(jobData.outDir) + "/" + str(jobData.jobName) + "/" + \
                     str(gageData.gage) + "/RUN.VALID/OUTPUT/BEST/HYDRO_TBL_2D.nc"
            if not os.path.isfile(pthTmp):
                statusData.errMsg = "ERROR: Failure to find: " + pthTmp
                raise Exception()
            inStr = 'HYDROTBL_F = "' + pthTmp + '"\n'
        if genFlag == 4:
            pthTmp = outDir + "/HYDRO_TBL_2D.nc"
            if not os.path.isfile(pthTmp):
                statusData.errMsg = "ERROR: Failure to find: " + pthTmp
                raise Exception()
            inStr = 'HYDROTBL_F = "' + pthTmp + '"' + '\n'
        fileObj.write(inStr)
        fileObj.write('\n')
        fileObj.write('! Specify spatial metadata file for land surface grid. (e.g. "GEOGRID_LDASOUT_Spatial_Metadata.nc")\n')
        if str(gageData.landSpatialMeta) == '-9999':
            inStr = 'LAND_SPATIAL_META_FLNM = \'\'' + '\n'
        else:
            inStr = 'LAND_SPATIAL_META_FLNM = "' + str(gageData.landSpatialMeta) + '"' + '\n'
        fileObj.write(inStr)
        fileObj.write('\n')
        fileObj.write('!Specify the name of the restart file if starting from restart... comment out with ! if not...\n')
        if typeFlag == 1:
            # We are cold-starting this simulation. This will most likely be for spinup
            # purposes.
            inStr = '!RESTART_FILE = ""' + '\n'
        if typeFlag == 2:
            # We are restarting a model simulation that has either failed, or was killed.
            restartFile = outDir + "/HYDRO_RST." + bDate.strftime('%Y-%m-%d') + "_00:00_DOMAIN1"
            if not os.path.isfile(restartFile):
                statusData.errMsg = "ERROR: Failure to find: " + restartFile
                raise Exception()
            inStr = 'RESTART_FILE = "' + restartFile + '"' + '\n'
        if typeFlag == 3:
            # This is the beginning of a new sensitivity/calibration/validation
            # simulation.
            if jobData.coldStart == 1:
                inStr = '!RESTART_FILE = ""' + '\n'
            if jobData.optSpinFlag == 1:
                inStr = 'RESTART_FILE = \"' + gageData.optHydroRstFile + '\"\n'
            if jobData.optSpinFlag == 0 and jobData.coldStart == 0:
                restartFile = outDir + "/HYDRO_RST." + bDate.strftime('%Y-%m-%d') + "_00:00_DOMAIN1"
                if not os.path.isfile(restartFile):
                    statusData.errMsg = "ERROR: Failure to find: " + restartFile
                    raise Exception()
                inStr = 'RESTART_FILE = "' + restartFile + '"' + '\n'
        fileObj.write(inStr)
        fileObj.write('\n')
        fileObj.write('!!!! ---------------------- MODEL SETUP OPTIONS ---------------------- !!!!\n')
        fileObj.write('\n')
        fileObj.write('!Specify the domain or nest number identifier...(integer)\n')
        fileObj.write('IGRID = 1\n')
        fileObj.write('\n')
        fileObj.write('!Specify the restart file write frequency...(minutes)\n')
        fileObj.write('! A value of -99999 will output restarts on the first day of the month only.\n')
        if minOutFlag == 1:
            inStr = 'rst_dt = -99999\n'
        else:
            if int(jobData.hydroRstFreq) == -99999:
                inStr = 'rst_dt = -99999\n'
            else:
                inStr = 'rst_dt = ' + str(int(jobData.hydroRstFreq/60.0)) + '\n'
        fileObj.write(inStr)
        fileObj.write('\n') 
        fileObj.write('! Reset the LSM soil states from the high-res routing restart file (1=overwrite, 0 = no overwrite)\n')
        fileObj.write('! NOTE: Only turn this option on if overland or subsurface routing is active!\n')
        inStr = 'rst_typ = ' + str(jobData.rstType)  + '\n'
        fileObj.write(inStr)
        fileObj.write('\n')
        fileObj.write('! Restart file format control\n')
        fileObj.write('rst_bi_in = 0  !0: use netcdf input restart file (default)\n')
        fileObj.write('               !1: use parallel io for reading multiple restart files, 1 per core\n')
        fileObj.write('rst_bi_out = 0 !0: use netcdf output restart file (default)\n')
        fileObj.write('               !1: use paralle io for outputting multiple restart files, 1 per core\n')
        fileObj.write('\n')
        fileObj.write('!Restart switch to set restart accumulation variables = 0 (0-no reset, 1-yes reset to 0.0)\n')
        inStr = 'RSTRT_SWC = ' + str(jobData.resetHydro) + '\n'
        fileObj.write(inStr)
        fileObj.write('\n')
        fileObj.write('! Specify baseflow/bucket model initialization...(0=cold start from table, 1=restart file)\n')
        if typeFlag == 1:
            # For cold-start spinups
            inStr = "GW_RESTART = 0\n"
        else:
            if jobData.gwBaseFlag == 0:
                # If the user has turned off the ground water buckets, 
                # turn this option off.
                inStr = "GW_RESTART = 0\n"
            else:
                # For all other runs that are not cold-start spinups. 
                inStr = "GW_RESTART = 1\n"
        fileObj.write(inStr)
        fileObj.write('\n')
        fileObj.write('!!!!------------ MODEL OUTPUT CONTROL ---------------!!!\n')
        fileObj.write('\n')
        fileObj.write('!Specify the output file write frequency...(minutes)\n')
        inStr = 'out_dt = ' + str(int(jobData.hydroOutDt/60.0)) + ' ! minutes' + '\n'
        fileObj.write(inStr)
        fileObj.write('\n')
        fileObj.write('!Specify the number of output times to be contained within each output history file...(integer)\n')
        fileObj.write('!  SET = 1 WHEN RUNNING CHANNEL ROUTING ONLY/CALIBRATION SIMS!!!!\n')
        fileObj.write('!  SET = 1 WHEN RUNNING COUPLED TO WRF!!!\n')
        fileObj.write('!  SET = 0 WHEN All outputs will be written into one file\n')
        inStr = 'SPLIT_OUTPUT_COUNT = ' + str(int(jobData.SplitOutputCount)) + '\n'
        fileObj.write(inStr)
        fileObj.write('\n')
        fileObj.write('!Specify the minimum stream order to output to netcdf point file...(integer)\n')
        fileObj.write('!Note: lower value of stream order produces more output\n')
        inStr = 'order_to_write = ' + str(jobData.strOrder) + '\n'
        fileObj.write(inStr)
        fileObj.write('\n')
        fileObj.write('! Flag to turn configure output routines: 1 = with scale/offset/compression\n')
        fileObj.write('! 2 = with scale/offset/NO compression, 3 = compression only, 4 = no scale/offset/compression (default)\n')
        inStr = 'io_form_outputs = ' + str(jobData.ioFormOutputs) + '\n'
        fileObj.write(inStr)
        fileObj.write('\n')
        fileObj.write('! Realtime run configuration option:\n')
        fileObj.write('! 0=all (default), 1=analysis, 2=short-range, 3=medium-range, 4=long-range, 5=retrospective\n')
        inStr = 'io_config_outputs = ' + str(jobData.ioConfigOutputs) + '\n'
        #TML: Write additional channel routing output for validation runs, permitting additional analysis:
        if genFlag >= 2:
            inStr = 'io_config_outputs = 0\n'
        fileObj.write(inStr)
        fileObj.write('\n')
        fileObj.write('! Option to write output files at time 0: 0=no, 1=yes (default)\n')
        fileObj.write('t0OutputFlag = 1\n')
        fileObj.write('\n')
        fileObj.write('! Options to output channel & bucket influxes. Only active for UDMP_OPT=1.\n')
        fileObj.write('! Nonzero choice requires that out_dt above matches NOAH_TIMESTEP in namelist.hrldas.\n')
        fileObj.write('! 0=None (default), 1=channel influxes (qSfcLatRunoff,qBucket)\n')
        fileObj.write('! 2=channel+bucket fluxes (qSfcLatRunoff,qBucket,qBtmVertRunoff_toBucket)\n')
        fileObj.write('! 3=channel accumulations (accSfcLatRunoff, accBucket) *** NOT TESTED ***\n')
        #TML: Write additional channel routing output for validation runs, permitting additional analysis:
        if genFlag >= 2:
            fileObj.write('output_channelBucket_influx = 0\n')
        else:
            fileObj.write('output_channelBucket_influx = 0\n')

        fileObj.write('!Output netcdf file control\n')
        if minOutFlag == 1:
            # Turn all outputs off
            inStr = 'CHRTOUT_DOMAIN = 0 ! Netcdf point timeseries output at all channel points (1d)\n'
            fileObj.write(inStr)
            fileObj.write('                   ! 0 = no output, 1 = output\n')
            inStr = 'CHANOBS_DOMAIN = 0 ! Netcdf point timeseries at forecast points or gage points (defined in Routelink)\n'
            fileObj.write(inStr)
            fileObj.write('              ! 0 = no output, 1 = output at forecast points or gage points\n')
            inStr = 'CHRTOUT_GRID = 0 ! Netcdf grid of channel streamflow values (2d)\n'
            fileObj.write(inStr)
            fileObj.write('              ! 0 = no output, 1 = output\n')
            fileObj.write('              ! NOTE: Not available with reach-based routing\n')
            inStr = 'LSMOUT_DOMAIN = 0 ! Netcdf grid of variables passed between LSM and routing components\n'
            fileObj.write(inStr)
            fileObj.write('              ! 0 = no output, 1 = output\n')
            fileObj.write('              ! NOTE: No scale_factor/add_offset available\n')
            inStr = 'RTOUT_DOMAIN = 0 ! Netcdf grid of terrain routing variables on routing grid\n'
            fileObj.write(inStr)
            fileObj.write('              ! 0 = no output, 1 = output\n')
            inStr = 'output_gw = 0 ! Netcdf point of GW buckets\n'
            fileObj.write('              ! 0 = no output, 1 = output\n')
            fileObj.write(inStr)
            inStr = 'outlake = 0 ! Netcdf point file of lakes (1d)\n'
            fileObj.write(inStr)
            fileObj.write('              ! 0 = no output, 1 = output\n')
            inStr = 'frxst_pts_out = 0 ! ASCII text file of forecast points or gage points (defined in Routelink)\n'
            fileObj.write(inStr)
        else:
            inStr = 'CHRTOUT_DOMAIN = ' + str(jobData.chrtoutDomain) + ' ! Netcdf point timeseries output at all channel points (1d)\n'
            fileObj.write(inStr)
            fileObj.write('                   ! 0 = no output, 1 = output\n')
            inStr = 'CHANOBS_DOMAIN = ' + str(jobData.chanObs) + ' ! Netcdf point timeseries at forecast points or gage points (defined in Routelink)\n'
            fileObj.write(inStr)
            fileObj.write('              ! 0 = no output, 1 = output at forecast points or gage points\n')
            inStr = 'CHRTOUT_GRID = ' + str(jobData.chrtoutGrid) + ' ! Netcdf grid of channel streamflow values (2d)' + '\n'
            fileObj.write(inStr)
            fileObj.write('              ! 0 = no output, 1 = output\n')
            fileObj.write('              ! NOTE: Not available with reach-based routing\n')
            inStr = 'LSMOUT_DOMAIN = ' + str(jobData.lsmDomain) + ' ! Netcdf grid of variables passed between LSM and routing components\n'
            fileObj.write(inStr)
            fileObj.write('              ! 0 = no output, 1 = output\n')
            fileObj.write('              ! NOTE: No scale_factor/add_offset available\n')
            inStr = 'RTOUT_DOMAIN = ' + str(jobData.rtoutDomain) + ' ! Netcdf grid of terrain routing variables on routing grid\n'
            fileObj.write(inStr)
            fileObj.write('              ! 0 = no output, 1 = output\n')
            inStr = 'output_gw = ' + str(jobData.gwOut) + ' ! Netcdf point of GW buckets\n'
            fileObj.write(inStr)
            fileObj.write('              ! 0 = no output, 1 = output\n')
            inStr = 'outlake = ' + str(jobData.lakeOut) + ' ! Netcdf point file of lakes (1d)\n'
            fileObj.write(inStr)
            fileObj.write('              ! 0 = no output, 1 = output\n')
            inStr = 'frxst_pts_out = ' + str(jobData.frxstPts) + ' ! ASCII text file of forecast points or gage points (defined in Routelink)\n'
            fileObj.write(inStr)
        fileObj.write('              ! 0 = no output, 1 = output\n')
        fileObj.write('\n')
        fileObj.write('!!!! ---------------------- PHYSICS OPTIONS AND RELATED SETTINGS ---------------------- !!!!\n')
        fileObj.write('\n')
        fileObj.write('!Specify the number of soil layers (integer) and the depth of the bottom of of each layer (meters)...\n')
        fileObj.write('! Notes: In Version 1 of WRF-Hydro these must be the same as in the namelist.input file\n')
        fileObj.write('! Future versions will permit this to be different.\n')
        fileObj.write(' NSOIL=4\n')
        inStr = 'ZSOIL8(1) = ' + str((0.00 - jobData.soilThick[0])) + '\n'
        fileObj.write(inStr)
        inStr = 'ZSOIL8(2) = ' + str((0.00 - jobData.soilThick[0] - jobData.soilThick[1])) + '\n'
        fileObj.write(inStr)
        inStr = 'ZSOIL8(3) = ' + str((0.00 - jobData.soilThick[0] - jobData.soilThick[1] - jobData.soilThick[2])) + '\n'
        fileObj.write(inStr)
        inStr = 'ZSOIL8(4) = ' + str((0.00 - jobData.soilThick[0] - jobData.soilThick[1] - jobData.soilThick[2] - jobData.soilThick[3])) + '\n'
        fileObj.write(inStr)
        fileObj.write('\n')
        fileObj.write('!Specify the grid spacing of the terrain routing grid...(meters)\n')
        inStr = 'DXRT = ' + str(float(gageData.dxHydro)) + '\n'
        fileObj.write(inStr)
        fileObj.write('\n')
        fileObj.write('!Specify the integer multiple between the land model grid and the terrain routing grid...(integer)\n')
        inStr = 'AGGFACTRT = ' + str(int(gageData.aggFact)) + '\n'
        fileObj.write(inStr)
        fileObj.write('\n')
        fileObj.write('! Specify the routing model timestep...(seconds)\n')
        inStr = 'DTRT_CH = ' + str(jobData.dtChRt) + '\n'
        fileObj.write(inStr)
        inStr = 'DTRT_TER = ' + str(jobData.dtTerRt) + '\n'
        fileObj.write(inStr)
        fileObj.write('\n')
        fileObj.write('!Switch activate sucsurface routing...(0=no, 1=yes)\n')
        inStr = 'SUBRTSWCRT = ' + str(jobData.subRtFlag) + '\n'
        fileObj.write(inStr)
        fileObj.write('\n')
        fileObj.write('!Switch activate surface overland flow routing...(0=no, 1=yes)\n')
        inStr = 'OVRTSWCRT = ' + str(jobData.ovrRtFlag) + '\n'
        fileObj.write(inStr)
        fileObj.write('!Specify overland flow routing option: 1=Steepest Descent(D8) 2=CASC2D\n')
        fileObj.write(' ! NOTE: Currently subsurface flow is only steepest descent\n')
        inStr = 'rt_option = ' + str(jobData.rtOpt) + '\n'
        fileObj.write(inStr)
        fileObj.write('\n')
        #fileObj.write(' ! Specify whether to adjust overland flow parameters based on imperviousness\n')
        #inStr = ' imperv_adj = ' + str(jobData.imperv_adj) + '\n'
        #fileObj.write(inStr)
        #fileObj.write('\n')
        fileObj.write('!Switch to activate channel routing:\n')
        inStr = 'CHANRTSWCRT = ' + str(jobData.chnRtFlag) + '\n'
        fileObj.write(inStr)
        fileObj.write('!Specify channel routing option: 1=Muskingam-reach, 2=Musk.-Cunge-reach, 3=Diff.Wave-gridded\n')
        inStr = 'channel_option = ' + str(jobData.chnRtOpt) + '\n'
        fileObj.write(inStr)
        fileObj.write('\n')
        fileObj.write('!Specify the reach file for reach-based routing options...\n')
        if str(gageData.rtLnk) == '-9999':
            inStr = 'route_link_f = \'\'' + '\n'
        else:
            if genFlag == 0:
                inStr = 'route_link_f = "' + str(gageData.rtLnk) + '"\n'
            if genFlag == 1:
                pthTmp = str(jobData.outDir) + "/" + str(jobData.jobName) + "/" + \
                         str(gageData.gage) + "/RUN.CALIB/OUTPUT/RouteLink.nc"
                if not os.path.isfile(pthTmp):
                    statusData.errMsg = "ERROR: Failure to find: " + pthTmp
                    raise Exception()
                inStr = 'route_link_f = "' + pthTmp + '"\n'
            if genFlag == 2:
                pthTmp = str(jobData.outDir) + "/" + str(jobData.jobName) + "/" + \
                         str(gageData.gage) + "/RUN.VALID/OUTPUT/CTRL/RouteLink.nc"
                if not os.path.isfile(pthTmp):
                    statusData.errMsg = "ERROR: Failure to find: " + pthTmp
                    raise Exception()
                inStr = 'route_link_f = "' + pthTmp + '"\n'
            if genFlag == 3:
                pthTmp = str(jobData.outDir) + "/" + str(jobData.jobName) + "/" + \
                         str(gageData.gage) + "/RUN.VALID/OUTPUT/BEST/RouteLink.nc"
                if not os.path.isfile(pthTmp):
                    statusData.errMsg = "ERROR: Failure to find: " + pthTmp
                    raise Exception()
                inStr = 'route_link_f = "' + pthTmp + '"\n'
            if genFlag == 4:
                pthTmp = outDir + "/RouteLink.nc"
                if not os.path.isfile(pthTmp):
                    statusData.errMsg = "ERROR: Failure to find: " + pthTmp
                    raise Exception()
                inStr = 'route_link_f = "' + pthTmp + '"' + '\n'
        fileObj.write(inStr)
        fileObj.write('\n')
        fileObj.write('! If using channel_option=2, activate the compound channel formulation? (Default=.FALSE.)\n')
        if jobData.enableCmpdChan == 1:
            if jobData.cmpdChan == 1:
                fileObj.write('compound_channel = .TRUE.\n')
            else:
                fileObj.write('!compound_channel = .FALSE.\n')
        fileObj.write('\n')
        fileObj.write('! Switch to activate channel-loss option (0=no, 1=yes) [Requires Kchan in RouteLink]\n')
        fileObj.write('channel_loss_option = 1\n')
        fileObj.write('\n')
        fileObj.write('! Specify the simulated lakes for NHDPlus reach-based routing\n')
        if str(gageData.lkFile) == '-9999':
            inStr = '!route_lake_f = \'\'' + '\n'
        else:
            inStr = 'route_lake_f = "' + str(gageData.lkFile) + '"\n'
        fileObj.write(inStr)
        fileObj.write('\n')
        fileObj.write('!Switch to activate baseflow bucket model...(0=none, 1=exp. bucket, 2=pass-through\n')
        inStr = 'GWBASESWCRT = ' + str(jobData.gwBaseFlag) + '\n'
        fileObj.write(inStr)
        fileObj.write('\n')
        if jobData.enableGwLoss == 1:
            fileObj.write('! Switch to activate bucket model loss (0=no, 1=yes)\n')
            inStr = 'bucket_loss = ' + str(jobData.gwLoss) + '\n'
            fileObj.write(inStr)
            fileObj.write('\n')
        fileObj.write('!Groundwater/baseflow mask specified on land surface model grid...\n')
        fileObj.write('!Note: Only required in baseflow bucket model is active\n')
        fileObj.write('!gwbasmskfil will not be used if UDMP_OPT = 1\n')
        if str(gageData.gwMask) == '-9999':
            inStr = '!gwbasmskfil = \'\'' + '\n'
        else:
            inStr = 'gwbasmskfil = "' + str(gageData.gwMask) + '"\n'
        fileObj.write(inStr)
        fileObj.write('\n')
        fileObj.write('! Groundwater bucket parameter file (e.g.: "GWBUCKPARM.nc")\n')
        if jobData.gwBaseFlag == 1  or jobData.gwBaseFlag == 4:
            if genFlag == 0:
                inStr = 'GWBUCKPARM_file = "' + str(gageData.gwFile) + '"\n'
            if genFlag == 1:
                pthTmp = str(jobData.outDir) + "/" + str(jobData.jobName) + "/" + \
                         str(gageData.gage) + "/RUN.CALIB/OUTPUT/GWBUCKPARM.nc"
                if not os.path.isfile(pthTmp):
                    statusData.errMsg = "ERROR: Failure to find: " + pthTmp
                    raise Exception()
                inStr = 'GWBUCKPARM_file = "' + pthTmp + '"\n'
            if genFlag == 2:
                pthTmp = str(jobData.outDir) + "/" + str(jobData.jobName) + "/" + \
                         str(gageData.gage) + "/RUN.VALID/OUTPUT/CTRL/GWBUCKPARM.nc"
                if not os.path.isfile(pthTmp):
                    statusData.errMsg = "ERROR: Failure to find: " + pthTmp
                    raise Exception()
                inStr = 'GWBUCKPARM_file = "' + pthTmp + '"\n'
            if genFlag == 3:
                pthTmp = str(jobData.outDir) + "/" + str(jobData.jobName) + "/" + \
                         str(gageData.gage) + "/RUN.VALID/OUTPUT/BEST/GWBUCKPARM.nc"
                if not os.path.isfile(pthTmp):
                    statusData.errMsg = "ERROR: Failure to find: " + pthTmp
                    raise Exception()
                inStr = 'GWBUCKPARM_file = "' + pthTmp + '"\n'
            if genFlag == 4:
                pthTmp = outDir + "/GWBUCKPARM.nc"
                if not os.path.isfile(pthTmp):
                    statusData.errMsg = "ERROR: Failure to find: " + pthTmp
                    raise Exception()
                inStr = 'GWBUCKPARM_file = "' + pthTmp + '"' + '\n'
        else:
            # We aren't running with the ground water bucket model.
            inStr = 'GWBUCKPARM_file = "-9999"\n'
        fileObj.write(inStr)
        fileObj.write('\n')
        fileObj.write('! User defined mapping, such NHDPlus\n')
        fileObj.write('!0: default none. 1: yes\n')
        inStr = 'UDMP_OPT = ' + str(jobData.udmpOpt) + '\n'
        fileObj.write(inStr)
        fileObj.write('! If on, specify the user-defined mapping file (e.g.: "spatialWeights.nc")\n')
        if jobData.udmpOpt == 1:
            inStr = 'udmap_file = "' + str(gageData.udMap) + '"\n'
        else:
            inStr = '!udmap_file = "./DOMAIN/spatialweights.nc"\n'
        fileObj.write(inStr)
        fileObj.write('\n')
        fileObj.write('/')
        fileObj.write('\n')
        fileObj.write('&NUDGING_nlist\n')
        fileObj.write('\n')
        fileObj.write(' ! Path to the "timeslice" observation files.\n')
        fileObj.write('timeSlicePath = "./nudgingTimeSliceObs/"\n')
        fileObj.write('\n')
        fileObj.write('!nudgingParamFile  = "foo"\n')
        fileObj.write('\n')
        fileObj.write(' ! Nudging restart file = "nudgingLastObsFile"\n')
        fileObj.write(' ! nudgingLastObsFile defaults to "", which will look for nudgingLastObs.YYYY-mm-dd_HH:MM:SS.nc\n')
        fileObj.write(' !  **AT THE INITIALIZATION TIME OF THE RUN**. Set to a missing file to use no restart.\n')
        fileObj.write(' !nudgingLastObsFile = "foo"\n')
        fileObj.write('\n')
        fileObj.write('!! Parallel input of nudging timeslice observation files?\n')
        fileObj.write('readTimesliceParallel = .TRUE.\n')
        fileObj.write('\n')
        fileObj.write('! TemporalPersistence defaults to true, only runs if necessary params present.\n')
        fileObj.write('temporalPersistence = .FALSE.\n')
        fileObj.write('\n')
        fileObj.write(' ! The total number of last (obs,modeled) pairs to save in nudgingLastObs for\n')
        fileObj.write(' ! removal of bias. This is the maximum array length. (This option is active when persistBias=FALSE)\n')
        fileObj.write(' ! (Default=960=10days @15 min obs resolution, if all the obs are present and no longer if not.)\n')
        fileObj.write('nLastObs = 960\n')
        fileObj.write('\n')
        fileObj.write(' ! If using temporalPersistence the last observation persists by default.\n')
        fileObj.write(' ! This option instead persists the bias after the last observation.\n')
        fileObj.write('persistBias = .FALSE.\n')
        fileObj.write('\n')
        fileObj.write(' ! AnA (FALSE) vs Forecast (TRUE) bias persistence.\n')
        fileObj.write(' ! If persistBias: Does the window for calculating the bias end at\n')
        fileObj.write(' ! model init time (=t0)?\n')
        fileObj.write(' ! FALSE = window ends at model time (moving),\n')
        fileObj.write(' ! TRUE = window ends at init=t0(fcst) time.\n')
        fileObj.write(' ! (If commented out, Default=FALSE) time.\n')
        fileObj.write(' ! Note: Perfect restart tests require this option to be .FALSE.\n')
        fileObj.write('biasWindowBeforeT0 = .FALSE.\n')
        fileObj.write('\n')
        fileObj.write(' ! If persistBias: Only use this many last (obs,modeled) pairs. (If Commented out, Default=-1*nLastObs)\n')
        fileObj.write(' ! > 0: apply an age-based filter, units=hours.\n')
        fileObj.write(' ! = 0: apply no additional filter, use all available/usable obs.\n')
        fileObj.write(' ! < 0: apply an count-based filter, units=count\n')
        fileObj.write('maxAgePairsBiasPersist = -960\n')
        fileObj.write('\n')
        fileObj.write(' ! If persistBias: The minimum number of last (obs,modeled) pairs, with age less than\n')
        fileObj.write(' ! maxAgePairsBiasPersist, required to apply a bias correction. (default=8)\n')
        fileObj.write('minNumPairsBiasPersist = 8\n')
        fileObj.write('\n')
        fileObj.write(' ! If persistBias: give more weight to observations closer in time? (default=FALSE)\n')
        fileObj.write('invDistTimeWeightBias = .TRUE.\n')
        fileObj.write('\n')
        fileObj.write(' ! If persistBias: "No constructive interference in bias correction?", Reduce the bias adjustment\n')
        fileObj.write(' ! when the model and the bias adjustment have the same sign relative to the modeled flow at t0?\n')
        fileObj.write(' (default=FALSE)\n')
        fileObj.write(' ! Note: Perfect restart tests require this option to be .FALSE.\n')
        fileObj.write('noConstInterfBias = .FALSE.\n')
        fileObj.write('/')
        fileObj.close
    except:
        if len(statusData.errMsg) == 0:
            statusData.errMsg = "ERROR: Failure to create " + pathOut
        raise

def createLisNL(statusData,gageData,jobData,outDir,typeFlag,bDate,eDate,genFlag):

    file_path = statusData.lisConfig
    nlc_file_path = statusData.nlcConfig
    out_path = outDir + '/lis.config'
    if os.path.isfile(out_path):
        os.remove(out_path)
    # Read the content of the file
    with open(file_path, 'r') as file:
        lis_config_content = file.read()

    if bDate == jobData.bCalibDate:
        typeFlag == 4

    # Define the new values for the variables you want to change
    if typeFlag == 1:
        mode = 'coldstart'
        lCurrent = bDate
        hour = bDate.strftime('%-H')
        lisRestartPath = jobData.noah_mp_4_0_1_restart_file
    elif typeFlag == 2:
        mode = 'restart'
        hour = '23'
        lCurrent = bDate - datetime.timedelta(days=1)
        lisRestartPath = "LIS_OUTPUT/SURFACEMODEL/" + lCurrent.strftime('%Y%m') + "/LIS_RST_NOAHMP401_" + lCurrent.strftime('%Y%m%d') + "2300.d01.nc"
    elif typeFlag == 4 or typeFlag == 3:
        mode = 'restart'
        hour = '23'
        lCurrent = jobData.bCalibDate - datetime.timedelta(days=1)
        lisRestartPath = "./LIS_RST_NOAHMP401_" + lCurrent.strftime('%Y%m%d') + "2300.d01.nc"
 
    
    # ... add more new values as needed

    # Modify the variables in the content
    lis_config_content = lis_config_content.replace('Starting year: ', f"Starting year: {lCurrent.strftime('%Y')}")
    lis_config_content = lis_config_content.replace('Starting month:', f"Starting month: {lCurrent.strftime('%m')}")
    lis_config_content = lis_config_content.replace('Starting day:', f"Starting day: {lCurrent.strftime('%d')}")
    lis_config_content = lis_config_content.replace('Starting hour:', f"Starting hour: {hour}")
    lis_config_content = lis_config_content.replace('Starting minute:', f"Starting minute: {lCurrent.strftime('%-M')}")
    lis_config_content = lis_config_content.replace('Starting second:', f"Starting second: {lCurrent.strftime('%-S')}")
    lis_config_content = lis_config_content.replace('Ending year: ', f"Ending year: {eDate.strftime('%Y')}")
    lis_config_content = lis_config_content.replace('Ending month:', f"Ending month: {eDate.strftime('%m')}")
    lis_config_content = lis_config_content.replace('Ending day:', f"Ending day: {eDate.strftime('%d')}")
    lis_config_content = lis_config_content.replace('Ending hour:', f"Ending hour: {eDate.strftime('%-H')}")
    lis_config_content = lis_config_content.replace('Ending minute:', f"Ending minute: {eDate.strftime('%-M')}")
    lis_config_content = lis_config_content.replace('Ending second:', f"Ending second: {eDate.strftime('%-S')}")
    lis_config_content = lis_config_content.replace('Start mode:', f"Start mode: {mode}")
    lis_config_content = lis_config_content.replace('Surface model output interval:', f'Surface model output interval: "{jobData.surface_model_output_interval}"')
    lis_config_content = lis_config_content.replace('Land surface model:', f'Land surface model: "{jobData.land_surface_model}"')
    lis_config_content = lis_config_content.replace('Number of met forcing sources: ', f"Number of met forcing sources: {jobData.number_of_met_forcing_sources}")
    lis_config_content = lis_config_content.replace('Blending method for forcings:', f'Blending method for forcings: "{jobData.blending_method_for_forcings}"')
    lis_config_content = lis_config_content.replace('Met forcing sources:', f'Met forcing sources: "{jobData.met_forcing_sources}"')
    lis_config_content = lis_config_content.replace('Topographic correction method (met forcing):', f'Topographic correction method (met forcing): "{jobData.topographic_correction_method_met_forcing}"')
    lis_config_content = lis_config_content.replace('Forcing variables list file:', f'Forcing variables list file: "{jobData.forcing_variables_list_file}"')
    lis_config_content = lis_config_content.replace('Output forcing:', f"Output forcing: {jobData.output_forcing}")
    lis_config_content = lis_config_content.replace('Output parameters:', f"Output parameters: {jobData.output_parameters}")
    lis_config_content = lis_config_content.replace('Output model restart files:', f"Output model restart files: {jobData.output_model_restart_files}")
    lis_config_content = lis_config_content.replace('Output methodology:', f'Output methodology: "{jobData.output_methodology}"')
    lis_config_content = lis_config_content.replace('Output data format:', f'Output data format: "{jobData.output_data_format}"')
    lis_config_content = lis_config_content.replace('Output naming style:', f'Output naming style: "{jobData.output_naming_style}"')
    lis_config_content = lis_config_content.replace('Undefined value:', f"Undefined value: {jobData.undefined_value}")
    lis_config_content = lis_config_content.replace('Output directory:', f'Output directory: "LIS_OUTPUT"')
    lis_config_content = lis_config_content.replace('Diagnostic output file:', f'Diagnostic output file: "{jobData.diagnostic_output_file}"')
    lis_config_content = lis_config_content.replace('Number of ensembles per tile:', f"Number of ensembles per tile: {jobData.number_of_ensembles_per_tile}")
    lis_config_content = lis_config_content.replace('Number of processors along x:', f"Number of processors along x: {jobData.number_of_processors_along_x}")
    lis_config_content = lis_config_content.replace('Number of processors along y:', f"Number of processors along y: {jobData.number_of_processors_along_y}")
    lis_config_content = lis_config_content.replace('Halo size along x:', f"Halo size along x: {jobData.halo_size_along_x}")
    lis_config_content = lis_config_content.replace('Halo size along y:', f"Halo size along y: {jobData.halo_size_along_y}")
    lis_config_content = lis_config_content.replace('LIS domain and parameter data file:',f'LIS domain and parameter data file: "./lis.nc"')
    lis_config_content = lis_config_content.replace('Noah-MP.4.0.1 model timestep:', f'Noah-MP.4.0.1 model timestep: "{jobData.noah_mp_4_0_1_model_timestep}"')
    lis_config_content = lis_config_content.replace('Noah-MP.4.0.1 restart output interval:', f'Noah-MP.4.0.1 restart output interval: "{jobData.noah_mp_4_0_1_restart_output_interval}"')
    lis_config_content = lis_config_content.replace('Noah-MP.4.0.1 restart file:', f'Noah-MP.4.0.1 restart file: "{lisRestartPath}"')
    lis_config_content = lis_config_content.replace('Noah-MP.4.0.1 restart file format:', f"Noah-MP.4.0.1 restart file format: {jobData.noah_mp_4_0_1_restart_file_format}")
    lis_config_content = lis_config_content.replace('Noah-MP.4.0.1 soil parameter table:', f'Noah-MP.4.0.1 soil parameter table: "{jobData.noah_mp_4_0_1_soil_parameter_table}"')
    lis_config_content = lis_config_content.replace('Noah-MP.4.0.1 general parameter table:', f'Noah-MP.4.0.1 general parameter table: "{jobData.noah_mp_4_0_1_general_parameter_table}"')
    lis_config_content = lis_config_content.replace('Noah-MP.4.0.1 MP parameter table:', f'Noah-MP.4.0.1 MP parameter table: "{jobData.noah_mp_4_0_1_mp_parameter_table}"')
    lis_config_content = lis_config_content.replace('Noah-MP.4.0.1 number of soil layers:', f"Noah-MP.4.0.1 number of soil layers: {jobData.noah_mp_4_0_1_number_of_soil_layers}")
    lis_config_content = lis_config_content.replace('Noah-MP.4.0.1 thickness of soil layers:', f"Noah-MP.4.0.1 thickness of soil layers: {jobData.noah_mp_4_0_1_thickness_of_soil_layers}")
    lis_config_content = lis_config_content.replace('Noah-MP.4.0.1 dynamic vegetation option:', f"Noah-MP.4.0.1 dynamic vegetation option: {jobData.noah_mp_4_0_1_dynamic_vegetation_option}")
    lis_config_content = lis_config_content.replace('Noah-MP.4.0.1 canopy stomatal resistance option:', f"Noah-MP.4.0.1 canopy stomatal resistance option: {jobData.noah_mp_4_0_1_canopy_stomatal_resistance_option}")
    lis_config_content = lis_config_content.replace('Noah-MP.4.0.1 soil moisture factor for stomatal resistance:', f"Noah-MP.4.0.1 soil moisture factor for stomatal resistance: {jobData.noah_mp_4_0_1_soil_moisture_factor_for_stomatal_resistance}")
    lis_config_content = lis_config_content.replace('Noah-MP.4.0.1 runoff and groundwater option:', f"Noah-MP.4.0.1 runoff and groundwater option: {jobData.noah_mp_4_0_1_runoff_and_groundwater_option}")
    lis_config_content = lis_config_content.replace('Noah-MP.4.0.1 surface layer drag coefficient option:', f"Noah-MP.4.0.1 surface layer drag coefficient option: {jobData.noah_mp_4_0_1_surface_layer_drag_coefficient_option}")
    lis_config_content = lis_config_content.replace('Noah-MP.4.0.1 supercooled liquid water option:', f"Noah-MP.4.0.1 supercooled liquid water option: {jobData.noah_mp_4_0_1_supercooled_liquid_water_option}")
    lis_config_content = lis_config_content.replace('Noah-MP.4.0.1 frozen soil permeability option:', f"Noah-MP.4.0.1 frozen soil permeability option: {jobData.noah_mp_4_0_1_frozen_soil_permeability_option}")
    lis_config_content = lis_config_content.replace('Noah-MP.4.0.1 radiation transfer option:', f"Noah-MP.4.0.1 radiation transfer option: {jobData.noah_mp_4_0_1_radiation_transfer_option}")
    lis_config_content = lis_config_content.replace('Noah-MP.4.0.1 snow surface albedo option:', f"Noah-MP.4.0.1 snow surface albedo option: {jobData.noah_mp_4_0_1_snow_surface_albedo_option}")
    lis_config_content = lis_config_content.replace('Noah-MP.4.0.1 rainfall & snowfall option:', f"Noah-MP.4.0.1 rainfall & snowfall option: {jobData.noah_mp_4_0_1_rainfall_and_snowfall_option}")
    lis_config_content = lis_config_content.replace('Noah-MP.4.0.1 lower boundary of soil temperature option:', f"Noah-MP.4.0.1 lower boundary of soil temperature option: {jobData.noah_mp_4_0_1_lower_boundary_of_soil_temperature_option}")
    lis_config_content = lis_config_content.replace('Noah-MP.4.0.1 snow&soil temperature time scheme option:', f"Noah-MP.4.0.1 snow&soil temperature time scheme option: {jobData.noah_mp_4_0_1_snow_and_soil_temperature_time_scheme_option}")
    lis_config_content = lis_config_content.replace('Noah-MP.4.0.1 glacier option:', f"Noah-MP.4.0.1 glacier option: {jobData.noah_mp_4_0_1_glacier_option}")
    lis_config_content = lis_config_content.replace('Noah-MP.4.0.1 surface resistance option:', f"Noah-MP.4.0.1 surface resistance option: {jobData.noah_mp_4_0_1_surface_resistance_option}")
    lis_config_content = lis_config_content.replace('Noah-MP.4.0.1 soil configuration option:', f"Noah-MP.4.0.1 soil configuration option: {jobData.noah_mp_4_0_1_soil_configuration_option}")
    lis_config_content = lis_config_content.replace('Noah-MP.4.0.1 soil pedotransfer function option:', f"Noah-MP.4.0.1 soil pedotransfer function option: {jobData.noah_mp_4_0_1_soil_pedotransfer_function_option}")
    lis_config_content = lis_config_content.replace('Noah-MP.4.0.1 crop model option:', f"Noah-MP.4.0.1 crop model option: {jobData.noah_mp_4_0_1_crop_model_option}")
    lis_config_content = lis_config_content.replace('Noah-MP.4.0.1 urban physics option:', f"Noah-MP.4.0.1 urban physics option: {jobData.noah_mp_4_0_1_urban_physics_option}")
    lis_config_content = lis_config_content.replace('Noah-MP.4.0.1 initial surface skin temperature:', f"Noah-MP.4.0.1 initial surface skin temperature: {jobData.noah_mp_4_0_1_initial_surface_skin_temperature}")
    modified_temp_str = jobData.noah_mp_4_0_1_initial_soil_temperatures.replace('"','')
    lis_config_content = lis_config_content.replace('Noah-MP.4.0.1 initial soil temperatures:', f"Noah-MP.4.0.1 initial soil temperatures: {modified_temp_str}")
 
    modified_total_str = jobData.noah_mp_4_0_1_initial_total_soil_moistures.replace('"','')
    lis_config_content = lis_config_content.replace('Noah-MP.4.0.1 initial total soil moistures:', f"Noah-MP.4.0.1 initial total soil moistures: {modified_total_str}")
    lis_config_content = lis_config_content.replace('Noah-MP.4.0.1 initial snow depth:', f"Noah-MP.4.0.1 initial snow depth: {jobData.noah_mp_4_0_1_initial_snow_depth}")
    lis_config_content = lis_config_content.replace('Noah-MP.4.0.1 initial snow water equivalent:', f"Noah-MP.4.0.1 initial snow water equivalent: {jobData.noah_mp_4_0_1_initial_snow_water_equivalent}")
    lis_config_content = lis_config_content.replace('Noah-MP.4.0.1 initial total canopy surface water:', f"Noah-MP.4.0.1 initial total canopy surface water: {jobData.noah_mp_4_0_1_initial_total_canopy_surface_water}")
    lis_config_content = lis_config_content.replace('Noah-MP.4.0.1 initial water table depth:', f"Noah-MP.4.0.1 initial water table depth: {jobData.noah_mp_4_0_1_initial_water_table_depth}")
    lis_config_content = lis_config_content.replace('Noah-MP.4.0.1 initial water in the aquifer:', f"Noah-MP.4.0.1 initial water in the aquifer: {jobData.noah_mp_4_0_1_initial_water_in_the_aquifer}")
    lis_config_content = lis_config_content.replace('Noah-MP.4.0.1 initial water in aquifer and saturated soil:', f"Noah-MP.4.0.1 initial water in aquifer and saturated soil: {jobData.noah_mp_4_0_1_initial_water_in_aquifer_and_saturated_soil}")
    lis_config_content = lis_config_content.replace('Noah-MP.4.0.1 initial leaf area index:', f"Noah-MP.4.0.1 initial leaf area index: {jobData.noah_mp_4_0_1_initial_leaf_area_index}")
    lis_config_content = lis_config_content.replace('Noah-MP.4.0.1 reference height of temperature and humidity:', f"Noah-MP.4.0.1 reference height of temperature and humidity: {jobData.noah_mp_4_0_1_reference_height_of_temperature_and_humidity}")
    lis_config_content = lis_config_content.replace('Template open water timestep:', f"Template open water timestep: {jobData.template_open_water_timestep:}")
    # ... add more modifications for other variables

    # Save the modified content back to the file
    with open(out_path, 'w') as file:
        file.write(lis_config_content)

    out_path = outDir + '/nlc.runconfig'
    if os.path.isfile(out_path):
        os.remove(out_path)
    # Read the content of the file
    with open(nlc_file_path, 'r') as file:
        lis_config_content = file.read()

    # Define the new values for the variables you want to change
    if typeFlag == 1:
        dataInit = "INIT_DEFAULTS"
        importDependency = "false"
        read_restart = "false"
    elif typeFlag == 2 or typeFlag == 4 or typeFlag == 3:
        dataInit = "INIT_MODELS"
        importDependency = "true"
        read_restart = "true"

    nCoresInd = str(int(jobData.nCoresMod) - 1)

    lis_config_content = lis_config_content.replace('start_time:', f"start_time: {bDate.strftime('%Y %m %d %k %-M %-S')}")
    lis_config_content = lis_config_content.replace('stop_time:', f"stop_time: {eDate.strftime('%Y %m %d %k %-M %-S')}")
    lis_config_content = lis_config_content.replace('pets_lnd:', f"pets_lnd: 0 {nCoresInd}")
    lis_config_content = lis_config_content.replace('pets_hyd:', f"pets_hyd: 0 {nCoresInd}")
    lis_config_content = lis_config_content.replace('pets_med:', f"pets_med: 0 {nCoresInd}")
    lis_config_content = lis_config_content.replace('DataInitialization =', f"DataInitialization = {dataInit}")
    lis_config_content = lis_config_content.replace('import_dependency = lnd', f"import_dependency = {importDependency}")
    lis_config_content = lis_config_content.replace('read_restart =', f"read_restart = {read_restart}")

    # Save the modified content back to the file
    with open(out_path, 'w') as file:
        file.write(lis_config_content)

