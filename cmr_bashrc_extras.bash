. /etc/os-release

case $ID in
  sles) echo "Suse Linux" 1>&2
    # echo Running lyra cmr .bashrc extras 1>&2
    . /work/microbiome/sw/hpc_scripts/cmr_bashrc_extras_lyra.bash
    ;;
  rhel)
    # echo "RedHat Linux" 1>&2
    echo Running aqua cmr .bashrc extras 1>&2
    . /work/microbiome/sw/hpc_scripts/cmr_bashrc_extras_aqua.bash
    ;;
esac