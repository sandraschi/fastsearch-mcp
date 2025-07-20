#[cfg(windows)]
fn main() {
    // The second argument is a list of preprocessor macros, which we don't need here
    embed_resource::compile("resources.rc", embed_resource::NONE);
}

#[cfg(not(windows))]
fn main() {
    // Nothing to do on non-Windows platforms
}
