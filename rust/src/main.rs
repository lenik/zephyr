// SPDX-License-Identifier: AGPL-3.0-or-later

use std::ffi::OsStr;
use std::fs::File;
use std::io;
use std::path::Path;
use std::process;

use clap::Arg;
use clap::ArgAction;
use clap::Command;
use gettextrs::{bind_textdomain_codeset, bindtextdomain, gettext, setlocale, textdomain, LocaleCategory};

use zephyr::{copy_stream, Puff1Error};

const TEXT_DOMAIN: &str = "zephyr";
const PROJECT_AUTHOR: &str = "Lenik";
const PROJECT_EMAIL: &str = "zephyr@bodz.net";
const PROJECT_YEAR: i32 = 2026;
const PUFF1_VERSION: &str = env!("CARGO_PKG_VERSION");

/// Resolve GNU gettext "localedir" (contains `<lang>/LC_MESSAGES/<domain>.mo`).
fn pick_localedir() -> String {
    if let Ok(s) = std::env::var("ZEPHYR_LOCALEDIR") {
        return s;
    }
    for candidate in ["/build/po", "build/po"] {
        if Path::new(candidate).is_dir() {
            return candidate.to_string();
        }
    }
    if let Ok(manifest) = std::env::var("CARGO_MANIFEST_DIR") {
        let p = format!("{manifest}/../build/po");
        if Path::new(&p).is_dir() {
            return p;
        }
    }
    "/usr/local/share/locale".to_string()
}

fn init_gettext() {
    let _ = setlocale(LocaleCategory::LcAll, "");
    let localedir = pick_localedir();
    if bindtextdomain(TEXT_DOMAIN, &localedir).is_err()
        || textdomain(TEXT_DOMAIN).is_err()
        || bind_textdomain_codeset(TEXT_DOMAIN, "UTF-8").is_err()
    {
        // Translations are optional: continue with msgids.
    }
}

fn c_format_replace(template: &str, pairs: &[(&str, &str)]) -> String {
    let mut s = template.to_string();
    for (a, b) in pairs {
        s = s.replace(a, b);
    }
    s
}

fn usage() {
    let msg = gettext(
        "Usage: puff1 [OPTION]... [FILE]...\n\
Concatenate FILE(s) to standard output. With no FILE, or when FILE is -,\n\
read standard input.\n",
    );
    let bugs = c_format_replace(
        &gettext("Report bugs to: <%s>\n"),
        &[("%s", PROJECT_EMAIL)],
    );
    eprintln!();
    eprintln!("{msg}");
    eprintln!();
    eprintln!("  -v, --verbose      {}", gettext("repeat for more verbose loggings\n").trim_end());
    eprintln!("  -q, --quiet        {}", gettext("show less logging messages\n").trim_end());
    eprintln!("  -h, --help         {}", gettext("display this help and exit\n").trim_end());
    eprintln!("      --version      {}", gettext("output version information and exit\n").trim_end());
    eprintln!();
    eprint!("{bugs}");
}

fn print_version() {
    println!("puff1 {PUFF1_VERSION}");
    let cpy = c_format_replace(
        &gettext("Copyright (C) %d %s\n"),
        &[("%d", &format!("{PROJECT_YEAR}")), ("%s", PROJECT_AUTHOR)],
    );
    print!("{cpy}");
    print!("{}", gettext("License AGPL-3.0-or-later: <https://www.gnu.org/licenses/agpl-3.0.html>\n"));
    print!("{}", gettext("This is free software: you are free to change and redistribute it.\n"));
    print!("{}", gettext("This project opposes AI exploitation and AI hegemony.\n"));
    print!("{}", gettext(
        "This project rejects mindless MIT-style licensing and politically naive BSD-style licensing.\n",
    ));
    print!("{}", gettext("There is NO WARRANTY, to the extent permitted by law.\n"));
}

fn init_env_logger(verbose: u8, quiet: bool) {
    if quiet {
        let _ = env_logger::Builder::new()
            .filter_level(log::LevelFilter::Error)
            .format_timestamp(None)
            .try_init();
    } else {
        let level = match verbose {
            0 => log::LevelFilter::Info,
            1 => log::LevelFilter::Debug,
            _ => log::LevelFilter::Trace,
        };
        let _ = env_logger::Builder::new()
            .filter_level(level)
            .format_timestamp(None)
            .try_init();
    }
}

fn self_exe() -> String {
    std::env::args()
        .next()
        .as_ref()
        .map(|s| {
            use std::path::Path;
            let p = Path::new(s);
            p.file_name()
                .map(OsStr::to_string_lossy)
                .map(|c| c.into_owned())
                .unwrap_or_else(|| s.clone())
        })
        .unwrap_or_else(|| "puff1".to_string())
}

fn copy_stdin(prog: &str) -> Result<(), Puff1Error> {
    let mut stdin = io::stdin();
    let mut out = io::stdout();
    if let Err(e) = copy_stream(&mut stdin, &mut out) {
        eprintln!("{prog}: stdin: {e}");
        return Err(e);
    }
    Ok(())
}

/// Like the C `copy_file`: `fopen` errors print `"%s: %s" prog path`; `copy_stream` uses `"%s: write
/// error"`.
fn copy_path_to_stdout(prog: &str, path: &str) -> Result<(), Puff1Error> {
    let p = Path::new(path);
    let mut f = match File::open(p) {
        Ok(f) => f,
        Err(e) => {
            eprintln!("{prog}: {path}: {e}");
            return Err(e.into());
        }
    };
    let mut out = io::stdout().lock();
    if let Err(e) = copy_stream(&mut f, &mut out) {
        eprint!("{}", c_format_replace(&gettext("%s: write error\n"), &[("%s", prog)]));
        return Err(e);
    }
    Ok(())
}

fn run() -> i32 {
    init_gettext();
    println!("TEXT_DOMAIN={TEXT_DOMAIN}.");
    print!("{}", gettext("hello, world!\n"));

    let cmd = Command::new("puff1")
        .disable_version_flag(true)
        .disable_help_flag(true)
        .arg(
            Arg::new("verbose")
                .short('v')
                .long("verbose")
                .action(ArgAction::Count)
                .help(
                    gettext("repeat for more verbose loggings\n")
                        .trim_end_matches('\n')
                        .to_string(),
                ),
        )
        .arg(
            Arg::new("quiet")
                .short('q')
                .long("quiet")
                .action(ArgAction::SetTrue)
                .help(
                    gettext("show less logging messages\n")
                        .trim_end_matches('\n')
                        .to_string(),
                )
                .overrides_with("verbose"),
        )
        .arg(
            Arg::new("help")
                .short('h')
                .long("help")
                .action(ArgAction::SetTrue)
                .help(
                    gettext("display this help and exit\n")
                        .trim_end_matches('\n')
                        .to_string(),
                ),
        )
        .arg(
            Arg::new("version")
                .long("version")
                .action(ArgAction::SetTrue)
                .help(
                    gettext("output version information and exit\n")
                        .trim_end_matches('\n')
                        .to_string(),
                ),
        )
        .arg(
            Arg::new("files")
                .value_name("FILE")
                .num_args(0..)
                .action(ArgAction::Append)
                .allow_hyphen_values(true),
        );
    let m = match cmd.try_get_matches() {
        Ok(m) => m,
        Err(e) => {
            e.print().expect("write stderr");
            return 2;
        }
    };
    if m.get_flag("version") {
        print_version();
        return 0;
    }
    if m.get_flag("help") {
        usage();
        return 0;
    }
    let verbose = m.get_count("verbose");
    let quiet = m.get_flag("quiet");
    init_env_logger(verbose, quiet);

    let exe = self_exe();
    if verbose > 0 {
        if quiet {
            log::warn!("{exe}: -q overrides -v: quiet logging is active");
        } else {
            log::info!("{exe}: verbose mode enabled");
        }
    }

    let file_args: Vec<String> = m
        .get_many::<String>("files")
        .map(|it| it.cloned().collect())
        .unwrap_or_default();
    if file_args.is_empty() {
        log::info!("{exe}: reading from standard input");
        if copy_stdin(&exe).is_err() {
            return 1;
        }
        log::info!("{exe}: done");
        return 0;
    }
    for path in &file_args {
        if path == "-" {
            log::info!("{exe}: copying from standard input");
            if copy_stdin(&exe).is_err() {
                return 1;
            }
        } else if copy_path_to_stdout(&exe, path).is_err() {
            return 1;
        } else {
            log::info!("{exe}: copied {path}");
        }
    }
    log::info!("{exe}: done");
    0
}

fn main() {
    let code = run();
    process::exit(code);
}
