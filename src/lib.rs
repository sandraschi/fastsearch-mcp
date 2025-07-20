// Temporary lib.rs to satisfy Cargo requirements
// This is a workaround for building the workspace

/// Dummy function to satisfy the library requirement
#[allow(dead_code)]
pub fn dummy() -> &'static str {
    "This is a dummy library for building the FastSearch MCP workspace"
}

#[cfg(test)]
mod tests {
    #[test]
    fn it_works() {
        assert_eq!(2 + 2, 4);
    }
}
