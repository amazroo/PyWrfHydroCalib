####################################################
####  NASA Land Coupler runtime configuration  #####
####################################################

# optionally turn off a component (options are "yes" and "no")
lnd: yes
hyd: yes
med: yes

# PET lists - if not set, use all PETs
pets_lnd: 0 39
pets_hyd: 0 39
pets_med: 0 39

# global clock
time_step:  3600
start_time: 2016 10 01 0 0 0
stop_time:  2022 10 01 0 0 0

# run sequence
runSeq::
    @3600
        LND
        LND -> MED
        MED prepHYD
        MED -> HYD
        HYD
        HYD -> MED
        MED prepLND
        MED -> LND
    @
::

# component attributes
driverAttributes::
  Verbosity = high
  Profiling = 0
::

connectorAttributes::
  Verbosity = 0
  Profiling = 0
::

medAttributes::
  Verbosity = 1
  Profiling = 0
  DataInitialization = INIT_MODELS
  RemapLND = FLD_REMAP_BILINR
  RemapHYD = FLD_REMAP_BILINR
  MaskFrLND = FLD_MASK_NNE
  MaskToLND = FLD_MASK_NNE
  MaskFrHYD = FLD_MASK_NNE
  MaskToHYD = FLD_MASK_NNE
::

lndAttributes::
  Verbosity = 1
  Diagnostic = 0
  Profiling = 0
  realize_all_export = false
  config_file = lis.config
  nest_to_nest = false
  import_dependency = true
  output_directory = LND_OUTPUT
::

hydAttributes::
  Verbosity = 1
  Diagnostic = 0
  Profiling = 0
  realize_all_export = false
  config_file = hydro.namelist
  das_config_file = namelist.hrldas
  time_step = 0
  forcings_directory = NONE
  domain_id = 1
  nest_to_nest = false
  import_dependency = false
  write_restart = true
  read_restart = true
  input_directory = HYD_INPUT
  output_directory = HYD_OUTPUT
::

