# Add HPC scripts e.g. mqsub to the path
export PATH="/mnt/hpccs01/work/microbiome/sw/hpc_scripts/bin:$PATH"

#function for command prompt and email notification of job completion
function notify { command "$@" && success || fail; }

#setup temporary file folder # No need for this since /tmp is /data1 in mounts
# export TMPDIR=/data1/tmp-$USER
# mkdir -p $TMPDIR

#check for nextflow config
if [[ ! -e ~/.nextflow/config ]]; then
    NEXTFLOW_CONFIG=/mnt/hpccs01/work/microbiome/sw/nextflow_config/config
fi

# Otherwise qaddtime is only available on lyra # currently disabled due to abuse
#alias qaddtime=/pkg/hpc/scripts/qaddtime

# Save all the history, see https://debian-administration.org/article/543/Bash_eternal_history
export HISTTIMEFORMAT="%F %T "
PROMPT_COMMAND="${PROMPT_COMMAND:+$PROMPT_COMMAND ; }"'echo $$ $USER \
               "$(history 1)" >> ~/.bash_eternal_history'

#Path to kingfisher # symlinked /lustre/work-lustre/microbiome/sw/kingfisher-download/bin/kingfisher in $CONDA_PREFIX/envs/kingfisher/bin instead
#export PATH=/lustre/work-lustre/microbiome/sw/kingfisher-download/bin:$PATH

#add RAM usage limits
if [ `hostname` = "cl5n006" ] || [ `hostname` = "cl5n007" ] || [ `hostname` = "cl5n008" ] || [ `hostname` = "cl5n009" ]
then
    case $- in *i*) echo "** Setting 750GB RAM ulimit **"; esac
    ulimit -v $((750 * 1024 * 1024))
elif [ `hostname` = "cl5n005" ]
then
    case $- in *i*) echo "** Setting 300GB RAM ulimit **"; esac
    ulimit -v $((350 * 1024 * 1024))
fi

#notify about disk usage
case $- in *i*) echo "** cl5n005 disk usage (%): `cat /work/microbiome/cl5n005_disk_usage` **"; esac
case $- in *i*) echo "** cl5n006 disk usage (%): `cat /work/microbiome/cl5n006_disk_usage` **"; esac
case $- in *i*) echo "** cl5n007 disk usage (%): `cat /work/microbiome/cl5n007_disk_usage` **"; esac
case $- in *i*) echo "** cl5n008 disk usage (%): `cat /work/microbiome/cl5n008_disk_usage` **"; esac
case $- in *i*) echo "** cl5n009 disk usage (%): `cat /work/microbiome/cl5n009_disk_usage` **"; esac
case $- in *i*) echo "** cl5n010 disk usage (%): `cat /work/microbiome/cl5n010_disk_usage` **"; esac
case $- in *i*) echo "** cl5n011 disk usage (%): `cat /work/microbiome/cl5n011_disk_usage` **"; esac
case $- in *i*) echo "** cl5n012 disk usage (%): `cat /work/microbiome/cl5n012_disk_usage` **"; esac
case $- in *i*) echo "** cl5n013 disk usage (%): `cat /work/microbiome/cl5n013_disk_usage` **"; esac


# Setup snakemake config directories so it interfaces well with the PBS system
mkdir -p ~/.config/snakemake
cd ~/.config/snakemake && ln -sf /work/microbiome/sw/hpc_scripts/snakemake_configs/* . && cd ~
