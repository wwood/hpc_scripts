# Add HPC scripts e.g. mqsub to the path
export PATH="/work2/microbiome/sw/hpc_scripts/bin:$PATH"

#function for command prompt and email notification of job completion
function notify { command "$@" && success || fail; }

#setup temporary file folder # No need for this since /tmp is /data1 in mounts
# export TMPDIR=/data1/tmp-$USER
# mkdir -p $TMPDIR

#check for nextflow config and source if none found
if [[ ! -e ~/.nextflow/config ]]; then
    source /work2/microbiome/sw/nextflow_config/config
fi

#re-sources cron-scheduled jobs
#crontab -r
#crontab /work2/microbiome/sw/hpc_scripts/bin/cron

