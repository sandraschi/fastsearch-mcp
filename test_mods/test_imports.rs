// Test file to verify module imports

// Import from the service crate
use fastsearch_service::search_engine::SearchEngine;

#[test]
fn test_import() {
    // This test will pass if the import is successful
    let _ = SearchEngine::new().unwrap();
    assert!(true);
}
