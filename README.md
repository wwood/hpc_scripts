# hpc_scripts
Scripts for easier use of the QUT HPC system. These are available once you run the following (soon this will be done automatically)
```
source /work/microbiome/sw/hpc_scripts/cmr_bashrc_extras.bash
```

# mqsub
mqsub aims to be an ergonomic method for submitting jobs to the PBS queue. It dynamically generates a qsub script, submits it, 
waits for the result and then emails you to say it is done.

A straightforward example:

```
$ mqsub -- echo hello world
12/23/2020 10:38:30 AM INFO: qsub stdout was: 8690551.pbs
12/23/2020 10:38:30 AM INFO: First status of job is: Q: Job is queued
12/23/2020 10:41:31 AM INFO: Now status of job is: F: Job is finished
12/23/2020 10:41:31 AM INFO: Job has finished
12/23/2020 10:41:31 AM INFO: resources_used.walltime: 00:00:01
12/23/2020 10:41:31 AM INFO: resources_used.cpupercent: 0
12/23/2020 10:41:31 AM INFO: resources_used.cput: 00:00:00
12/23/2020 10:41:31 AM INFO: resources_used.vmem: 67728kb
hello world
```

From there the behaviour can be modified in several ways, using the optional arguments. For instance to request 1 hour instead of 1 week:

```
$ mqsub --hours 1 -- echo hi
```

There are several other options, which can be viewed with `mqsub -h`
```
optional arguments:
  -h, --help            show this help message and exit
  --debug               output debug information
  --quiet               only output errors
  -t CPUS, --cpus CPUS  Number of CPUs to queue job with [default: 1]
  -m MEM, --mem MEM, --ram MEM
                        GB of RAM to ask for [default: 4*num_cpus]
  --directive DIRECTIVE
                        Arbitrary PBS directory to add e.g. '-l ngpus=1' to
                        ask for a GPU [default: Not used]
  -q QUEUE, --queue QUEUE
                        Name of queue to send to
                        [default: 'microbiome']
  --hours HOURS         Hours to run for [default: 1 week]
  --weeks WEEKS         Weeks to run for [default 1]
  --name NAME           Name of the job [default: first word of command]
  --dry-run             Print script to STDOUT and do not lodge it with qsub
  --bg                  Submit the job, then quit [default: wait until job is
                        finished before exiting]
  --no-email            Do not send any emails, either on job finishing or
                        aborting
  --script SCRIPT       Script to run, or "-" for STDIN
  --script-shell SCRIPT_SHELL
                        Run script specified in --script with this shell
                        [default: /bin/bash]
  --script-tmpdir SCRIPT_TMPDIR
                        When '--script -' is specified, write the script to
                        this location as a temporary file
  --poll-interval POLL_INTERVAL
                        Poll the PBS server once every this many seconds
                        [default: 30]
  --no-executable-check
                        Usually mqsub checks the executable is currently
                        available. Don't do this [default: do check]
```


# mqstat
To view useful usage statistics (i.e. the percentage of microbiome queue CPUs which are currently in-use/available) simply type `mqstat`. Example output:
```
Microbiome group jobs running: 4 / 4 (100.00%)
Microbiome group CPUs utilized: 120 / 512 (23.44%)
Microbiome group CPUs queued: 0
sternesp jobs running: 0 / 0 (0.0%)
sternesp CPUs running: 0 / 512 (0.0%)
sternesp CPUs queued: 0
Non-microbiome group jobs / CPU: 0 / 0 (0.0%)
```

You can also view a detailed breakdown queued and running jobs on a per-user basis by typing `mqstat --list`. Example output:
```
List of jobs in queue:
----------------------
PBS ID      | username  | name        | state | CPUs | RAM   | walltime (hrs) | start time               | elapsed time         | % walltime | microbiome queue | node       
----------- | --------- | ----------- | ----- | ---- | ----- | -------------- | ------------------------ | -------------------- | ---------- | ---------------- | -----------
9524869.pbs | n10853499 | Rhys Newell | R     | 48   | 480gb | 84             | Tue Jun  8 03:02:37 2021 | 2 day, 6 hr, 19 min  | 64         | yes              | cl5n013/0*0
9524870.pbs | n10853499 | Rhys Newell | R     | 48   | 480gb | 84             | Tue Jun  8 20:57:54 2021 | 1 day, 12 hr, 24 min | 43         | yes              | cl5n012/0*0

Time left until maintenance (hr:min:sec): 1999:37:25
```

Furthermore, you can also view the amount of available resources per-node basis by typing `mqstat --avail`. This can help you plan on how many resources to request. In the example below, if you were to request 49+ CPUs your job will be held in the queue until that amount of resource is available on a single node.
```
Available resources:
--------------------
node    | CPU        | RAM   
------- | ---------- | ------
cl5n010 | 0 threads  | 560 GB
cl5n011 | 16 threads | 550 GB
cl5n012 | 48 threads | 480 GB
cl5n013 | 1 threads  | 356 GB
```


# mqwait
If you are running a batch of jobs, you may wish to be notified once the entire batch has finished processing, as opposed to per-job notifications generated by mqsub. There are three ways to run mqwait:

1) Typing `mqwait` will send you an email once all your current running and queued jobs finish.

2) You can specify a newline delimited list of PBS jobs you wish to be notified by. ie. `mqwait -i pbs_job_list`
In this example pbs_job_list would contain:
```
123456.pbs
123457.pbs
123458.pbs
```

3) You can also pipe multiple mqsubs (using parallel or a script containing mqsub commands) in a single command to be notified when that specific batch of jobs finish. Note: currently the STDERR from mqsub is piped into mqwait using |&. This may change in future.
`parallel mqsub --no-email --bg ... |& mqwait -m` or `mqsub_jobs.sh |& mqwait -m`

Specifying the `-l` parameter will verbosely display the number of remaining jobs on your terminal and it controlled by the polling rate `-p` (default 60 seconds)

# mcreate
This is a basic script which searches for the latest version of conda package and creates a new, versioned, environment using conda (with the `-c` parameter) or mamba (default; requires mamba to be installed first).

Simply: `mcreate <package_name>`

You can also check for the latest version of a package without installing:
`mcreate <package_name> -v`
