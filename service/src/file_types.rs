//! File type detection and filtering utilities

use std::collections::HashSet;
use lazy_static::lazy_static;
use log::debug;

/// Supported document type presets
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum DocumentType {
    Text,
    Code,
    Image,
    Spreadsheet,
    Presentation,
    Archive,
    Audio,
    Video,
    Pdf,
}

lazy_static! {
    static ref EXTENSION_MAP: std::collections::HashMap<DocumentType, HashSet<&'static str>> = {
        let mut m = std::collections::HashMap::new();
        
        // Text documents
        m.insert(DocumentType::Text, 
            vec!["txt", "md", "markdown", "rtf", "odt", "doc", "docx", "pdf", "tex", "log"]
            .into_iter().collect());
            
        // Source code files
        m.insert(DocumentType::Code,
            vec![
                // Common languages
                "rs", "py", "js", "ts", "jsx", "tsx", "java", "c", "cpp", "h", "hpp", "cs", 
                "go", "rb", "php", "swift", "kt", "scala", "m", "mm", "sh", "bash", "ps1", "bat",
                // Web
                "html", "css", "scss", "sass", "less", "json", "yaml", "toml", "xml", "sql",
                // Config
                "ini", "cfg", "conf", "env", "gitignore", "dockerfile", "makefile",
                // Other
                "lua", "perl", "r", "sql", "vue", "svelte"
            ].into_iter().collect());
            
        // Image files
        m.insert(DocumentType::Image,
            vec!["jpg", "jpeg", "png", "gif", "bmp", "webp", "tiff", "tif", "svg", "ico", "heic"]
            .into_iter().collect());
            
        // Spreadsheets
        m.insert(DocumentType::Spreadsheet,
            vec!["xls", "xlsx", "xlsm", "ods", "csv", "tsv"]
            .into_iter().collect());
            
        // Presentations
        m.insert(DocumentType::Presentation,
            vec!["ppt", "pptx", "odp", "key"]
            .into_iter().collect());
            
        // Archives
        m.insert(DocumentType::Archive,
            vec!["zip", "rar", "7z", "tar", "gz", "bz2", "xz", "zst", "lzma", "lz4", "lzh", "cab"]
            .into_iter().collect());
            
        // Audio files
        m.insert(DocumentType::Audio,
            vec!["mp3", "wav", "ogg", "flac", "aac", "m4a", "wma", "aiff", "aif", "midi", "mid"]
            .into_iter().collect());
            
        // Video files
        m.insert(DocumentType::Video,
            vec!["mp4", "avi", "mkv", "mov", "wmv", "flv", "webm", "m4v", "mpeg", "mpg", "3gp"]
            .into_iter().collect());
            
        // PDFs
        m.insert(DocumentType::Pdf, 
            vec!["pdf"]
            .into_iter().collect());
            
        m
    };
}

/// Check if a file extension matches any of the document types
pub fn extension_matches_doc_types(extension: &str, doc_types: &[DocumentType]) -> bool {
    if doc_types.is_empty() {
        return true; // No filter means match all
    }
    
    let ext_lower = extension.to_lowercase();
    
    for doc_type in doc_types {
        if let Some(extensions) = EXTENSION_MAP.get(doc_type) {
            if extensions.contains(ext_lower.as_str()) {
                return true;
            }
        }
    }
    
    false
}

/// Parse document type from string
pub fn parse_document_type(s: &str) -> Option<DocumentType> {
    match s.to_lowercase().as_str() {
        "text" => Some(DocumentType::Text),
        "code" => Some(DocumentType::Code),
        "image" => Some(DocumentType::Image),
        "spreadsheet" => Some(DocumentType::Spreadsheet),
        "presentation" => Some(DocumentType::Presentation),
        "archive" => Some(DocumentType::Archive),
        "audio" => Some(DocumentType::Audio),
        "video" => Some(DocumentType::Video),
        "pdf" => Some(DocumentType::Pdf),
        _ => None,
    }
}

/// Get all extensions for a document type
pub fn get_extensions(doc_type: DocumentType) -> Vec<&'static str> {
    EXTENSION_MAP
        .get(&doc_type)
        .map(|exts| exts.iter().map(|&s| s).collect())
        .unwrap_or_default()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_extension_matching() {
        assert!(extension_matches_doc_types("txt", &[DocumentType::Text]));
        assert!(extension_matches_doc_types("rs", &[DocumentType::Code]));
        assert!(!extension_matches_doc_types("txt", &[DocumentType::Code]));
        assert!(extension_matches_doc_types("TXT", &[DocumentType::Text])); // case insensitive
    }

    #[test]
    fn test_parse_document_type() {
        assert_eq!(parse_document_type("text"), Some(DocumentType::Text));
        assert_eq!(parse_document_type("TEXT"), Some(DocumentType::Text));
        assert_eq!(parse_document_type("invalid"), None);
    }
}
