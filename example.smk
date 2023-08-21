rule echo:
    output:
        "echo.done"
    threads: 2
    resources:
        mem_mb=2000,
        runtime = "1h",
    shell:
        "echo hello world > {output}"
