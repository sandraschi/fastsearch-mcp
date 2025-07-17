#[cfg(windows)]
fn main() {
    embed_resource::compile("resources.rc");
}

#[cfg(not(windows))]
fn main() {
    // Nothing to do on non-Windows platforms
}
