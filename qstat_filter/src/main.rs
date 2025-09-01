use serde::Serialize;
use serde_json::{Map, Value};
use simd_json::serde::from_slice;
use std::env;
use std::fs::File;
use std::io::Read;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let args: Vec<String> = env::args().collect();
    if args.len() != 3 {
        eprintln!("Usage: {} <json_path> <user>", args[0]);
        std::process::exit(1);
    }
    let path = &args[1];
    let user = &args[2];

    let mut file = File::open(path)?;
    let mut buf = Vec::new();
    file.read_to_end(&mut buf)?;
    // simd_json requires a mutable slice
    let data: Value = from_slice(&mut buf)?;

    if let Some(jobs) = data.get("Jobs").and_then(|j| j.as_object()) {
        #[derive(Serialize)]
        struct JobWithId<'a> {
            #[serde(flatten)]
            job: &'a Map<String, Value>,
            id: &'a str,
        }

        for (id, job) in jobs {
            if job.get("euser").and_then(Value::as_str) == Some(user.as_str()) {
                if let Value::Object(map) = job {
                    let out = JobWithId { job: map, id };
                    println!("{}", serde_json::to_string(&out)?);
                }
            }
        }
    }

    Ok(())
}

