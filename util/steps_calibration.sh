#!/bin/sh -f

fold_running=edit_this_to_your_run_dir/gpfsm/dnb06/projects/p225/amazrooe/calibration/test_calib_large # Note: update the running dir
source /discover/nobackup/projects/lis-ndmc/isrivast/python_envs/py_discover-mil/bin/activate
export QSCACHE_BYPASS=true

path_PyWrfHydroCalib=$fold_running/PyWrfHydroCalib # create a symlink to repo
path_nlc=/discover/nobackup/projects/lis-ndmc/tlahmers/excutables/LISHYDRO_08_2024_NDMC_NLDAS2Fix_SLES15/NASA-Land-Coupler/src/driver/NLC.exe
path_wrfhydro=/discover/nobackup/projects/lis-ndmc/tlahmers/excutables/LISHYDRO_08_2024_NDMC_NLDAS2Fix_SLES15/NASA-Land-Coupler/build/Run/
path_lis_inputs=/discover/nobackup/projects/lis-ndmc/tlahmers/CALIB/LIS_INPUTS/

file_db=$fold_running/DATABASE.db

## Configure $fold_running/setup_files/setup.parm
cp -r $path_PyWrfHydroCalib/setup_files $fold_running/
sed -i "/^outDir/c\outDir = ${fold_running}/calibOut" $fold_running/setup_files/setup.parm
mkdir -p ${fold_running}/calibOut

sed -i "/^moduleLoadStr/c\moduleLoadStr = []" $fold_running/setup_files/setup.parm

sed -i "/^nCoresModel/c\nCoresModel = 15" $fold_running/setup_files/setup.parm # NOTE: adjust the x/y processors below so the product is equal to nCoresModel
sed -i "/^number_of_processors_along_x/c\number_of_processors_along_x=5" $fold_running/setup_files/setup.parm
sed -i "/^number_of_processors_along_y/c\number_of_processors_along_y=3" $fold_running/setup_files/setup.parm

sed -i "/^calibParmTbl/c\calibParmTbl = ${fold_running}/setup_files/calib_params.tbl" $fold_running/setup_files/setup.parm
sed -i "/^numIter/c\numIter = 500" $fold_running/setup_files/setup.parm
sed -i "/^email/c\email = dummy@dummy.edu" $fold_running/setup_files/setup.parm # NOTE: update your email address

sed -i "/^wrfExe/c\wrfExe = ${path_nlc}" $fold_running/setup_files/setup.parm
sed -i "/^genParmTbl/c\genParmTbl = ${path_wrfhydro}/GENPARM.TBL" $fold_running/setup_files/setup.parm
sed -i "/^urbParmTbl/c\urbParmTbl = ${path_wrfhydro}/URBPARM.TBL" $fold_running/setup_files/setup.parm
sed -i "/^vegParmTbl/c\vegParmTbl = ${path_wrfhydro}/VEGPARM.TBL" $fold_running/setup_files/setup.parm
sed -i "/^soilParmTbl/c\soilParmTbl = ${path_wrfhydro}/SOILPARM.TBL" $fold_running/setup_files/setup.parm
sed -i "/^mpParmTbl/c\mpParmTbl = /discover/nobackup/projects/lis-ndmc/tlahmers/WR_DROUGHT/LISWrfHydro_DOMAIN/NOAHMP401_PARMS/MPTABLE.TBL" $fold_running/setup_files/setup.parm
sed -i "/^forcingVarTbl/c\forcingVarTbl = ${path_lis_inputs}/forcing_variables.txt" $fold_running/setup_files/setup.parm
sed -i "/^noahMPLSMTbl/c\noahMPLSMTbl = ${path_lis_inputs}/NOAHMP_OUTPUT_LIST.LSM.TBL" $fold_running/setup_files/setup.parm

sed -i "/^SplitOutputCount/c\SplitOutputCount = 0" $fold_running/setup_files/setup.parm # 1 means that it will output 1 file per output time step ; 0 means that it will append all the timesteps to one file
sed -i "/^lis_config_file/c\lis_config_file = ${fold_running}/setup_files/lis.config" $fold_running/setup_files/setup.parm
sed -i "/^nlc_config_file/c\nlc_config_file = ${fold_running}/setup_files/nlc.runconfig" $fold_running/setup_files/setup.parm
sed -i "/^surface_model_output_interval/c\surface_model_output_interval=1mo" $fold_running/setup_files/setup.parm


# Step 1: Create database
echo "[INFO] `date` | Step 1: Create database "
python $path_PyWrfHydroCalib/initDB.py --optDbPath $file_db
# Step 2: Input domain meta
echo "[INFO] `date` | Step 2: Input domain meta "
python $path_PyWrfHydroCalib/inputDomainMeta.py $fold_running/setup_files/domainMeta.csv --optDbPath $file_db # NOTE: update this file
# Step 3: Initialize batch job
echo "[INFO] `date` | Step 3: Initialize batch job "
nohup python $path_PyWrfHydroCalib/jobInit.py $fold_running/setup_files/setup.parm --optExpID 101 --optDbPath $file_db > log_jobInit.out 2>&1& # NOTE: update jobID globally

## Step 4: Run spinup
echo "[INFO] `date` | Step 4: Run spinup "
nohup python $path_PyWrfHydroCalib/spinOrchestrator.py 101 --optDbPath $file_db > log_spin.out 2>&1&

## Step 5: Run calibration
echo "[INFO] `date` | Step 5: Run calibration " 
nohup python $path_PyWrfHydroCalib/calibOrchestrator.py 101 --optDbPath $file_db > log_calib.out 2>&1&

## Step 6: Run validation
echo "[INFO] `date` | Step 6: Run validation "
nohup python $path_PyWrfHydroCalib/runValidOrchestrator.py $path_PyWrfHydroCalib 101 --optDbPath $file_db > log_valid.out 2>&1&

