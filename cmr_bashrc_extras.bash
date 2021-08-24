# Add HPC scripts e.g. mqsub to the path
export PATH="/work2/microbiome/sw/hpc_scripts/bin:$PATH"

#function for command prompt and email notification of job completion
function notify { command "$@" && success || fail; }

#setup temporary file folder # No need for this since /tmp is /data1 in mounts
# export TMPDIR=/data1/tmp-$USER
# mkdir -p $TMPDIR

#check for nextflow config
if [[ ! -e ~/.nextflow/config ]]; then
    NEXTFLOW_CONFIG=/work2/microbiome/sw/nextflow_config/config
fi

# Otherwise qaddtime is only available on lyra
alias qaddtime=/pkg/hpc/scripts/qaddtime

# Save all the history, see https://debian-administration.org/article/543/Bash_eternal_history
export HISTTIMEFORMAT="%F %T "
PROMPT_COMMAND="${PROMPT_COMMAND:+$PROMPT_COMMAND ; }"'echo $$ $USER \
               "$(history 1)" >> ~/.bash_eternal_history'
